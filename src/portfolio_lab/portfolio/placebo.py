"""Random-regime placebo — does the macro-state signal add anything beyond the menu? (M32)

The regime layer is this project's signature feature and its most attackable one. Every
regime-conditioned contestant (the maximin family, whose objective maximizes the worst
per-quadrant mean) could in principle owe its record not to the LABELS but to the menu and the
caps: "maximize the worst of four arbitrary partitions of history" is already a robustness
device, and a referee will ask whether four RANDOM partitions would have done the same.

This module answers it the only way that settles it — a permutation test. The identical
walk-forward is re-run B times with the state labels SCRAMBLED, and the real record is placed
in the resulting null distribution. Empirical p = share of placebo replicates reaching the real
value.

**Two metrics, deliberately.** Scoring the placebo on Sharpe alone would test the maximin on a
target it never claimed — its objective is max_w min_q w'mu_q, the worst-quadrant FLOOR. So
every arm is also scored on its ``floor``: the realized worst mean monthly OOS return across
the four **REAL** quadrants, for whatever weights that arm chose. Real labels always — grading a
scrambled-label portfolio against its own scrambled quadrants would be circular, and would
guarantee the placebo looks good by construction.

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
- The test is about the LABELS' contribution to ALLOCATION. It says nothing about the
  classifier's descriptive value (which quadrant we are in, per-state performance) — that is a
  different claim, measured elsewhere.

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
    Returns {"<contestant> | sharpe": ..., "<contestant> | floor": ...}.
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
    real_labels = opt._load_states(rets.index)               # ALWAYS the real ones — see below
    out = {}
    for name, chunks in gross_chunks.items():
        g = np.concatenate(chunks)
        net = pd.Series(g - cost * np.concatenate(turn_chunks[name]),
                        index=oos_index[:len(g)])
        lvl = pd.concat([pd.Series([100.0], index=[net.index[0] - pd.offsets.MonthEnd(1)]),
                         100.0 * (1 + net).cumprod()])
        out[f"{name} | sharpe"] = _perf_stats(lvl)["sharpe_rf0"]
        # The maximin does not optimize Sharpe — it maximizes the WORST per-quadrant mean. So
        # scoring the placebo on Sharpe alone tests it on a metric it never claimed. The fair
        # score is the realized floor: for the weights each arm CHOSE, the worst mean monthly
        # OOS return across the four REAL quadrants. Real labels always, so the floor means the
        # same thing in every arm — scoring a scrambled-label portfolio against its own
        # scrambled quadrants would be circular.
        out[f"{name} | floor"] = _realized_floor(net, real_labels)
    out["_n_refits"] = n_refits
    return out


def _realized_floor(net: pd.Series, real_labels: pd.DataFrame) -> float:
    """Worst mean monthly OOS return across the four REAL macro quadrants (min 3 months)."""
    if real_labels is None:
        return np.nan
    lab = real_labels.state.reindex(net.index)
    means = net.groupby(lab).agg(["mean", "size"])
    means = means[means["size"] >= 3]["mean"]
    return float(means.min()) if len(means) else np.nan


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
    """Per (contestant, metric, mode): the real value against the scrambled-label null."""
    real = df[df.arm == "real"].iloc[0]
    cols = [c for c in df.columns if " | " in c]
    rows = []
    for mode in sorted(df[df.arm == "placebo"]["mode"].unique()):
        sub = df[(df.arm == "placebo") & (df["mode"] == mode)]
        for col in cols:
            name, metric = col.split(" | ")
            if not np.isfinite(real[col]):
                continue
            null = sub[col].dropna().values
            if not len(null):
                continue
            # one-sided permutation p (bigger is better for BOTH metrics: Sharpe, and the
            # realized floor, which is least-negative-is-best); real arm in the reference set
            p = (1 + int((null >= real[col]).sum())) / (1 + len(null))
            rows.append(dict(portfolio=name, metric=metric, mode=mode,
                             real=float(real[col]),
                             placebo_mean=float(null.mean()),
                             placebo_sd=float(null.std(ddof=1)),
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
         "**Two metrics, because Sharpe alone would test the maximin on a target it never "
         "claimed.** `sharpe` is the net OOS Sharpe. `floor` is the realized worst mean monthly "
         "return across the four **REAL** quadrants, for whatever weights each arm chose — the "
         "quantity the maximin actually optimizes. The floor is always scored on real labels: "
         "grading a scrambled-label portfolio against its own scrambled quadrants would be "
         "circular.", "",
         "`p_perm` is the one-sided share of scrambled replicates reaching the real value "
         "(bigger is better for both metrics; the real arm counts in the reference set, so the "
         f"smallest attainable p is 1/{b + 1} = {1 / (b + 1):.3f}).", ""]
    for metric, title, fmt in (("sharpe", "Net OOS Sharpe", "{:.3f}"),
                               ("floor", "Realized floor — worst REAL-quadrant mean monthly "
                                         "return (the maximin's actual objective)", "{:+.4%}")):
        sub = v[v.metric == metric]
        if not len(sub):
            continue
        L += [f"## {title}", "",
              "| portfolio | mode | real | placebo mean | placebo sd | placebo p5–p95 | p_perm |",
              "|---|---|---|---|---|---|---|"]
        for _, r in sub.iterrows():
            L.append(f"| {r.portfolio} | {r['mode']} | {fmt.format(r.real)} | "
                     f"{fmt.format(r.placebo_mean)} | {fmt.format(r.placebo_sd)} | "
                     f"{fmt.format(r.placebo_p05)} – {fmt.format(r.placebo_p95)} | "
                     f"{r.p_perm:.3f} |")
        L += [""]
    ctrl = v[(v.portfolio == CONTROL) & (v.metric == "sharpe")]
    L += ["## Invariance check", ""]
    if len(ctrl):
        ok = bool(np.allclose(ctrl.placebo_sd.values, 0.0, atol=1e-12))
        L.append(f"- **{CONTROL}** consumes no labels, so its Sharpe must be identical in every "
                 f"arm — placebo sd = {ctrl.placebo_sd.max():.2e}. "
                 f"{'PASS.' if ok else '**FAIL — the harness is leaking.**'}")
    L += ["", "## Verdict", ""]
    for _, r in v[v.portfolio != CONTROL].iterrows():
        if r.p_perm <= 0.05:
            verdict = "the real labels carry information the scrambled ones do not"
        elif r.real >= r.placebo_p95:
            verdict = "in the null's top 5% but short of the permutation threshold"
        elif r.real <= r.placebo_mean:
            verdict = ("**indistinguishable from random labels — and BELOW the scrambled mean**")
        else:
            verdict = "above the scrambled mean but inside the null distribution"
        fmt = "{:.3f}" if r.metric == "sharpe" else "{:+.4%}"
        L.append(f"- **{r.portfolio}** · {r.metric} ({r['mode']}): real {fmt.format(r.real)} vs "
                 f"null {fmt.format(r.placebo_mean)} ± {fmt.format(r.placebo_sd)}, "
                 f"p = {r.p_perm:.3f} — {verdict}.")
    L += ["", "_Conservative by construction: the rotation is applied once to the full history, "
          "so a placebo training window can receive labels from months after its own end. That "
          "can only help the placebo._", ""]
    C.OPTIMIZER_PLACEBO_REPORT.write_text("\n".join(L))


# ------------------------------------- the estimator A/B under scrambled labels (M35)

def estimator_ab(b: int = None, mode: str = "circular", seed: int = 777) -> pd.DataFrame:
    """Is the era-agreement-gated estimator a REGIME-INFORMATION device or a SHRINKAGE device?

    M32 settled that the LABELS add nothing to allocation. This settles what the ESTIMATOR is,
    which is a different mechanism with its own switch (`config.OPTIMIZER_ANCHOR_LONG`): when
    ON, each per-quadrant mean is pulled toward its 66-year Fama-French counterpart, weighted by
    months of evidence, only in cells where both eras agree on that factor's sign.

    Design — a paired DIFFERENCE OF DIFFERENCES:

        Delta_real     = score(anchor ON) - score(anchor OFF)   under the real labels
        Delta_placebo  = score(anchor ON) - score(anchor OFF)   under scrambled labels

    Both switch positions are run on the SAME scrambled labels within a replicate, so the noise
    of that particular shuffle cancels in the difference. That is where the power comes from: an
    unpaired design would drown Delta (~0.002-0.016 Sharpe) in a null with sd ~0.14.

    Reading:
      Delta_placebo ~ Delta_real  => SHRINKAGE. Pulling noisy cell means toward a long sample
                                    reduces estimation error whether or not the conditioning
                                    variable means anything. The paper says exactly that.
      Delta_placebo ~ 0 < Delta_real => the conditioning matters for the ESTIMATOR even though
                                    it does not for allocation, and M32's re-interpretation of
                                    M5/M10/M16 must be withdrawn.

    **What this design does NOT test, stated because it is easy to assume otherwise:** the
    agreement GATE is not degraded by scrambling. The gate compares sign(long-era mean) with
    sign(modern-era mean) OF THE FAMA-FRENCH FACTOR ITSELF (`long_history.msci_factor_prior`),
    computed from the real classifier over the real FF history — by design, per `info/
    estimator.md` ("era sign-agreement of j's own record", j = the long series). It is a
    property of that factor's two eras, not of our menu's labelling, so it opens exactly the
    same cells in every arm. What IS scrambled is the modern per-quadrant means being shrunk.
    So the question this answers is precisely "does pulling arbitrary-subset means toward real
    long-run quadrant values still help?" — the shrinkage question, cleanly.

    Only the `circular` null is used (the referee-grade one: marginals, run lengths and the
    transition matrix preserved exactly).
    """
    C.ensure_dirs()
    b = C.OPTIMIZER_ESTIMATOR_AB_B if b is None else b
    states_real = opt._load_states(opt.load_returns().index)
    if states_real is None:
        print("[estimator-ab] macro-state labels absent — skipped")
        return pd.DataFrame()

    shipped = C.OPTIMIZER_ANCHOR_LONG
    t0 = time.time()
    rows = []

    def _pair(states, arm, replicate):
        out = {}
        for anchor in (False, True):
            try:
                C.OPTIMIZER_ANCHOR_LONG = anchor
                res = _regime_walk_forward(states=states)
            finally:
                C.OPTIMIZER_ANCHOR_LONG = shipped
            res.pop("_n_refits", None)
            out[anchor] = res
        row = dict(arm=arm, replicate=replicate)
        for k in out[True]:
            row[f"{k} | OFF"] = out[False].get(k, np.nan)
            row[f"{k} | ON"] = out[True][k]
            row[f"{k} | delta"] = out[True][k] - out[False].get(k, np.nan)
        return row

    real = _pair(None, "real", 0)
    rows.append(real)
    print(f"[estimator-ab] real arm ({time.time() - t0:.0f}s): "
          + "  ".join(f"{k.split(' | ')[0]} {v:+.4f}"
                      for k, v in real.items() if k.endswith("| delta") and "sharpe" in k))

    rng = np.random.default_rng(seed)
    for i in range(b):
        row = _pair(scramble_states(states_real, mode, rng), "placebo", i + 1)
        rows.append(row)
        print(f"[estimator-ab] {mode} {i + 1}/{b}  "
              + "  ".join(f"{k.split(' | ')[0]} {v:+.4f}"
                          for k, v in row.items() if k.endswith("| delta") and "sharpe" in k))

    df = pd.DataFrame(rows)
    df.to_csv(C.OPTIMIZER_ESTIMATOR_AB, index=False)
    _write_estimator_report(df, b, mode)
    print(f"[estimator-ab] wrote {C.OPTIMIZER_ESTIMATOR_AB} and "
          f"{C.OPTIMIZER_ESTIMATOR_AB_REPORT} ({time.time() - t0:.0f}s)")
    return df


def estimator_verdicts(df: pd.DataFrame) -> pd.DataFrame:
    real = df[df.arm == "real"].iloc[0]
    sub = df[df.arm == "placebo"]
    rows = []
    for col in [c for c in df.columns if c.endswith("| delta")]:
        name, metric, _ = col.split(" | ")
        if not np.isfinite(real[col]):
            continue
        null = sub[col].dropna().values
        if not len(null):
            continue
        rows.append(dict(portfolio=name, metric=metric,
                         delta_real=float(real[col]),
                         delta_placebo_mean=float(null.mean()),
                         delta_placebo_sd=float(null.std(ddof=1)),
                         share_placebo_positive=float((null > 0).mean()),
                         p_real_exceeds=(1 + int((null >= real[col]).sum())) / (1 + len(null)),
                         n_placebo=len(null)))
    return pd.DataFrame(rows)


def _write_estimator_report(df: pd.DataFrame, b: int, mode: str):
    v = estimator_verdicts(df)
    L = ["# Is the estimator a shrinkage device or a regime-information device? (M35)", "",
         "M32 showed the macro LABELS add nothing to allocation. This asks what the "
         "**estimator** is — a different mechanism with its own switch "
         "(`OPTIMIZER_ANCHOR_LONG`): per-quadrant means pulled toward their 66-year "
         "Fama-French counterparts, month-weighted, only where both eras agree on that "
         "factor's sign.", "",
         "Paired difference of differences: within each replicate the switch is run OFF and ON "
         "on the **same** scrambled labels, so that shuffle's noise cancels in the delta. "
         f"{b} replicates, `{mode}` null.", "",
         "- **Δ_placebo ≈ Δ_real** ⇒ SHRINKAGE: the gain does not need the labels to mean "
         "anything.",
         "- **Δ_placebo ≈ 0 < Δ_real** ⇒ the conditioning matters for the estimator after all, "
         "and M32's re-interpretation of M5/M10/M16 must be withdrawn.", "",
         "_Not tested here: the agreement GATE is not degraded by scrambling — it compares the "
         "two eras of the Fama-French factor's OWN record (`long_history.msci_factor_prior`), "
         "so it opens the same cells in every arm by design. What is scrambled is the modern "
         "per-quadrant means being shrunk._", ""]
    for metric, title, fmt in (("sharpe", "Net OOS Sharpe", "{:+.4f}"),
                               ("floor", "Realized floor (worst REAL-quadrant mean monthly "
                                         "return)", "{:+.4%}")):
        sub = v[v.metric == metric]
        if not len(sub):
            continue
        L += [f"## Δ (anchor ON − OFF) — {title}", "",
              "| portfolio | Δ real | Δ placebo mean | Δ placebo sd | % of placebo replicates "
              "where the estimator HELPS | p (real ≥ placebo) |", "|---|---|---|---|---|---|"]
        for _, r in sub.iterrows():
            L.append(f"| {r.portfolio} | {fmt.format(r.delta_real)} | "
                     f"{fmt.format(r.delta_placebo_mean)} | {fmt.format(r.delta_placebo_sd)} | "
                     f"{r.share_placebo_positive:.0%} | {r.p_real_exceeds:.3f} |")
        L += [""]
    L += ["## Verdict", ""]
    for _, r in v[v.portfolio != CONTROL].iterrows():
        fmt = "{:+.4f}" if r.metric == "sharpe" else "{:+.4%}"
        if r.delta_placebo_mean > 0 and r.share_placebo_positive >= 0.6:
            verdict = ("**SHRINKAGE — the estimator still helps with meaningless labels** "
                       f"({r.share_placebo_positive:.0%} of replicates)")
        elif r.delta_real > 0 and r.delta_placebo_mean <= 0:
            verdict = ("**the estimator helps ONLY with real labels — the conditioning "
                       "matters**")
        else:
            verdict = "inconclusive on this contestant"
        L.append(f"- **{r.portfolio}** · {r.metric}: Δ_real {fmt.format(r.delta_real)} vs "
                 f"Δ_placebo {fmt.format(r.delta_placebo_mean)} ± "
                 f"{fmt.format(r.delta_placebo_sd)} — {verdict}.")
    L += ["", "_1/N is carried through as the invariance control: it consumes neither labels "
          "nor the estimator, so every Δ on its row must be exactly zero._", ""]
    C.OPTIMIZER_ESTIMATOR_AB_REPORT.write_text("\n".join(L))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Random-regime placebo (permutation test)")
    ap.add_argument("--b", type=int, default=None, help="replicates per mode")
    ap.add_argument("--mode", choices=["circular", "iid"], default=None,
                    help="only this shuffle mode (default: both)")
    ap.add_argument("--estimator", action="store_true",
                    help="run the estimator A/B under scrambled labels (M35) instead")
    args = ap.parse_args()
    if args.estimator:
        estimator_ab(b=args.b, mode=args.mode or "circular")
    else:
        run(b=args.b, modes=(args.mode,) if args.mode else ("circular", "iid"))
