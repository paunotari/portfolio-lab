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
    """PDF for submission quality, PNG alongside it so the figures render inline when the
    draft is read as markdown (draft.md embeds the PNGs)."""
    fig.tight_layout()
    fig.savefig(OUT / name, bbox_inches="tight")
    fig.savefig(OUT / name.replace(".pdf", ".png"), bbox_inches="tight", dpi=160)
    plt.close(fig)
    print(f"[figures] wrote figures/{name} (+ .png)")


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
    # v3: two colours, not five. Red/green carry loss/gain valence in finance, which these
    # bars do not mean, and red/green is also the worst pair for colour vision deficiency.
    # Five arbitrary hues encoded nothing; a single colour would have hidden the grouping that
    # IS the finding. So: grey = equity-vs-equity cuts, teal = asset-class-vs-equity. Those are
    # the same two colours panel B already uses for the equity menu and the extended one, so
    # across the whole exhibit grey means equity and teal means asset class.
    EQ, AC = "#8E8E93", "#1F8A99"
    colors = [EQ, EQ, EQ, AC, AC]

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
    # v3: the descriptive title moves to the LaTeX exhibit label. Scaled to \textwidth a
    # matplotlib title renders at ~6pt, smaller than body text, and duplicates the caption.
    axA.set_title("A", fontsize=10, loc="left", color=INK, fontweight="bold")
    style(axA)

    # ---- Panel B: independent bets (DR²)
    bl = ["28 equity\nsleeves (1/N)", "Min-variance\n(4 sleeves)", "+ 3 asset\nclasses (1/N)"]
    bv = [dr2_eq, dr2_mv, dr2_aw]
    bc = ["#8E8E93", "#2E9E68", "#1F8A99"]
    xB = np.arange(len(bv))
    # DR2 = 1 means NO diversification at all, so only the part above 1.0 is real. Shading the
    # dead band stops the eye reading 1.31 vs 1.43 as "nearly the same bar" (M39).
    axB.axhspan(0, 1.0, color="#F0F0F3", zorder=0)
    axB.bar(xB, bv, 0.6, color=bc, edgecolor="white", lw=0.5, zorder=2)
    # 95% bootstrap CI on the equity menu's DR2 (M39); the other two are not bootstrapped here
    axB.errorbar([0], [bv[0]], yerr=[[bv[0] - 1.242], [1.399 - bv[0]]], fmt="none",
                 ecolor=INK, elinewidth=1.1, capsize=4, zorder=3)
    for xi, v in zip(xB, bv):
        top = 1.399 if xi == 0 else v          # clear the CI cap on the bootstrapped bar
        axB.text(xi, top + 0.045, f"{v:.2f}", ha="center", va="bottom", fontsize=8.6,
                 color=INK, zorder=4)
    axB.axhline(1.0, color=MUT, lw=0.9, ls=":", zorder=1)
    # label the reference line at the right margin, clear of every bar: centred inside the
    # shaded band it was grey-on-grey and half-covered by the middle bar.
    # x=0.5 is the gap between bars 1 and 2, and y just above 1.0 is above the shading:
    # the only spot in this panel that is empty at every height.
    axB.text(0.5, 1.03, "1 bet", color=MUT, fontsize=6.5, ha="center", va="bottom", zorder=4)
    axB.set_xlim(-0.55, 2.55)
    axB.set_xticks(xB, bl, fontsize=7.6)
    axB.set_ylabel("independent risk bets  (DR$^2$)", fontsize=9)
    axB.set_ylim(0, 1.7)
    axB.set_title("B", fontsize=10, loc="left", color=INK, fontweight="bold")
    style(axB)

    save(fig, "F0_dispersion.pdf")


