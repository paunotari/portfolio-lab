"""Random-regime placebo — does the macro-state signal add anything beyond the menu? (M32)

The regime layer is this project's signature feature and its most attackable one. Every
regime-conditioned contestant (the maximin family, whose objective maximizes the worst
per-quadrant mean) could in principle owe its record not to the LABELS but to the menu and the
caps: "maximize the worst of four arbitrary partitions of history" is already a robustness
device, and a referee will ask whether four RANDOM partitions would have done the same.

This module answers it the only way that settles it — a permutation test. The identical
walk-forward is re-run B times with the state labels SCRAMBLED, and the real record is placed
in the resulting null distribution. Empirical p = share of placebo replicates whose net OOS
Sharpe reaches the real one.

Two shuffle modes, because they destroy different things:

- ``circular`` (primary): rotate the whole label frame by a random offset. Marginal state
  frequencies, run lengths and the transition matrix are preserved EXACTLY — only the alignment
  between labels and returns is destroyed. This is the referee-grade null: it isolates "do these
  months' labels carry return information?" from "does a persistent 4-state partition help?"
- ``iid``: permute the rows. Destroys persistence as well, so the gap between the two modes
  says how much of any real edge is alignment vs. mere regime-shaped structure.

The whole row travels together (hard label + the four soft probabilities + scores), so a
scrambled month stays internally consistent — the outlook and transition machinery see
well-formed input, just mislabelled months.

Honest caveats, stated not hidden:
- The rotation is applied ONCE to the full history, so a placebo training window can receive
  labels drawn from months after its own end. That can only help the placebo (the assignment is
  random), which makes a "real beats placebo" verdict CONSERVATIVE.
- The shipped specification is kept in both arms, including the long-history anchor
  (`OPTIMIZER_ANCHOR_LONG`). Anchoring keys per-quadrant cells by quadrant NAME, so under
  scrambled labels the 66-year prior is still real — but attached to random months, which is
  precisely what makes it unexploitable. Turning it off would test a portfolio we do not ship.
- 1/N is carried through every replicate as an invariance check: it consumes no labels, so its
  Sharpe MUST be identical in every arm. If it ever moves, the harness is leaking.

Run:  python -m portfolio_lab.portfolio.placebo              # both modes, config B replicates
      python -m portfolio_lab.portfolio.placebo --b 10 --mode circular
"""
from __future__ import annotations
import argparse
import time

import numpy as np
import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.analytics.engine import _perf_stats
from portfolio_lab.portfolio import optimizer as opt

AW_NAME = "Maximin (all-weather div)"
REGIME_CONTESTANTS = ["Maximin (worst quadrant)", "Maximin (diversified)", AW_NAME]
CONTROL = "1/N"


def scramble_states(states: pd.DataFrame, mode: str, rng: np.random.Generator) -> pd.DataFrame:
    """Return a label frame with the same index and the same rows, re-assigned to months.

    circular: roll the values by a random offset (preserves marginals, run lengths, transitions).
    iid:      permute the rows (destroys persistence too).
    """
    T = len(states)
    if mode == "circular":
        k = int(rng.integers(1, T))                     # never 0 — that is the real labelling
        order = np.roll(np.arange(T), k)
    elif mode == "iid":
        order = rng.permutation(T)
    else:
        raise ValueError(f"unknown shuffle mode {mode!r} (use 'circular' or 'iid')")
    out = states.iloc[order].copy()
    out.index = states.index
    return out


