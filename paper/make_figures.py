"""Paper figures — static PDFs from the SAME cached CSVs the ledger cites.

One figure per file in paper/figures/, matched to paper/draft.md Appendix B. Rerunnable any
time the pipeline/CLI probes have refreshed their CSVs; nothing here computes new results.

Run:  python paper/make_figures.py        (from the repo root)
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from portfolio_lab import config as C  # noqa: E402

OUT = ROOT / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

INK, MUT, LINE = "#1D1D1F", "#6E6E73", "#D8D8DE"
PCOLOR = {"1/N": "#8E8E93", "ERC (anchor)": "#3B6FD4", "HRP": "#7A5FD0",
          "Min-variance": "#2E9E68", "Balanced sliders (5/5/5)": "#E08A00",
          "Maximin (worst quadrant)": "#C94F4F", "Maximin (diversified)": "#1F8A99",
          "Maximin (all-weather div)": "#8C6D1F", "Momentum 12-1 (top 6)": "#B5892E",
          "1/N + vol-target": "#5AA6B5", "Min-variance + vol-target": "#4E8F7B"}


def pc(name: str) -> str:
    return PCOLOR.get(name, "#E08A00")


def style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="both", color=LINE, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(colors=INK, labelsize=8.5)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, bbox_inches="tight")
    plt.close(fig)
    print(f"[figures] wrote figures/{name}")


def f0_dispersion():
    """THE PILLAR FIGURE (v0.2). Two panels:
      A — long-only factor tilts do NOT decorrelate (within-region cross-factor corr is the
          HIGHEST cut of the menu), while three asset classes do; the DR² mechanism made visual.
      B — independent risk bets (DR²) barely move across 28 equity sleeves, and a 4-sleeve
          min-variance portfolio holds as many as the whole menu; adding 3 asset classes buys
          more than 24 equity sleeves.
    All numbers recomputed from the same cached inputs the ledger cites (M27/M34)."""
    import itertools
    from portfolio_lab.portfolio import optimizer as opt

    lv = pd.read_csv(C.LEVELS_WIDE, index_col=0, parse_dates=True).sort_index()
    r = lv.pct_change().dropna()
    cols = list(r.columns)
    corr = r.corr()
    reg = lambda c: c.split(" | ")[0]
    fac = lambda c: c.split(" | ")[1]
    within = [corr.loc[a, b] for a, b in itertools.combinations(cols, 2) if reg(a) == reg(b)]
    same_fac = [corr.loc[a, b] for a, b in itertools.combinations(cols, 2)
                if fac(a) == fac(b) and reg(a) != reg(b)]
    cross_ref = [corr.loc[a, b] for a, b in
                 itertools.combinations([c for c in cols if fac(c) == "Reference"], 2)]

    ac = pd.read_csv(C.ASSET_CLASS_MONTHLY, index_col=0, parse_dates=True)
    j = r.join(ac, how="inner")
    eq = [c for c in j.columns if not c.startswith("Asset")]
    ac_corr = {c.split(" | ")[1]: float(np.mean([j[c].corr(j[e]) for e in eq]))
               for c in j.columns if c.startswith("Asset")}

    labels = ["Same region,\ndiff. factors", "Same factor,\ndiff. regions",
              "Market beta,\nacross regions", "Treasuries\nvs equity", "Gold\nvs equity"]
    vals = [np.mean(within), np.mean(same_fac), np.mean(cross_ref),
            ac_corr.get("US Treasury 10y", np.nan), ac_corr.get("Gold", np.nan)]
    colors = ["#C94F4F", "#C97A4F", "#C9A24F", "#2E9E68", "#8C6D1F"]

    inp = opt.build_inputs()
    inp_aw = opt.build_inputs(include_asset_classes=True)
    dr2_eq = opt.diversification_ratio(np.ones(len(inp["series"])) / len(inp["series"]),
                                       inp["sigma"]) ** 2
    dr2_mv = opt.diversification_ratio(inp["anchors"]["Min-variance"], inp["sigma"]) ** 2
    dr2_aw = opt.diversification_ratio(np.ones(len(inp_aw["series"])) / len(inp_aw["series"]),
                                       inp_aw["sigma"]) ** 2

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(8.4, 3.8),
                                   gridspec_kw={"width_ratios": [1.7, 1.0]})

    # ---- Panel A: correlation cuts
    xA = np.arange(len(vals))
    axA.axhline(0, color=INK, lw=0.8)
    axA.bar(xA, vals, 0.62, color=colors, edgecolor="white", lw=0.5)
    for xi, v in zip(xA, vals):
        axA.text(xi, v + (0.035 if v >= 0 else -0.035), f"{v:+.2f}",
                 ha="center", va="bottom" if v >= 0 else "top", fontsize=8, color=INK)
    axA.set_xticks(xA, labels, fontsize=7.4)
    axA.set_ylabel("mean pairwise correlation", fontsize=9)
    axA.set_ylim(-0.32, 1.05)
    axA.set_title("A · Factor tilts don't decorrelate; asset classes do",
                  fontsize=9, loc="left", color=INK)
    style(axA)

    # ---- Panel B: independent bets (DR²)
    bl = ["28 equity\nsleeves (1/N)", "Min-variance\n(4 sleeves)", "+ 3 asset\nclasses (1/N)"]
    bv = [dr2_eq, dr2_mv, dr2_aw]
    bc = ["#8E8E93", "#2E9E68", "#1F8A99"]
    xB = np.arange(len(bv))
    axB.bar(xB, bv, 0.6, color=bc, edgecolor="white", lw=0.5)
    for xi, v in zip(xB, bv):
        axB.text(xi, v + 0.02, f"{v:.2f}", ha="center", va="bottom", fontsize=8.6, color=INK)
    axB.axhline(1.0, color=MUT, lw=0.9, ls=":")
    axB.text(2.4, 1.02, "1 bet", color=MUT, fontsize=7.5, ha="right", va="bottom")
    axB.set_xticks(xB, bl, fontsize=7.6)
    axB.set_ylabel("independent risk bets  (DR$^2$)", fontsize=9)
    axB.set_ylim(0, 1.7)
    axB.set_title("B · The menu is ~1 bet, however you weight it", fontsize=8.8,
                  loc="left", color=INK)
    style(axB)

    save(fig, "F0_dispersion.pdf")


def f0b_frontier_cloud():
    """The dispersion pillar, dramatized (the figure discussed with the owner). Two risk-return
    panels: the achievable set of long-only portfolios (a Dirichlet cloud) with the fielded
    rules on top. LEFT the 28-sleeve equity menu — a thin sliver, every rule piled together;
    RIGHT the menu extended with Treasuries/gold/cash — the set opens up and the rules spread.
    'Dispersion, not method' in one image: on a one-bet menu there is nowhere for weighting to
    go. Honest construction (our own note, mean-variance-and-estimation-error.md §6.1): the
    cloud is the BACKGROUND achievable set; we do not read a frontier off it (Dirichlet
    under-samples the high-return corners as N grows). Full-sample geometry, illustrative."""
    from portfolio_lab.portfolio import optimizer as opt
    ANN = np.sqrt(12.0)
    rng = np.random.default_rng(0)

    def panel(ax, inp, title, rules):
        R = inp["rets"].values
        mu = R.mean(0) * 12.0
        cov = np.cov(R, rowvar=False) * 12.0
        n = R.shape[1]
        W = rng.dirichlet(np.ones(n), 40000)
        pr = W @ mu
        pv = np.sqrt(np.einsum("ij,jk,ik->i", W, cov, W))
        ax.scatter(pv * 100, pr * 100, s=2, c="#D8D8DE", alpha=0.5, edgecolors="none",
                   rasterized=True)
        for name, w, col, mk, off in rules:
            v = float(np.sqrt(w @ cov @ w)) * 100
            r = float(w @ mu) * 100
            ax.scatter(v, r, s=52, c=col, edgecolors="white", lw=0.8, marker=mk, zorder=5)
            ax.annotate(name, (v, r), textcoords="offset points", xytext=off,
                        fontsize=7.2, color=INK, zorder=6)
        ax.set_xlabel("annualized volatility (%)", fontsize=9)
        ax.set_title(title, fontsize=9, loc="left", color=INK)
        style(ax)
        return pv.min() * 100, pv.max() * 100

    inp = opt.build_inputs()
    a = inp["anchors"]
    eq_rules = [("1/N", a["1/N"], "#8E8E93", "o", (6, 4)),
                ("Min-var", a["Min-variance"], "#2E9E68", "D", (-40, -2)),
                ("ERC", a["ERC (anchor)"], "#3B6FD4", "s", (6, 5)),
                ("HRP", a["HRP"], "#7A5FD0", "^", (6, -10))]

    # share BOTH axes: on a common scale the equity cloud is a narrow sliver at high vol while
    # the extended cloud fills the space to its left — the dispersion difference, made honest.
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(8.4, 4.0), sharex=True, sharey=True)
    panel(axL, inp, "A · 28-sleeve equity menu — one bet, rules piled together", eq_rules)
    axL.set_ylabel("annualized return (%)", fontsize=9)

    try:
        inp_aw = opt.build_inputs(include_asset_classes=True)
        aw = inp_aw["anchors"]
        aw_rules = [("1/N", aw["1/N"], "#8E8E93", "o", (6, 4)),
                    ("Min-var", aw["Min-variance"], "#2E9E68", "D", (8, 6)),
                    ("ERC", aw["ERC (anchor)"], "#3B6FD4", "s", (8, -2)),
                    ("HRP", aw["HRP"], "#7A5FD0", "^", (8, -12))]
        panel(axR, inp_aw, "B · + Treasuries / gold / cash — the set opens up", aw_rules)
    except Exception as e:
        axR.text(0.5, 0.5, f"(extended menu unavailable: {e})", ha="center", fontsize=8)

    save(fig, "F0b_frontier_cloud.pdf")


def f1_race():
    m = pd.read_csv(C.OPTIMIZER_WALKFORWARD_RETURNS, index_col=0, parse_dates=True)
    growth = 100.0 * (1.0 + m).cumprod()
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for col in growth.columns:
        lw = 1.9 if col in ("Min-variance", "1/N", "Maximin (all-weather div)") else 0.9
        ax.plot(growth.index, growth[col], color=pc(col), lw=lw, label=col,
                alpha=1.0 if lw > 1 else 0.75)
    ax.set_yscale("log")
    ax.set_ylabel("growth of 100 (log scale, net of costs)", fontsize=9)
    ax.legend(fontsize=6.7, ncol=2, frameon=False, loc="upper left")
    style(ax)
    save(fig, "F1_walkforward_race.pdf")


def f2_inference():
    inf = pd.read_csv(C.OPTIMIZER_INFERENCE)
    inf = inf[(inf.portfolio != "1/N") & inf["delta_ann_vs_1/N"].notna()]
    inf = inf.sort_values("delta_ann_vs_1/N")
    col = ["#C94F4F" if (p < 0.05 and d < 0) else "#2E9E68" if (p < 0.05 and d > 0)
           else "#B9B9C0" for p, d in zip(inf["p_boot_vs_1/N"], inf["delta_ann_vs_1/N"])]
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    y = np.arange(len(inf))
    ax.barh(y, inf["delta_ann_vs_1/N"], color=col, height=0.62)
    for yi, (d, p) in enumerate(zip(inf["delta_ann_vs_1/N"], inf["p_boot_vs_1/N"])):
        ax.text(d + (0.006 if d >= 0 else -0.006), yi, f"p={p:.3f}", va="center",
                ha="left" if d >= 0 else "right", fontsize=7.5, color=MUT)
    ax.set_yticks(y, inf.portfolio, fontsize=8.5)
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_xlabel("annualized OOS Sharpe difference vs 1/N (net)", fontsize=9)
    ax.set_xlim(inf["delta_ann_vs_1/N"].min() - 0.09, inf["delta_ann_vs_1/N"].max() + 0.09)
    style(ax)
    save(fig, "F2_inference_vs_1N.pdf")


def f3_loro():
    lo = pd.read_csv(C.OPTIMIZER_LORO)
    drops = list(dict.fromkeys(lo.dropped_region))
    lbl = ["full menu" if d == "none" else f"– {d.replace('_', ' ')}" for d in drops]
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    for p in dict.fromkeys(lo.portfolio):
        sub = lo[lo.portfolio == p].set_index("dropped_region").reindex(drops)
        ax.plot(range(len(drops)), sub["rank"], marker="o", ms=3.5, lw=1.2, color=pc(p),
                label=p)
    ax.set_xticks(range(len(drops)), lbl, rotation=28, ha="right", fontsize=8)
    ax.set_ylabel("rank (1 = best)", fontsize=9)
    ax.invert_yaxis()
    ax.set_yticks(range(1, int(lo["rank"].max()) + 1))
    ax.legend(fontsize=6.5, ncol=2, frameon=False, loc="lower right")
    style(ax)
    save(fig, "F3_leave_one_region_out.pdf")


def f4_virgin():
    ab = pd.read_csv(C.FF_INTL_AB, header=[0, 1], index_col=0)
    sh = ab.xs("oos_sharpe_rf0", axis=1, level=1)
    mx = [p for p in sh.index if p.startswith("Maximin")]
    rest = sh.drop(index=mx).sort_values("anchored", ascending=False).index.tolist()
    order = mx + rest
    x = np.arange(len(order))
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.bar(x - 0.2, sh.loc[order, "modern"], 0.38, color=[pc(p) for p in order], alpha=0.35,
           label="estimator OFF (modern-only)")
    ax.bar(x + 0.2, sh.loc[order, "anchored"], 0.38, color=[pc(p) for p in order],
           label="estimator ON (66y anchored)")
    for xi, p in enumerate(order):
        d = sh.loc[p, "anchored"] - sh.loc[p, "modern"]
        ax.text(xi, max(sh.loc[p, "modern"], sh.loc[p, "anchored"]) + 0.012,
                f"Δ{d:+.3f}", ha="center", fontsize=6.8, color=MUT)
    if "1/N" in sh.index:
        y1n = float(sh.loc["1/N", "anchored"])
        ax.axhline(y1n, color=INK, lw=1.0, ls="--")
        ax.text(len(order) - 0.5, y1n + 0.008, "1/N", color=INK, fontsize=7.5,
                ha="right", va="bottom")
    ax.set_xticks(x, order, rotation=28, ha="right", fontsize=7.6)
    # HONEST AXIS: bars start at zero, so the ±0.002–0.016 A/B deltas read as the noise band
    # they are (M35) — never a truncated axis that magnifies them.
    ax.set_ylim(0, max(sh.max().max() * 1.18, 0.8))
    ax.set_ylabel("net OOS Sharpe (virgin universe, 2000–2026)", fontsize=9)
    ax.set_title("Estimator ON vs OFF on the pre-registered virgin universe: everything "
                 "clusters, and the Δ is within the noise band (M35)",
                 fontsize=8.2, loc="left", color=INK)
    ax.legend(fontsize=8, frameon=False, loc="lower left")
    style(ax)
    save(fig, "F4_virgin_universe_ab.pdf")


def f5_sensitivity():
    sd = pd.read_csv(C.OPTIMIZER_SENSITIVITY)
    grid = sd[sd.portfolio.notna()] if "portfolio" in sd.columns else pd.DataFrame()
    blk = sd[sd.dimension == "lw_block"]
    dims = [("cost_bps", "cost {} bps"), ("refit_months", "refit {}m"),
            ("caps_slv_geo_fac", "caps {}")]
    cells = []
    for d, f in dims:
        for c in dict.fromkeys(grid[grid.dimension == d].cell):
            cells.append((d, c, f.format(c)))
    want = ["Min-variance", "1/N", "HRP", "Maximin (diversified)", "Maximin (all-weather div)"]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(8.6, 3.6), width_ratios=[2.4, 1])
    for p in want:
        ys = [grid[(grid.dimension == d) & (grid.cell == c)
                   & (grid.portfolio == p)].oos_sharpe.mean() for d, c, _ in cells]
        ax.plot(range(len(cells)), ys, marker="o", ms=3.5, lw=1.2, color=pc(p), label=p)
    ax.set_xticks(range(len(cells)), [l for _, _, l in cells], rotation=32, ha="right",
                  fontsize=7.6)
    ax.set_ylabel("net OOS Sharpe", fontsize=9)
    ax.legend(fontsize=6.8, frameon=False)
    style(ax)
    ax2.bar([f"b={c}" for c in blk.cell], blk.c2_p_minvar_vs_1N, color="#2E9E68", width=0.55)
    ax2.axhline(0.05, color="#C94F4F", lw=1, ls=":")
    ax2.text(len(blk) - 0.55, 0.052, "5%", color="#C94F4F", fontsize=8)
    ax2.set_ylabel("p (min-var vs 1/N)", fontsize=9)
    style(ax2)
    save(fig, "F5_sensitivity_grids.pdf")


def f6_attribution():
    at = pd.read_csv(C.OPTIMIZER_ATTRIBUTION)
    ports = ["Min-variance", "Maximin (diversified)", "Maximin (all-weather div)", "HRP"]
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    cmap = plt.get_cmap("tab20")
    sleeves = list(dict.fromkeys(
        at[at.portfolio.isin(ports)].sort_values("share", ascending=False).sleeve))
    scolor = {s: cmap(i % 20) for i, s in enumerate(sleeves)}
    for xi, p in enumerate(ports):
        sub = at[at.portfolio == p].sort_values("share", ascending=False)
        bottom = 0.0
        for r in sub.itertuples():
            if r.share <= 0:
                continue
            ax.bar(xi, r.share, 0.6, bottom=bottom, color=scolor[r.sleeve],
                   edgecolor="white", lw=0.4)
            if r.share > 0.08:
                ax.text(xi, bottom + r.share / 2, f"{r.sleeve.replace(' | ', ' ')}\n"
                        f"{r.share:.0%}", ha="center", va="center", fontsize=6.4)
            bottom += r.share
    ax.set_xticks(range(len(ports)), ports, fontsize=8.2)
    ax.set_ylabel("share of OOS return (arithmetic)", fontsize=9)
    ax.set_ylim(0, 1.02)
    style(ax)
    save(fig, "F6_attribution.pdf")


def f7_placebo():
    """The two null results in one figure (M32 labels). For each maximin contestant, the
    scrambled-label null distribution of net OOS Sharpe with the real value marked — the
    permutation test that attacks our own signature feature, shown honestly."""
    fp = C.OPTIMIZER_PLACEBO
    if not fp.exists():
        raise FileNotFoundError(fp)
    df = pd.read_csv(fp)
    real = df[df.arm == "real"].iloc[0]
    circ = df[(df.arm == "placebo") & (df["mode"] == "circular")]
    ports = ["Maximin (worst quadrant)", "Maximin (diversified)", "Maximin (all-weather div)"]
    fig, axes = plt.subplots(1, 3, figsize=(8.4, 3.0), sharey=True)
    for ax, p in zip(axes, ports):
        col = f"{p} | sharpe"
        if col not in df.columns:
            continue
        null = circ[col].dropna().values
        ax.hist(null, bins=12, color="#C9C9CE", edgecolor="white", lw=0.5)
        ax.axvline(float(real[col]), color="#C94F4F", lw=1.8)
        ax.axvline(float(null.mean()), color=INK, lw=1.0, ls=":")
        ax.text(float(real[col]), ax.get_ylim()[1] * 0.96, " real", color="#C94F4F",
                fontsize=7.5, ha="left", va="top")
        p_perm = (1 + int((null >= float(real[col])).sum())) / (1 + len(null))
        ax.set_title(f"{p.replace('Maximin ', '').strip('()')}\np = {p_perm:.2f}",
                     fontsize=8.2, color=INK)
        ax.set_xlabel("net OOS Sharpe", fontsize=8.2)
        style(ax)
    axes[0].set_ylabel("scrambled-label replicates", fontsize=8.6)
    fig.suptitle("Real regime labels vs 40 scrambled-label replicates (circular null)",
                 fontsize=9.2, color=INK, y=1.02)
    save(fig, "F7_placebo_null.pdf")


if __name__ == "__main__":
    for fn in (f0_dispersion, f0b_frontier_cloud, f1_race, f2_inference, f3_loro, f4_virgin,
               f5_sensitivity, f6_attribution, f7_placebo):
        try:
            fn()
        except Exception as e:
            print(f"[figures] WARN {fn.__name__} skipped ({e})")