def f0b_frontier_cloud():
    """THE PILLAR FIGURE. What a long-only investor can actually reach on each menu.

    v2 (2026-08) — the v1 of this figure did not show what its caption claimed. It drew a
    Dirichlet cloud of random weights, and a uniform Dirichlet over N sleeves concentrates
    almost all its mass NEAR 1/N: both panels therefore rendered as similar blobs, hiding the
    very difference the figure exists to show. (The v1 docstring already flagged the sampling
    problem; the plot was never changed.) The claim itself is true and stronger than v1 showed:
    the extended menu's achievable region is roughly twice the area, and the decisive fact is
    the LEFT EDGE — on equities alone no long-only portfolio reaches below ~14% volatility,
    while the extended menu reaches 0.6%.

    So v2 draws the boundary instead of sampling the interior: the long-only minimum-variance
    frontier (SLSQP per target return, the same solver `anchors.min_var_weights` uses), the
    individual sleeves, and the fielded rules. Full-sample geometry, illustrative."""
    from scipy.optimize import minimize
    from portfolio_lab.portfolio import anchors, optimizer as opt

    def frontier(mu, cov, k=40):
        """Long-only EFFICIENT frontier: min w'Sw s.t. w'mu = target, w>=0, sum w = 1.

        Swept upward from the global minimum-variance portfolio's own return, not from
        mu.min(). Below that return every solution is on the inefficient lower branch, where
        SLSQP has no unique basin and returns a different local answer per target — which is
        what made the first attempt at this figure render as a sawtooth instead of an arc."""
        n = len(mu)
        pts = []
        w_mv = anchors.min_var_weights(cov)
        r_mv = float(w_mv @ mu)
        pts.append((float(np.sqrt(w_mv @ cov @ w_mv)) * 100, r_mv * 100))
        w0 = w_mv.copy()
        for tgt in np.linspace(r_mv, mu.max(), k)[1:]:
            res = minimize(lambda w: w @ cov @ w, w0, jac=lambda w: 2.0 * cov @ w,
                           method="SLSQP", bounds=[(0.0, 1.0)] * n,
                           constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0},
                                        {"type": "eq", "fun": lambda w, t=tgt: w @ mu - t}],
                           options={"maxiter": 400, "ftol": 1e-11})
            if res.success:
                w = np.clip(res.x, 0, None)
                s = w.sum()
                if s > 0:
                    w = w / s
                    w0 = w                      # warm start: the frontier is continuous
                    pts.append((float(np.sqrt(w @ cov @ w)) * 100, float(w @ mu) * 100))
        return np.array(sorted(pts)) if pts else np.empty((0, 2))

    def panel(ax, inp, title, rules):
        R = inp["rets"].values
        mu = R.mean(0) * 12.0
        cov = np.cov(R, rowvar=False) * 12.0
        vols = np.sqrt(np.diag(cov)) * 100
        ax.scatter(vols, mu * 100, s=14, c="#C9C9D0", edgecolors="none", zorder=2,
                   label="individual sleeves")
        F = frontier(mu, cov)
        if len(F):
            ax.plot(F[:, 0], F[:, 1], color=INK, lw=1.6, zorder=3,
                    label="long-only frontier")
            floor = F[:, 0].min()
            ax.axvline(floor, color="#C94F4F", lw=1.0, ls="--", zorder=1)
            ax.text(floor + 0.4, 0.97, f"nothing exists\nleft of {floor:.1f}%",
                    transform=ax.get_xaxis_transform(), fontsize=7.2, color="#C94F4F",
                    va="top", ha="left", zorder=6)
        for name, w, col, mk, off in rules:
            v, r = float(np.sqrt(w @ cov @ w)) * 100, float(w @ mu) * 100
            ax.scatter(v, r, s=54, c=col, edgecolors="white", lw=0.9, marker=mk, zorder=5)
            ax.annotate(name, (v, r), textcoords="offset points", xytext=off, fontsize=7.4,
                        color=INK, zorder=6,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
        ax.set_xlabel("annualized volatility (%)", fontsize=9)
        ax.set_title(title, fontsize=8.8, loc="left", color=INK)
        style(ax)

    inp = opt.build_inputs()
    a = inp["anchors"]
    # offsets chosen so the four labels never collide: rules pile into one corner here, which
    # is the point of the panel, so the labels fan out rather than sit on their markers.
    eq_rules = [("1/N", a["1/N"], "#8E8E93", "o", (8, 6)),
                ("Min-var", a["Min-variance"], "#2E9E68", "D", (-46, -4)),
                ("ERC", a["ERC (anchor)"], "#3B6FD4", "s", (8, -4)),
                ("HRP", a["HRP"], "#7A5FD0", "^", (8, -16))]

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(8.6, 4.1), sharex=True, sharey=True)
    panel(axL, inp, "A · 28 equity sleeves", eq_rules)
    axL.set_ylabel("annualized return (%)", fontsize=9)

    try:
        inp_aw = opt.build_inputs(include_asset_classes=True)
        aw = inp_aw["anchors"]
        aw_rules = [("1/N", aw["1/N"], "#8E8E93", "o", (8, 6)),
                    ("Min-var", aw["Min-variance"], "#2E9E68", "D", (14, 10)),
                    ("ERC", aw["ERC (anchor)"], "#3B6FD4", "s", (12, -2)),
                    ("HRP", aw["HRP"], "#7A5FD0", "^", (14, -12))]
        panel(axR, inp_aw, "B · + Treasuries / gold / cash", aw_rules)
    except Exception as e:
        axR.text(0.5, 0.5, f"(extended menu unavailable: {e})", ha="center", fontsize=8)

    h, l = axL.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.06), ncol=2, fontsize=8,
               frameon=False)
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
    """v2 (2026-08): HIGHLIGHT, don't enumerate. v1 drew 11 equally-weighted lines with the
    legend sitting on top of the data, so the finding it exists to show — the structural rules
    hold rank while the maximin family swings — was invisible in the tangle. v2 greys every
    stable rule into a background band and colours only the three lines that move, with the
    legend outside the plot."""
    lo = pd.read_csv(C.OPTIMIZER_LORO)
    drops = list(dict.fromkeys(lo.dropped_region))
    lbl = ["full menu" if d == "none" else f"– {d.replace('_', ' ')}" for d in drops]
    ports = list(dict.fromkeys(lo.portfolio))

    def path(p):
        return lo[lo.portfolio == p].set_index("dropped_region").reindex(drops)["rank"].values

    swing = {p: float(np.nanmax(path(p)) - np.nanmin(path(p))) for p in ports}
    # Select the maximin family BY NAME, not by a swing threshold: the paper's claim is about
    # that family specifically, and a threshold picked a set that did not match it (it colored
    # min-variance+vol-target and dropped the all-weather variant).
    movers = [p for p in ports if "Maximin" in p]
    fig, ax = plt.subplots(figsize=(7.8, 4.0))
    for p in ports:                                        # background: everything that holds
        if p not in movers:
            ax.plot(range(len(drops)), path(p), marker="o", ms=2.6, lw=1.0,
                    color="#C9C9D0", zorder=1)
    for p in movers:
        ax.plot(range(len(drops)), path(p), marker="o", ms=4.5, lw=2.0, color=pc(p),
                label=f"{p}  (moves {int(swing[p])} ranks)", zorder=3)
    # name the two anchors the reader needs even though they do not move
    for p, ha in (("Min-variance", "left"), ("1/N", "left")):
        if p in ports:
            ax.annotate(p, (0, path(p)[0]), textcoords="offset points", xytext=(-6, 0),
                        ha="right", va="center", fontsize=7.4, color=INK, zorder=4)
    ax.set_xticks(range(len(drops)), lbl, rotation=28, ha="right", fontsize=8)
    ax.set_ylabel("rank (1 = best)", fontsize=9)
    ax.invert_yaxis()
    ax.set_yticks(range(1, int(lo["rank"].max()) + 1))
    ax.set_xlim(-1.6, len(drops) - 0.6)
    ax.legend(fontsize=7, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.28),
              ncol=1)
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
    # Two colours only. v1 gave every portfolio its own hue, which encoded nothing — the
    # light/dark pairing already carries OFF/ON, so per-portfolio colour was pure noise.
    ax.bar(x - 0.2, sh.loc[order, "modern"], 0.38, color="#C9C9D0",
           label="estimator OFF (modern-only)")
    ax.bar(x + 0.2, sh.loc[order, "anchored"], 0.38, color="#1F8A99",
           label="estimator ON (66y anchored)")
    for xi, p in enumerate(order):
        d = sh.loc[p, "anchored"] - sh.loc[p, "modern"]
        # white bbox: in v1 the 1/N reference line struck straight through the Δ label of the
        # bar that happened to sit at its height.
        ax.text(xi, max(sh.loc[p, "modern"], sh.loc[p, "anchored"]) + 0.02,
                f"Δ{d:+.3f}", ha="center", fontsize=6.8, color=MUT, zorder=5,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none"))
    if "1/N" in sh.index:
        y1n = float(sh.loc["1/N", "anchored"])
        ax.axhline(y1n, color=INK, lw=1.0, ls="--", zorder=1)
        ax.text(-0.55, y1n, "1/N", color=INK, fontsize=7.5, ha="right", va="center")
    ax.set_xticks(x, order, rotation=28, ha="right", fontsize=7.6)
    ax.set_xlim(-1.1, len(order) - 0.4)
    # HONEST AXIS: bars start at zero, so the ±0.002–0.016 A/B deltas read as the noise band
    # they are (M35) — never a truncated axis that magnifies them.
    ax.set_ylim(0, max(sh.max().max() * 1.18, 0.8))
    ax.set_ylabel("net OOS Sharpe (virgin universe)", fontsize=9)
    style(ax)
    h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=8,
               frameon=False)
    save(fig, "F4_virgin_universe_ab.pdf")