def _regime_walk_forward(states: pd.DataFrame = None, warmup: int = None, refit: int = None,
                         n_starts: int = None, seed: int = None) -> dict:
    """The main walk-forward stripped to the label-consuming contestants (+ 1/N as control).

    Same expanding window, same estimation-on-train-only discipline, same cost charge as
    `validation.walk_forward` — just fewer contestants, because a permutation test needs the
    run repeated dozens of times. `states=None` runs the REAL labels.
    Returns {contestant: net OOS Sharpe}.
    """
    warmup = warmup or C.OPTIMIZER_WF_WARMUP_MONTHS
    refit = refit or C.OPTIMIZER_WF_REFIT_MONTHS
    n_starts = n_starts or C.OPTIMIZER_WF_N_STARTS
    seed = C.OPTIMIZER_SEED if seed is None else seed

    rets = opt.load_returns()
    T = len(rets)
    div_kw = dict(cap=C.OPTIMIZER_DIVERSIFIED_SLEEVE_CAP_PCT / 100.0,
                  geo_cap=C.OPTIMIZER_GEO_CAP_PCT / 100.0,
                  factor_cap=C.OPTIMIZER_FACTOR_CAP_PCT / 100.0)
    rets_aw = None
    if C.ASSET_CLASS_MONTHLY.exists():
        aw = opt.load_returns(include_asset_classes=True)
        if aw.shape[1] > rets.shape[1]:
            rets_aw = aw

    gross_chunks: dict[str, list] = {}
    turn_chunks: dict[str, list] = {}
    prev_w: dict[str, np.ndarray] = {}
    n_refits = 0
    for t in range(warmup, T, refit):
        inp = opt.build_inputs(rets.iloc[:t], states=states)
        n_refits += 1
        oos = rets.iloc[t:t + refit].values
        entries = [(CONTROL, inp["anchors"][CONTROL], oos)]
        if inp["mu_q"] is not None and len(inp["mu_q"]) >= 2:
            entries.append(("Maximin (worst quadrant)", opt.optimize(
                maximin=True, inputs=inp, n_starts=n_starts, seed=seed)["w"], oos))
            entries.append(("Maximin (diversified)", opt.optimize(
                maximin=True, inputs=inp, n_starts=n_starts, seed=seed, **div_kw)["w"], oos))
        if rets_aw is not None:
            train_aw = rets_aw.loc[:rets.index[t - 1]]
            oos_aw = rets_aw.loc[rets.index[t]:rets.index[min(t + refit, T) - 1]]
            if len(train_aw) >= warmup - 12 and len(oos_aw):
                try:
                    inp_aw = opt.build_inputs(train_aw, states=states)
                    if inp_aw["mu_q"] is not None:
                        entries.append((AW_NAME, opt.optimize(
                            maximin=True, inputs=inp_aw, n_starts=n_starts, seed=seed,
                            **div_kw)["w"], oos_aw.values))
                except Exception as e:
                    print(f"[placebo] WARN all-weather refit skipped ({e})")
        for name, w, oos_m in entries:
            chunk = oos_m @ w
            tmonth = np.zeros(len(chunk))
            if name in prev_w:
                tmonth[0] = float(np.abs(w - prev_w[name]).sum() / 2)
            prev_w[name] = w
            gross_chunks.setdefault(name, []).append(chunk)
            turn_chunks.setdefault(name, []).append(tmonth)

    oos_index = rets.index[warmup:]
    cost = C.OPTIMIZER_TC_BPS / 10_000.0
    out = {}
    for name, chunks in gross_chunks.items():
        g = np.concatenate(chunks)
        net = pd.Series(g - cost * np.concatenate(turn_chunks[name]),
                        index=oos_index[:len(g)])
        lvl = pd.concat([pd.Series([100.0], index=[net.index[0] - pd.offsets.MonthEnd(1)]),
                         100.0 * (1 + net).cumprod()])
        out[name] = _perf_stats(lvl)["sharpe_rf0"]
    out["_n_refits"] = n_refits
    return out


def run(b: int = None, modes: tuple = ("circular", "iid"), seed: int = 12345) -> pd.DataFrame:
    """Real arm + b scrambled replicates per mode -> optimizer_placebo.csv + REPORT_placebo.md."""
    C.ensure_dirs()
    b = C.OPTIMIZER_PLACEBO_B if b is None else b
    states_real = opt._load_states(opt.load_returns().index)
    if states_real is None:
        print("[placebo] macro-state labels absent — nothing to scramble; skipped")
        return pd.DataFrame()

    t0 = time.time()
    real = _regime_walk_forward()
    print(f"[placebo] real arm ({real.pop('_n_refits')} refits, {time.time() - t0:.0f}s): "
          + "  ".join(f"{k} {v:.3f}" for k, v in real.items()))

    rows = [dict(arm="real", mode="—", replicate=0, **real)]
    rng = np.random.default_rng(seed)
    for mode in modes:
        for i in range(b):
            res = _regime_walk_forward(states=scramble_states(states_real, mode, rng))
            res.pop("_n_refits", None)
            rows.append(dict(arm="placebo", mode=mode, replicate=i + 1, **res))
            print(f"[placebo] {mode} {i + 1}/{b}  "
                  + "  ".join(f"{k} {v:.3f}" for k, v in res.items()))
    df = pd.DataFrame(rows)
    df.to_csv(C.OPTIMIZER_PLACEBO, index=False)
    _write_report(df, b, modes)
    print(f"[placebo] wrote {C.OPTIMIZER_PLACEBO} and {C.OPTIMIZER_PLACEBO_REPORT} "
          f"({time.time() - t0:.0f}s total)")
    return df


