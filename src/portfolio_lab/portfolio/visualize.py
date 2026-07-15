"""Optimizer comparison visualization — the method's evidence, as one self-contained HTML page.

Renders the optimizer's test/comparison machinery (the walk-forward race, the benchmark table,
the regime breakdown, the Black-Litterman tilt, the scenario cones) as charts with plain-language
captions, so the whole unified method (info/portfolio_optimization.md) can be *seen*:

  1. Walk-forward race        — cumulative out-of-sample growth of all contestants (the honesty
                                test: does anything beat 1/N on data it never saw?)
  2. Out-of-sample summary    — OOS Sharpe / CAGR / max drawdown per contestant
  3. Risk/return map          — every sleeve + every portfolio on one vol-vs-CAGR plane (why
                                blending beats picking; where each engine chooses to sit)
  4. Per-quadrant returns     — how each portfolio does in each macro quadrant (the maximin
                                story: lift the worst floor, give up the best ceiling)
  5. What the views changed   — anchor-implied returns Π vs BL posterior μ_BL per sleeve (the
                                whole Bayesian tilt, auditable)
  6. Weights vs risk          — where the money sits vs where the risk actually sits (Euler
                                risk contributions)
  7. Scenario cones           — simulated 10y CAGR ranges under current_conditions (validator,
                                not objective)

Same house pattern as the dashboard: data baked as JSON into a static HTML shell, Plotly from
CDN, light "research note" theme — no new Python dependency. Reuses the walk-forward CSVs cached
by the optimizer pipeline stage when present (recomputes them if not, ~1 min).

Run:  python -m portfolio_lab.portfolio.visualize     ->  outputs/analytics/optimizer/optimizer_viz.html
"""
from __future__ import annotations
import json

import numpy as np
import pandas as pd

from portfolio_lab import config as C
from portfolio_lab.portfolio import optimizer as opt

ANN = 12


def _short(state: str) -> str:
    return state.split(" (")[0]


def _ann(m: float) -> float:
    """Annualize a mean monthly return for display."""
    return (1.0 + m) ** ANN - 1.0


def _walkforward_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(summary, monthly returns) — from the pipeline stage's cache, else recomputed."""
    if C.OPTIMIZER_WALKFORWARD.exists() and C.OPTIMIZER_WALKFORWARD_RETURNS.exists():
        return (pd.read_csv(C.OPTIMIZER_WALKFORWARD),
                pd.read_csv(C.OPTIMIZER_WALKFORWARD_RETURNS, index_col=0, parse_dates=True))
    from portfolio_lab.portfolio.validation import walk_forward
    summary, _, monthly = walk_forward()
    return summary, monthly


def build_data() -> dict:
    inp = opt.build_inputs()
    rets, series = inp["rets"], inp["series"]
    have_macro = inp["mu_q"] is not None and len(inp["mu_q"]) >= 2

    portfolios = {"Balanced sliders (5/5/5)": opt.optimize(
        prefs={"return": 5, "risk": 5, "diversification": 5}, inputs=inp)}
    if have_macro:
        portfolios["Maximin (worst quadrant)"] = opt.optimize(maximin=True, inputs=inp)
        portfolios[f"Maximin (geo ≤{C.OPTIMIZER_GEO_CAP_PCT:.0f}%)"] = opt.optimize(
            maximin=True, geo_cap=C.OPTIMIZER_GEO_CAP_PCT / 100.0, inputs=inp)

    # 1-2. walk-forward race + summary
    wf_summary, wf_monthly = _walkforward_data()
    growth = 100.0 * (1.0 + wf_monthly).cumprod()
    wf = dict(dates=[str(d.date()) for d in growth.index],
              growth={c: [round(v, 2) for v in growth[c]] for c in growth.columns},
              summary=wf_summary.to_dict("records"))

    # 3. risk/return map: every sleeve faint, every portfolio bold
    sleeve_pts = []
    for col in series:
        r = rets[col]
        cagr = float(np.prod(1 + r.values) ** (ANN / len(r)) - 1)
        sleeve_pts.append(dict(name=col, vol=float(r.std() * np.sqrt(ANN)), cagr=cagr,
                               factor=col.split(" | ")[1]))
    port_pts = []
    for name, w in inp["anchors"].items():
        p = opt._perf_stats(opt.blended_level(rets, w))
        port_pts.append(dict(name=name, vol=p["ann_vol"], cagr=p["CAGR"]))
    for name, res in portfolios.items():
        p = res["performance"]
        port_pts.append(dict(name=name, vol=p["ann_vol"], cagr=p["CAGR"]))

    # 4. per-quadrant annualized returns for 1/N vs the flagships
    quad = None
    if have_macro:
        mu_q = inp["mu_q"]
        states = list(mu_q.index)
        rows = {"1/N": inp["anchors"]["1/N"], "ERC (anchor)": inp["anchors"]["ERC (anchor)"]}
        rows.update({name: res["w"] for name, res in portfolios.items()})
        quad = dict(states=[_short(s) for s in states],
                    portfolios={name: [_ann(float(w @ mu_q.loc[s].values)) for s in states]
                                for name, w in rows.items()})

    # 5. Pi vs mu_BL (annualized, per sleeve)
    bl = dict(series=[s.replace(" | ", " · ") for s in series],
              pi=[_ann(v) for v in inp["pi"]], mu_bl=[_ann(v) for v in inp["mu_bl"]],
              views=[dict(view=v["view"], q_ann=_ann(v["q_monthly"]),
                          confidence=v["confidence"]) for v in inp["view_descs"]])

    # 6. weights vs risk contributions per flagship
    wrc = {}
    for name, res in portfolios.items():
        total_rc = sum(res["risk_contributions"].values()) or 1.0
        items = sorted(res["weights"].items(), key=lambda kv: kv[1])
        wrc[name] = dict(series=[s.replace(" | ", " · ") for s, _ in items],
                         weight=[w for _, w in items],
                         rc_share=[res["risk_contributions"].get(s, 0) / total_rc
                                   for s, _ in items])

    # 7. scenario cones for anchors + flagships
    cones = []
    if C.MACRO_STATE_MONTHLY.exists():
        from portfolio_lab.analytics.scenario import build_universe, portfolio_cone
        uni = build_universe()
        cone_sets = {"1/N": inp["anchors"]["1/N"], "ERC (anchor)": inp["anchors"]["ERC (anchor)"],
                     "Min-variance": inp["anchors"]["Min-variance"]}
        cone_sets.update({name: res["w"] for name, res in portfolios.items()})
        for name, w in cone_sets.items():
            full_w = {series[i]: float(w[i]) for i in range(len(series)) if w[i] > 0}
            cones.append(dict(name=name, **{k: v for k, v in portfolio_cone(full_w, uni=uni).items()
                                            if k not in ("scenario", "years")}))

    # roster holdings: the actual sleeves+weights each strategy lands on (grounds the formulas)
    wvecs = dict(inp["anchors"])                            # 1/N, ERC (anchor), HRP, Min-variance
    wvecs.update({name: res["w"] for name, res in portfolios.items()})
    roster_weights = {}
    Z, zones = inp["geo_Z"], inp["geo_zones"]
    for name, w in wvecs.items():
        pairs = sorted([[series[i].replace(" | ", " · "), round(float(w[i]), 4)]
                        for i in range(len(series)) if w[i] > 0.001], key=lambda kv: -kv[1])
        geo = {z: round(float(w @ Z[:, j]), 3) for j, z in enumerate(zones)}
        roster_weights[name] = dict(holdings=pairs, n_total=len(pairs), geo=geo)

    outlook = ({_short(k): round(float(v), 3) for k, v in inp["outlook"].items()}
               if inp["outlook"] else None)
    return dict(window=f"{rets.index[0].date()} → {rets.index[-1].date()}", T=inp["T"],
                n=len(series), delta_star=round(inp["delta_star"], 3), outlook=outlook,
                wf=wf, sleeves=sleeve_pts, portfolios=port_pts, quad=quad, bl=bl, wrc=wrc,
                cones=cones, roster_weights=roster_weights)


TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Optimizer — comparisons &amp; evidence</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root{--paper:#FBFBFD;--ink:#1D1D1F;--mut:#6E6E73;--line:#E3E3E8}
  body{background:var(--paper);color:var(--ink);margin:0;padding:0 20px 80px;
       font:15px/1.55 "Instrument Sans",-apple-system,Segoe UI,sans-serif;max-width:1080px;
       margin-inline:auto}
  h1{font-size:26px;margin:34px 0 4px} h2{font-size:19px;margin:44px 0 2px}
  .sub{color:var(--mut);font-size:13.5px;margin:0 0 10px}
  .cap{color:var(--mut);font-size:13.5px;max-width:820px;margin:2px 0 12px}
  .cap b{color:var(--ink)}
  .chart{border:1px solid var(--line);border-radius:10px;background:#fff;padding:6px}
  .num{font-family:"IBM Plex Mono",ui-monospace,monospace}
  hr{border:0;border-top:1px solid var(--line);margin:36px 0}
  details.more{max-width:820px;margin:0 0 14px;border:1px solid var(--line);border-radius:8px;
    background:#fff;font-size:13.5px;color:var(--mut)}
  details.more summary{cursor:pointer;padding:7px 12px;color:var(--ink);font-weight:600;
    font-size:13px;list-style-position:inside}
  details.more[open] summary{border-bottom:1px solid var(--line)}
  details.more .body{padding:10px 14px 12px}
  details.more code{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12.5px;
    background:#F4F4F7;border-radius:4px;padding:1px 5px;color:var(--ink);white-space:nowrap}
  details.more .frm{display:block;white-space:pre;overflow-x:auto;background:#F4F4F7;
    border-radius:6px;padding:8px 12px;margin:8px 0;font-family:"IBM Plex Mono",monospace;
    font-size:12.5px;color:var(--ink)}
  details.more a{color:#3B6FD4;text-decoration:none} details.more a:hover{text-decoration:underline}
  details.more .src{margin:8px 0 0;padding-left:18px} details.more .src li{margin:2px 0}
  details.more.intro{border-color:#C9C9D2;margin-bottom:20px}
  details.more.intro>summary{font-size:14px}
  .roster{margin:10px 0}
  .roster .rp{padding:9px 0;border-top:1px solid var(--line)}
  .roster .rp:first-child{border-top:0}
  .roster .rp b{color:var(--ink)}
  .roster .dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:7px;
    vertical-align:middle}
  .roster .p{font-size:12.5px}
  .mut{color:var(--mut)}
  .holds{margin:8px 0 2px}
  .holds .htitle{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--mut);
    margin-bottom:5px}
  .hbar{display:grid;grid-template-columns:180px 1fr 44px;align-items:center;gap:8px;margin:3px 0;
    font-size:12px}
  .hlab{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--ink)}
  .htrk{background:#F0F0F3;border-radius:3px;height:9px;overflow:hidden}
  .hfill{display:block;height:9px;border-radius:3px}
  .hpct{font-family:"IBM Plex Mono",monospace;text-align:right;color:var(--ink)}
  .hmore{font-size:11.5px;color:var(--mut);margin-top:4px}
  @media(max-width:620px){.hbar{grid-template-columns:130px 1fr 40px}}
  details.more .key{margin-top:12px;padding-top:10px;border-top:1px solid var(--line)}
</style></head><body>
<h1>Portfolio optimizer — comparisons &amp; evidence</h1>
<p class="sub">Common window <span class="num" id="win"></span> · covariance shrinkage
δ* <span class="num" id="dstar"></span> · generated by <span class="num">portfolio/visualize.py</span>.
Every chart is a claim from <b>info/portfolio_optimization.md</b> made visible.
Label: <b>historically optimal under stated priorities — not a forecast.</b></p>

<details class="more intro"><summary>New here? Meet the six portfolios these charts compare — principles, formulas &amp; papers</summary><div class="body">
<p>Every chart on this page pits the same six allocation strategies against each other. Four are
established methods from the portfolio-construction literature; two (marked ★) are ours, built on
top of that literature. The deepest thing separating them is <b>how much each one bets on
predicted returns</b> — the input the research says is the least trustworthy of all.</p>
<div class="roster">
<div class="rp" data-port="1/N"><span class="dot" style="background:#8E8E93"></span><b>1/N — equal weight</b><br>
Split the money equally across all sleeves and ignore every input. Not really a "method" — it's
the humble baseline the whole field measures against. <code>w_i = 1/N</code><br>
<span class="p mut">DeMiguel, Garlappi &amp; Uppal (2009), <a href="https://academic.oup.com/rfs/article-abstract/22/5/1915/1592901"><i>RFS</i></a> — raced 14 sophisticated models against it; none beat it reliably.</span>
<div class="holds"></div></div>
<div class="rp" data-port="Min-variance"><span class="dot" style="background:#2E9E68"></span><b>Min-variance</b><br>
Pick the weights that make total portfolio volatility as small as mathematically possible — and
ignore expected returns entirely. Naturally lands in the calmest, most mutually-hedging assets.
<code>min_w  wᵀΣw   s.t. Σw = 1, w ≥ 0</code><br>
<span class="p mut">Markowitz (1952), <i>JF</i> — the original efficient-frontier idea; Nobel Prize 1990.</span>
<div class="holds"></div></div>
<div class="rp" data-port="ERC (anchor)"><span class="dot" style="background:#3B6FD4"></span><b>ERC — Equal Risk Contribution (our neutral anchor)</b><br>
Give every sleeve an equal share of the <i>risk</i>, not of the money (60/40 in dollars is ~90/10
in risk — equities dominate). No return forecasts needed; its volatility provably sits between
min-variance and 1/N. <code>RC_i = w_i·(Σw)_i / σ_p   equal for all i</code><br>
<span class="p mut">Maillard, Roncalli &amp; Teïletche (2010), <i>JPM</i>; the philosophy behind Bridgewater's All Weather (1996).</span>
<div class="holds"></div></div>
<div class="rp" data-port="HRP"><span class="dot" style="background:#7A5FD0"></span><b>HRP — Hierarchical Risk Parity</b><br>
Cluster the assets into a correlation "family tree," then split capital down the branches — never
inverting the covariance matrix, so one bad estimate can't blow up the whole allocation.
<code>distance d_ij = √((1 − ρ_ij)/2)</code><br>
<span class="p mut">López de Prado (2016), <a href="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678"><i>JPM</i></a> — beats min-variance out-of-sample in the paper's own tests.</span>
<div class="holds"></div></div>
<div class="rp" data-port="Balanced sliders (5/5/5)"><span class="dot" style="background:#E08A00"></span><b>★ Balanced sliders — our unified method</b><br>
Start from the ERC anchor, tilt it <i>gently</i> with confidence-weighted Black-Litterman views,
then blend your three preferences (return / risk / diversification), each scored 0–100 on its own
attainable range. Bets on returns only in proportion to stated confidence — never freely.<br>
<span class="p mut">Black &amp; Litterman (1992, Goldman Sachs) over the shrinkage+anchor stack — full math in the per-chart blocks below.</span>
<div class="holds"></div></div>
<div class="rp" data-port="Maximin (worst quadrant)"><span class="dot" style="background:#C94F4F"></span><b>★ Maximin — our robust mode</b><br>
Don't chase the best case — make the <i>worst</i> macro quadrant as good as possible, so no
regime can sink you. Accepts higher volatility as the price of that safety.
<code>max_w  min_q  wᵀμ̂_q</code> (solved as a linear program)<br>
<span class="p mut">Ang &amp; Bekaert (2002/2004) — regime value comes from surviving the bad state; = All Weather's whole philosophy.</span>
<div class="holds"></div></div>
<div class="rp" data-port="Maximin (geo ≤40%)"><span class="dot" style="background:#1F8A99"></span><b>★ Maximin, geo-capped — robust <i>and</i> spread across the world</b><br>
Same worst-quadrant objective, plus a hard cap on the <b>look-through</b> exposure to each
geographic zone (North America / Europe / Asia-Pacific / Rest, from the factsheet country
weights — so an "EM" sleeve counts as the Asia it really holds). Within each zone the optimizer
still picks the best sleeves; the cap only forbids piling everything into one region — insurance
for the scenario where a different part of the world leads the next decade.
<code>max_w min_q wᵀμ̂_q   s.t.  wᵀZ_zone ≤ 40% ∀zone</code><br>
<span class="p mut">Constraints as implicit shrinkage: Jagannathan &amp; Ma (2003), <i>JF</i> — capping is itself a robustness device, not just a preference.</span>
<div class="holds"></div></div>
</div>
<p class="key"><b>The pattern to watch across the charts:</b> the four methods that bet <i>least</i>
on predicted returns (1/N, min-variance, ERC, HRP) are exactly the ones that win out of sample —
the literature's core lesson that at ~27 years of data, humility about return forecasts beats
cleverness. Full canon + verdicts: <span class="num">info/literature.md</span> and the deep dives
in <span class="num">info/literature/</span>.</p>
</div></details>

<h2>1 · The walk-forward race (out of sample)</h2>
<p class="cap">Each contestant re-estimates everything on an expanding training window and is
judged only on months it never saw (annual refits). <b>This is the honesty test</b>: DeMiguel
(2009) says that at 330 months nothing should reliably beat equal weight — watch whether the
clever lines actually separate from <b>1/N</b>.</p>
<details class="more"><summary>Method, math &amp; sources</summary><div class="body">
At each refit date t the training set is months 1…t only; every input (shrunk covariance,
anchors, μ_BL, per-quadrant means, transition matrix) is re-estimated on it, weights are held
constant-mix (rebalanced monthly to target) for the next 12 months, and only those unseen months
score. The plotted line is the compounded out-of-sample growth:
<span class="frm">G_T = 100 · ∏_{t&gt;warmup} (1 + r_t·w_{refit(t)})        warmup = 120 months, refit yearly</span>
Why this matters: in-sample comparisons flatter any optimizer (it saw the answers). The key
number behind the caption — sample-based mean-variance needs roughly <b>T ≈ 3,000 months for 25
assets</b> to reliably beat 1/N; we have 330. Best performers among DeMiguel's 14 models were the
most constrained ones — constraints act as implicit shrinkage.
<ul class="src">
<li>DeMiguel, Garlappi &amp; Uppal (2009), "Optimal Versus Naive Diversification" — <a href="https://academic.oup.com/rfs/article-abstract/22/5/1915/1592901">RFS 22(5)</a></li>
<li>Jagannathan &amp; Ma (2003), <i>JF</i> — no-short/cap constraints ≈ shrinking extreme covariances</li>
<li>Repo deep dive: <span class="num">info/literature/mean-variance-and-estimation-error.md</span> · code: <span class="num">portfolio/validation.py</span></li>
</ul></div></details>
<div id="race" class="chart" style="height:440px"></div>

<h2>2 · Out-of-sample scoreboard</h2>
<p class="cap">Same race as numbers, ranked by Sharpe (return per unit of risk), <b>net of
transaction costs</b>. <b>Min-variance winning is itself a literature result</b> (the
low-volatility anomaly + immunity to return-estimation error). This board now also judges
rule-based challengers — cross-sectional <b>momentum 12-1</b> and <b>volatility targeting</b>
overlays: as of the 2026-07 test <b>none beat min-variance</b>, and vol-targeting cut drawdowns
without lifting the Sharpe. Reporting a rule that <i>didn't</i> work is the method working.</p>
<details class="more"><summary>Method, math &amp; sources</summary><div class="body">
All statistics are computed on the stitched out-of-sample monthly returns only:
<span class="frm">Sharpe (rf=0) = 12·mean(r) / (σ(r)·√12)      CAGR = (level_end/level_start)^(12/n) − 1
maxDD = min_t ( level_t / max_{s≤t} level_s − 1 )      turnover/refit = Σ|w_new − w_old| / 2</span>
Hover any bar for its CAGR, max drawdown and turnover. Returns are net of a per-rebalance cost
(one-way turnover × the configured bps), so high-turnover rules can't look good for free — at
annual refits even momentum's cost barely moves it, which the gross-vs-net columns confirm.
Michaud's warning explains the base pattern: an optimizer given estimated means "goes long the
luckiest estimation errors," so the methods that use <i>less</i> estimated information (min-var
uses only covariance; 1/N uses nothing) survive best at small T. The two rule challengers test
that from the other side — <b>momentum 12-1</b> is the one legitimate use of past returns (right
horizon, re-tested as a rule); <b>volatility targeting</b> scales exposure down when trailing vol
runs hot. Both were beaten by min-variance here.
<ul class="src">
<li>Michaud (1989), "The Markowitz Optimization Enigma" — <i>FAJ</i> 45(1); Chopra &amp; Ziemba (1993), <i>JPM</i> — means ≈ 11× costlier than variances</li>
<li>Jegadeesh &amp; Titman (1993), <i>JF</i> — momentum; Moreira &amp; Muir (2017), "Volatility-Managed Portfolios" — <i>JF</i></li>
<li>Repo: <span class="num">mean-variance-and-estimation-error.md</span> · code: <span class="num">portfolio/rules.py</span>, <span class="num">validation.py</span></li>
</ul></div></details>
<div id="board" class="chart" style="height:460px"></div>

<h2>3 · The risk/return map</h2>
<p class="cap">Grey dots are the 21 individual sleeves over the full window; colored markers are
whole portfolios. <b>Diversified blends sit further left (less risk) than almost any single
sleeve at similar return</b> — that is the whole free lunch, and the different engines are just
different choices of where to sit on the cloud's edge.</p>
<details class="more"><summary>Method, math &amp; sources</summary><div class="body">
This is Markowitz's 1952 frame: a portfolio's return is the weighted average of its parts, but
its risk is <i>not</i> — imperfect correlations cancel some of it:
<span class="frm">μ_p = wᵀμ          σ_p² = wᵀΣw   ≤   (Σ_i w_i σ_i)²   whenever correlations &lt; 1</span>
Every portfolio here consumes the <b>Ledoit-Wolf shrunk</b> covariance rather than the raw sample
matrix — extreme sample correlations are mostly luck, so each entry is pulled toward a
constant-correlation target in proportion to its estimated noise:
<span class="frm">Σ̂ = δ*·F + (1−δ*)·S          δ* on this data = <b>__DSTAR__</b>  (closed-form, no tuning)</span>
The engines differ only in where they sit: min-variance solves <code>min wᵀΣw</code>; ERC
equalizes risk contributions; HRP splits capital down a correlation-distance cluster tree
(<code>d_ij = √((1−ρ_ij)/2)</code>, never inverting Σ); 1/N ignores the data entirely.
<ul class="src">
<li>Markowitz (1952), "Portfolio Selection" — <i>JF</i>; Nobel Prize 1990</li>
<li>Ledoit &amp; Wolf (2004), "Honey, I Shrunk the Sample Covariance Matrix" — <a href="http://www.ledoit.net/honey.pdf">JPM 30(4)</a></li>
<li>López de Prado (2016), "Building Diversified Portfolios that Outperform Out-of-Sample" — <a href="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678">JPM 42(4)</a> (HRP)</li>
<li>Repo deep dives: <span class="num">ledoit-wolf-shrinkage.md</span>, <span class="num">hierarchical-risk-parity.md</span> · code: <span class="num">portfolio/shrinkage.py</span>, <span class="num">anchors.py</span></li>
</ul></div></details>
<div id="map" class="chart" style="height:480px"></div>

<div id="quadsec">
<h2>4 · Per-quadrant behaviour — the maximin story</h2>
<p class="cap">Annualized return of each portfolio inside each macro quadrant's months.
<b>Maximin raises the worst bar (usually Stagflation) at the cost of the best bars</b> —
Ang-Bekaert's point that regime value comes from not being destroyed in the bad state,
All Weather's philosophy on our four quadrants.</p>
<details class="more"><summary>Method, math &amp; sources</summary><div class="body">
Each bar pools all months the 4-quadrant classifier labeled with that state (growth trend ×
inflation trend, composite z-scored indicators) and annualizes the portfolio's mean monthly
return there: <code>(1 + wᵀμ̂_q)¹² − 1</code>. The maximin portfolio solves "make the worst
quadrant as good as possible" — nonsmooth as written, but the standard epigraph trick makes it a
plain linear program our SLSQP handles:
<span class="frm">max_w  min_q  wᵀμ̂_q     ⇔     max_{w,z}  z   s.t.  wᵀμ̂_q ≥ z  ∀q,  Σw = 1,  0 ≤ w ≤ cap</span>
Why aim at the floor and not the ceiling: Ang &amp; Bekaert showed regime-aware allocation adds
value out of sample mostly by <i>cutting exposure to the bad regime</i> — correlations spike in
bear states, so diversification fails exactly when needed. Caveat printed with the method: our
regime call is right ~52–57% at 3 months (measured), so quadrant bets are tilts, never certainty.
<ul class="src">
<li>Ang &amp; Bekaert (2002 <i>RFS</i>; 2004 <i>FAJ</i>) — regime shifts and asset allocation</li>
<li>Bridgewater, "The All Weather Story" — the same growth×inflation quadrant map, in production since 1996</li>
<li>Survey: Ang &amp; Timmermann, "Regime Changes and Financial Markets" — <a href="https://www.nber.org/system/files/working_papers/w17182/w17182.pdf">NBER w17182</a></li>
<li>Repo deep dive: <span class="num">regime-switching.md</span> · code: <span class="num">portfolio/optimizer.py::_solve_maximin</span>, <span class="num">analytics/macro_state.py</span></li>
</ul></div></details>
<div id="quad" class="chart" style="height:420px"></div>
</div>

<h2>5 · What the views changed — Π vs μ_BL</h2>
<p class="cap">Π (hollow) is what the neutral ERC anchor implies each sleeve should return —
say nothing and this is all the optimizer believes. μ_BL (solid) is after the regime views tilt
it, <b>each view weighted by the Markov outlook's own confidence</b><span id="conf"></span>.
The gaps are the entire effect of opinions: small, proportional, auditable. Raw historical
means never enter.</p>
<details class="more"><summary>Method, math &amp; sources</summary><div class="body">
Black-Litterman replaces the poisonous raw μ̂ in two moves. First, <b>reverse-optimize the
anchor</b>: instead of estimating returns and deriving weights, take the defensible neutral
portfolio (ERC) and derive the returns that would make it optimal —
<span class="frm">Π = δ·Σ·w₀          δ calibrated so w₀ᵀΠ = the anchor's own historical mean return</span>
Say nothing, and the optimizer hands back exactly w₀. Second, <b>update Bayesianly with views</b>
(ours: factor-vs-Reference tilts, Q = outlook-weighted per-quadrant excess, confidence c = the
Markov outlook's probability mass, capped at 0.95):
<span class="frm">μ_BL = [ (τΣ)⁻¹ + PᵀΩ⁻¹P ]⁻¹ · [ (τΣ)⁻¹Π + PᵀΩ⁻¹Q ]      τ = 1/T,   Ω_kk = (τ·PΣPᵀ)_kk / c_k</span>
Low confidence ⇒ big Ω ⇒ the view barely moves anything; that is why the dots barely separate.
The whole update is what this chart shows — auditable, no hidden conviction. In production at
Goldman Sachs since ~1990; the standard anchor at sovereign funds and endowments.
<ul class="src">
<li>Black &amp; Litterman (1992), "Global Portfolio Optimization" — <i>FAJ</i> 48(5)</li>
<li>He &amp; Litterman (1999), "The Intuition Behind Black-Litterman" — <a href="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=334304">Goldman Sachs / SSRN</a></li>
<li>Idzorek (2005) — confidence-based Ω, the convention behind our c_k</li>
<li>Repo deep dive: <span class="num">black-litterman.md</span> · code: <span class="num">portfolio/views.py</span></li>
</ul></div></details>
<div id="blchart" class="chart" style="height:520px"></div>

<h2>6 · Where the money sits vs where the risk sits</h2>
<p class="cap">For each recommended portfolio: capital weight (pale) next to the Euler risk
contribution (solid) — the share of portfolio volatility each sleeve is actually responsible
for. <b>They are never the same thing</b>; the risk bar is the honest one.</p>
<details class="more"><summary>Method, math &amp; sources</summary><div class="body">
Portfolio volatility σ_p = √(wᵀΣw) is homogeneous of degree 1 in the weights, so Euler's theorem
splits it <i>exactly</i> — no approximation — into one additive slice per sleeve:
<span class="frm">RC_i = w_i·(Σw)_i / σ_p          Σ_i RC_i = σ_p   (identity, unit-tested)</span>
Dollars diversify badly because risk concentrates: the classic example is 60/40
stocks/bonds being ~90/10 in <i>risk</i>. Our ERC anchor is defined as the portfolio where all
RC_i are equal — long-only it exists and is unique, and its volatility provably sits between
min-variance and 1/N (σ_minvar ≤ σ_ERC ≤ σ_1/N). When a recommendation's risk bars are much more
concentrated than its weight bars, the portfolio is secretly a bet on its most volatile sleeves —
which is exactly what this chart is here to expose.
<ul class="src">
<li>Maillard, Roncalli &amp; Teïletche (2010), "The Properties of Equally Weighted Risk Contribution Portfolios" — <i>JPM</i> 36(4)</li>
<li>Asness, Frazzini &amp; Pedersen (2012), "Leverage Aversion and Risk Parity" — <a href="https://pages.stern.nyu.edu/~afrazzin/pdf/Leverage%20Aversion%20and%20Risk%20Parity%20-%20Asness%20,%20Frazzini%20and%20Pedersen.pdf">FAJ 68(1)</a></li>
<li>Repo deep dive: <span class="num">risk-parity-erc.md</span> · code: <span class="num">portfolio/anchors.py::risk_contributions</span></li>
</ul></div></details>
<div id="wrc"></div>

<div id="conesec">
<h2>7 · Scenario cones (validator, not objective)</h2>
<p class="cap">Each portfolio run through 2,000 regime-persistent bootstrap futures starting
from today's actual quadrant (10y horizon). Boxes span p25–p75, whiskers p5–p95, the tick is
the median. <b>Wide cones are the honest admission of uncertainty</b> — the assumption
("future = re-sequenced 1997–2026") is stated, not hidden.</p>
<details class="more"><summary>Method, math &amp; sources</summary><div class="body">
Each simulated future is built in <b>regime spells</b>, not shuffled months: the path starts in
today's actual quadrant, each spell's length is geometric from that state's measured persistence
(<code>duration ~ Geometric(1 − p_stay)</code>, expected ≈ 4–6 months), the next state follows
the empirical transition matrix, and months inside a spell are contiguous blocks of real history
from that state — always whole cross-sections, so real cross-series correlation survives. This
is a state-conditioned <b>stationary bootstrap</b>: the geometric block lengths are
Politis-Romano's, with regime structure layered on top. Boundaries, stated plainly: a bootstrap
cannot invent dynamics history never contained, and the transitions are counted, not fitted
(the honest cousin of Hamilton's regime-switching models, kept deliberately on the
descriptive-statistics side of the FRED terms-of-use line). Why validate here instead of
optimizing on the simulation: optimizing through the Monte Carlo would overfit its noise —
judging through it costs nothing and flags fragile portfolios.
<ul class="src">
<li>Politis &amp; Romano (1994), "The Stationary Bootstrap" — <i>JASA</i> 89(428)</li>
<li>Hamilton (1989) — <i>Econometrica</i>; the regime-switching lineage our counted matrix descends from</li>
<li>Repo deep dive: <span class="num">stationary-bootstrap.md</span> · code: <span class="num">analytics/scenario.py::portfolio_cone</span></li>
</ul></div></details>
<div id="cones" class="chart" style="height:400px"></div>
</div>

<hr><p class="cap">Companions: <span class="num">REPORT_optimizer.md</span> (numbers),
<span class="num">info/portfolio_optimization.md</span> (method),
<span class="num">info/literature.md</span> (evidence). Charts need internet once for the
Plotly CDN.</p>

<script>
const DATA = __DATA__;
const INK='#1D1D1F', MUT='#6E6E73', LINE='#E3E3E8';
const PCOLOR={'1/N':'#8E8E93','ERC (anchor)':'#3B6FD4','HRP':'#7A5FD0','Min-variance':'#2E9E68',
  'Balanced sliders (5/5/5)':'#E08A00','Maximin (worst quadrant)':'#C94F4F'};
function pc(n){ if(PCOLOR[n]) return PCOLOR[n];
  if(n.startsWith('Maximin (geo')) return '#1F8A99';
  if(n.startsWith('Momentum')) return '#B5892E';
  if(n.indexOf('vol-target')>=0) return '#5AA6B5';
  return '#E08A00'; }
const L=o=>Object.assign({paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',
  font:{family:'Instrument Sans, sans-serif',color:INK,size:12.5},
  margin:{l:60,r:20,t:10,b:45},xaxis:{gridcolor:LINE,zerolinecolor:LINE},
  yaxis:{gridcolor:LINE,zerolinecolor:LINE},legend:{orientation:'h',y:1.12}},o);
const CFG={displayModeBar:false,responsive:true};
document.getElementById('win').textContent=DATA.window+'  ('+DATA.T+'m × '+DATA.n+' series)';
document.getElementById('dstar').textContent=DATA.delta_star;

// roster holdings — the actual sleeves+weights each strategy lands on
document.querySelectorAll('.roster .rp[data-port]').forEach(rp=>{
 const rw=DATA.roster_weights[rp.dataset.port], el=rp.querySelector('.holds');
 if(!rw||!el||!rw.holdings.length) return;
 const col=pc(rp.dataset.port), h=rw.holdings, mx=h[0][1];
 const equal=h.length===rw.n_total && (h[0][1]-h[h.length-1][1] < 0.001);
 let html='<div class="htitle">Holdings — what it actually buys</div>';
 if(equal){el.innerHTML=html+'<div class="hmore">All '+rw.n_total+
   ' sleeves held equally at '+(h[0][1]*100).toFixed(1)+'% each.</div>'+geoLine(rw);return;}
 h.slice(0,8).forEach(([s,w])=>{html+='<div class="hbar"><span class="hlab" title="'+s+'">'+s+
   '</span><span class="htrk"><span class="hfill" style="width:'+(w/mx*100).toFixed(0)+
   '%;background:'+col+'"></span></span><span class="hpct">'+(w*100).toFixed(1)+'%</span></div>';});
 const rest=rw.n_total-Math.min(8,h.length);
 if(rest>0){const rw2=h.slice(8).reduce((a,b)=>a+b[1],0);
   html+='<div class="hmore">+ '+rest+' more sleeve'+(rest>1?'s':'')+
   ' ('+(rw2*100).toFixed(0)+'% combined, each &lt; '+(h[8][1]*100).toFixed(1)+'%)</div>';}
 html+=geoLine(rw);
 el.innerHTML=html;
});
function geoLine(rw){ if(!rw.geo) return '';
 return '<div class="hmore">Look-through geography: '+Object.entries(rw.geo)
   .filter(([,v])=>v>=0.005).map(([z,v])=>z+' '+(v*100).toFixed(0)+'%').join(' · ')+'</div>';}

// 1 race
Plotly.newPlot('race',Object.keys(DATA.wf.growth).map(n=>({x:DATA.wf.dates,y:DATA.wf.growth[n],
  name:n,mode:'lines',line:{width:n==='1/N'?3:1.7,color:pc(n),dash:n==='1/N'?'solid':undefined}})),
  L({yaxis:{title:'growth of 100 (OOS months only)',gridcolor:LINE,type:'log'}}),CFG);

// 2 scoreboard
const S=DATA.wf.summary;
Plotly.newPlot('board',[
 {y:S.map(r=>r.portfolio),x:S.map(r=>r.oos_sharpe_rf0),name:'OOS Sharpe',type:'bar',
  orientation:'h',marker:{color:S.map(r=>pc(r.portfolio))},
  text:S.map(r=>r.oos_sharpe_rf0.toFixed(2)),textposition:'outside',
  hovertemplate:'%{y}<br>Sharpe %{x:.2f}<br>CAGR '+'%{customdata[0]:.1%}<br>maxDD %{customdata[1]:.1%}<br>turnover/refit %{customdata[2]:.1%}<extra></extra>',
  customdata:S.map(r=>[r.oos_CAGR,r.oos_max_drawdown,r.mean_turnover_per_refit])}],
 L({xaxis:{title:'out-of-sample Sharpe (rf=0)',gridcolor:LINE,range:[0,Math.max(...S.map(r=>r.oos_sharpe_rf0))*1.18]},
    yaxis:{automargin:true,autorange:'reversed'},margin:{l:200,r:20,t:10,b:45},showlegend:false}),CFG);

// 3 map
Plotly.newPlot('map',[
 {x:DATA.sleeves.map(s=>s.vol),y:DATA.sleeves.map(s=>s.cagr),mode:'markers',name:'individual sleeves',
  text:DATA.sleeves.map(s=>s.name),marker:{color:'#B9B9C0',size:7,opacity:.75},
  hovertemplate:'%{text}<br>vol %{x:.1%} · CAGR %{y:.1%}<extra></extra>'},
 ...DATA.portfolios.map(p=>({x:[p.vol],y:[p.cagr],mode:'markers+text',name:p.name,
  text:[p.name],textposition:'top center',textfont:{size:11},
  marker:{color:pc(p.name),size:13,symbol:'diamond',line:{color:'#fff',width:1.5}},
  hovertemplate:p.name+'<br>vol %{x:.1%} · CAGR %{y:.1%}<extra></extra>'}))],
 L({xaxis:{title:'annualized volatility',tickformat:'.0%',gridcolor:LINE},
    yaxis:{title:'CAGR (full window)',tickformat:'.0%',gridcolor:LINE},showlegend:false}),CFG);

// 4 quadrants
if(DATA.quad){
 Plotly.newPlot('quad',Object.entries(DATA.quad.portfolios).map(([n,vals])=>({
   x:DATA.quad.states,y:vals,name:n,type:'bar',marker:{color:pc(n)}})),
  L({barmode:'group',yaxis:{title:'annualized return in that quadrant',tickformat:'.0%',gridcolor:LINE}}),CFG);
}else{document.getElementById('quadsec').style.display='none'}

// 5 BL tilt
const order=[...DATA.bl.series.keys()].sort((a,b)=>DATA.bl.mu_bl[b]-DATA.bl.mu_bl[a]);
Plotly.newPlot('blchart',[
 {y:order.map(i=>DATA.bl.series[i]),x:order.map(i=>DATA.bl.pi[i]),name:'Π (anchor-implied)',
  mode:'markers',marker:{symbol:'circle-open',size:9,color:MUT,line:{width:2}},
  hovertemplate:'%{y}<br>Π %{x:.1%}<extra></extra>'},
 {y:order.map(i=>DATA.bl.series[i]),x:order.map(i=>DATA.bl.mu_bl[i]),name:'μ_BL (after views)',
  mode:'markers',marker:{size:9,color:'#E08A00'},
  hovertemplate:'%{y}<br>μ_BL %{x:.1%}<extra></extra>'}],
 L({xaxis:{title:'implied annual return',tickformat:'.0%',gridcolor:LINE},
    yaxis:{automargin:true,autorange:'reversed'},margin:{l:230,r:20,t:10,b:45}}),CFG);
if(DATA.bl.views.length){document.getElementById('conf').textContent=
 ' (currently '+Math.round(DATA.bl.views[0].confidence*100)+'%)';}

// 6 weights vs RC — one small grouped chart per portfolio
const wrcRoot=document.getElementById('wrc');
Object.entries(DATA.wrc).forEach(([n,d])=>{
 const h=document.createElement('p');h.innerHTML='<b>'+n+'</b>';h.style.margin='14px 0 6px';
 const div=document.createElement('div');div.className='chart';
 div.style.height=Math.max(180,60+d.series.length*34)+'px';
 wrcRoot.appendChild(h);wrcRoot.appendChild(div);
 Plotly.newPlot(div,[
  {y:d.series,x:d.weight,name:'capital weight',type:'bar',orientation:'h',
   marker:{color:pc(n),opacity:.4},hovertemplate:'%{y}<br>weight %{x:.1%}<extra></extra>'},
  {y:d.series,x:d.rc_share,name:'risk contribution share',type:'bar',orientation:'h',
   marker:{color:pc(n)},hovertemplate:'%{y}<br>risk share %{x:.0%}<extra></extra>'}],
  L({barmode:'group',xaxis:{tickformat:'.0%',gridcolor:LINE},
     yaxis:{automargin:true},margin:{l:220,r:20,t:10,b:30}}),CFG);
});

// 7 cones
if(DATA.cones.length){
 const cs=DATA.cones;
 Plotly.newPlot('cones',[{type:'box',orientation:'h',
   y:cs.map(c=>c.name),q1:cs.map(c=>c.cagr_p25),median:cs.map(c=>c.cagr_p50),
   q3:cs.map(c=>c.cagr_p75),lowerfence:cs.map(c=>c.cagr_p5),upperfence:cs.map(c=>c.cagr_p95),
   marker:{color:'#3B6FD4'},fillcolor:'rgba(59,111,212,.15)',line:{width:1.6},
   hovertemplate:'%{y}<br>p5 %{lowerfence:.1%} · p50 %{median:.1%} · p95 %{upperfence:.1%}<extra></extra>'}],
  L({xaxis:{title:'simulated 10y CAGR (current_conditions)',tickformat:'.0%',gridcolor:LINE},
     yaxis:{automargin:true,autorange:'reversed'},margin:{l:200,r:20,t:10,b:45},showlegend:false}),CFG);
 }else{document.getElementById('conesec').style.display='none'}
</script></body></html>
"""


def run():
    C.ensure_dirs()
    data = build_data()
    html = (TEMPLATE.replace("__DATA__", json.dumps(data))
                    .replace("__DSTAR__", f"{data['delta_star']:.3f}"))
    C.OPTIMIZER_VIZ.write_text(html)
    print(f"[visualize] wrote {C.OPTIMIZER_VIZ} ({C.OPTIMIZER_VIZ.stat().st_size // 1024} KB) "
          f"— open it in a browser")
    return C.OPTIMIZER_VIZ


if __name__ == "__main__":
    run()