def f5_sensitivity():
    """v2 (2026-08): SMALL MULTIPLES. v1 plotted three unrelated grid dimensions along one
    continuous x-axis, so the line segment joining "cost 25 bps" to "refit 6m" implied a trend
    between quantities that share no scale, and the eye read large movement in a figure whose
    caption says nothing flips. Each dimension now gets its own panel with its own axis, and
    the shared y-range across the three makes the real message visible: every line is flat.
    The fourth panel keeps the one genuine frontier, the headline p's block-length sensitivity."""
    sd = pd.read_csv(C.OPTIMIZER_SENSITIVITY)
    grid = sd[sd.portfolio.notna()] if "portfolio" in sd.columns else pd.DataFrame()
    blk = sd[sd.dimension == "lw_block"]
    dims = [("cost_bps", "{} bps", "transaction cost"),
            ("refit_months", "{}m", "refit cadence"),
            ("caps_slv_geo_fac", "{}", "diversification caps")]
    want = ["Min-variance", "1/N", "HRP", "Maximin (diversified)", "Maximin (all-weather div)"]

    fig, axes = plt.subplots(1, 4, figsize=(9.2, 3.2), width_ratios=[1, 1, 1.15, 0.9])
    lo, hi = [], []
    for k, (d, fmt, nice) in enumerate(dims):
        ax = axes[k]
        cells = list(dict.fromkeys(grid[grid.dimension == d].cell))
        for p in want:
            ys = [grid[(grid.dimension == d) & (grid.cell == c)
                       & (grid.portfolio == p)].oos_sharpe.mean() for c in cells]
            ax.plot(range(len(cells)), ys, marker="o", ms=3.5, lw=1.2, color=pc(p),
                    label=p if k == 0 else None)
            lo += [min(ys)]; hi += [max(ys)]
        ax.set_xticks(range(len(cells)), [fmt.format(c) for c in cells], fontsize=7.4)
        ax.set_xlim(-0.35, len(cells) - 0.65)
        ax.set_title(nice, fontsize=8.4, loc="left", color=INK)
        style(ax)
        if k:
            ax.tick_params(labelleft=False)
    pad = 0.02
    for k in range(3):
        axes[k].set_ylim(min(lo) - pad, max(hi) + pad)      # one shared scale: flat is flat
    axes[0].set_ylabel("net OOS Sharpe", fontsize=9)
    # legend below the figure, not on the data (it sat over the first panel in v2)

    ax2 = axes[3]
    ax2.bar([f"b={c}" for c in blk.cell], blk.c2_p_minvar_vs_1N, color="#2E9E68", width=0.55)
    ax2.axhline(0.05, color="#C94F4F", lw=1, ls=":")
    ax2.text(-0.4, 0.0525, "5%", color="#C94F4F", fontsize=7.5, va="bottom")
    ax2.set_ylabel("p (min-var vs 1/N)", fontsize=8.6)
    ax2.set_title("bootstrap block length", fontsize=8.4, loc="left", color=INK)
    ax2.tick_params(labelsize=7.4)
    style(ax2)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.10), ncol=5, fontsize=8,
               frameon=False)
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
        ax.axvline(float(null.mean()), color=INK, lw=1.0, ls=":",
                   label="mean of the scrambled runs")
        # v1 put this label inside the axes at 96% height, where it landed on the tallest bar,
        # and never said what the dotted line was.
        ax.text(float(real[col]), 0.90, " real labels", color="#C94F4F", fontsize=7.4,
                ha="left", va="top", transform=ax.get_xaxis_transform(), zorder=6,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
        p_perm = (1 + int((null >= float(real[col])).sum())) / (1 + len(null))
        ax.set_title(f"{p.replace('Maximin ', '').strip('()')}\np = {p_perm:.2f}",
                     fontsize=8.2, color=INK)
        ax.set_xlabel("net OOS Sharpe", fontsize=8.2)
        style(ax)
    axes[0].set_ylabel("scrambled-label replicates", fontsize=8.6)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.06), ncol=2, fontsize=8,
               frameon=False)
    save(fig, "F7_placebo_null.pdf")


if __name__ == "__main__":
    for fn in (f0_dispersion, f0b_frontier_cloud, f1_race, f2_inference, f3_loro, f4_virgin,
               f5_sensitivity, f6_attribution, f7_placebo):
        try:
            fn()
        except Exception as e:
            print(f"[figures] WARN {fn.__name__} skipped ({e})")