def verdicts(df: pd.DataFrame) -> pd.DataFrame:
    """Per (contestant, mode): the real Sharpe against the scrambled-label null."""
    real = df[df.arm == "real"].iloc[0]
    rows = []
    for mode in sorted(df[df.arm == "placebo"]["mode"].unique()):
        sub = df[(df.arm == "placebo") & (df["mode"] == mode)]
        for name in REGIME_CONTESTANTS + [CONTROL]:
            if name not in df.columns or not np.isfinite(real[name]):
                continue
            null = sub[name].dropna().values
            if not len(null):
                continue
            # one-sided permutation p, with the real arm counted in the reference set
            p = (1 + int((null >= real[name]).sum())) / (1 + len(null))
            rows.append(dict(portfolio=name, mode=mode, real_sharpe=float(real[name]),
                             placebo_mean=float(null.mean()), placebo_sd=float(null.std(ddof=1)),
                             placebo_p05=float(np.percentile(null, 5)),
                             placebo_p95=float(np.percentile(null, 95)),
                             n_placebo=len(null), p_perm=p))
    return pd.DataFrame(rows)


def _write_report(df: pd.DataFrame, b: int, modes: tuple):
    v = verdicts(df)
    L = ["# Random-regime placebo — is the macro-state signal real? (M32)", "",
         "The maximin family's objective maximizes the WORST per-quadrant mean. That is already "
         "a robustness device, so a referee is entitled to ask whether four RANDOM partitions of "
         "history would have worked as well. This is the permutation test that settles it: the "
         "same walk-forward, re-run with the state labels scrambled, "
         f"{b} replicates per shuffle mode.", "",
         "- **circular** — the label frame rotated by a random offset: marginal frequencies, run "
         "lengths and the transition matrix are preserved EXACTLY, only the alignment with "
         "returns is destroyed. The primary null.",
         "- **iid** — rows permuted: persistence destroyed too. The gap between the modes says "
         "how much of any edge is alignment versus regime-shaped structure.", "",
         "`p_perm` is the one-sided share of scrambled replicates reaching the real Sharpe "
         "(the real arm is counted in the reference set, so the smallest attainable p is "
         f"1/{b + 1} = {1 / (b + 1):.3f}).", ""]
    L += ["| portfolio | mode | real Sharpe | placebo mean | placebo sd | placebo p5–p95 | p_perm |",
          "|---|---|---|---|---|---|---|"]
    for _, r in v.iterrows():
        L.append(f"| {r.portfolio} | {r['mode']} | {r.real_sharpe:.3f} | {r.placebo_mean:.3f} | "
                 f"{r.placebo_sd:.3f} | {r.placebo_p05:.3f} – {r.placebo_p95:.3f} | "
                 f"{r.p_perm:.3f} |")
    ctrl = v[v.portfolio == CONTROL]
    L += ["", "## Invariance check", ""]
    if len(ctrl):
        ok = bool(np.allclose(ctrl.placebo_sd.values, 0.0, atol=1e-12))
        L.append(f"- **{CONTROL}** consumes no labels, so its Sharpe must be identical in every "
                 f"arm — placebo sd = {ctrl.placebo_sd.max():.2e}. "
                 f"{'PASS.' if ok else '**FAIL — the harness is leaking.**'}")
    L += ["", "## Verdict", ""]
    for _, r in v[v.portfolio != CONTROL].iterrows():
        if r.p_perm <= 0.05:
            verdict = ("the real labels carry information the scrambled ones do not")
        elif r.real_sharpe >= r.placebo_p95:
            verdict = "in the null's top 5% but short of the permutation threshold"
        elif r.real_sharpe <= r.placebo_mean:
            verdict = ("**indistinguishable from random labels — this contestant's record is the "
                       "menu and the caps, not the regime signal**")
        else:
            verdict = "above the scrambled mean but inside the null distribution"
        L.append(f"- **{r.portfolio}** ({r['mode']}): real {r.real_sharpe:.3f} vs null "
                 f"{r.placebo_mean:.3f} ± {r.placebo_sd:.3f}, p = {r.p_perm:.3f} — {verdict}.")
    L += ["", "_Conservative by construction: the rotation is applied once to the full history, "
          "so a placebo training window can receive labels from months after its own end. That "
          "can only help the placebo._", ""]
    C.OPTIMIZER_PLACEBO_REPORT.write_text("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Random-regime placebo (permutation test)")
    ap.add_argument("--b", type=int, default=None, help="replicates per mode")
    ap.add_argument("--mode", choices=["circular", "iid"], default=None,
                    help="only this shuffle mode (default: both)")
    args = ap.parse_args()
    run(b=args.b, modes=(args.mode,) if args.mode else ("circular", "iid"))
