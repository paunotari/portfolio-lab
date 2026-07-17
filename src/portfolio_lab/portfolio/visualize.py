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
        div_kw = dict(cap=C.OPTIMIZER_DIVERSIFIED_SLEEVE_CAP_PCT / 100.0,
                      geo_cap=C.OPTIMIZER_GEO_CAP_PCT / 100.0,
                      factor_cap=C.OPTIMIZER_FACTOR_CAP_PCT / 100.0)
        portfolios["Maximin (worst quadrant)"] = opt.optimize(maximin=True, inputs=inp)
        portfolios["Maximin (diversified)"] = opt.optimize(maximin=True, inputs=inp, **div_kw)
        if C.ASSET_CLASS_MONTHLY.exists():       # the all-weather opt-in (equity-only default)
            try:
                inp_aw = opt.build_inputs(include_asset_classes=True)
                if inp_aw["mu_q"] is not None:
                    portfolios["Maximin (all-weather: +bonds/gold/cash)"] = opt.optimize(
                        maximin=True, inputs=inp_aw, **div_kw)
            except Exception as e:
                print(f"[visualize] WARN all-weather skipped ({e})")

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

    # 4. per-quadrant annualized returns for 1/N vs the flagships (each portfolio's numbers come
    # from ITS OWN universe — the all-weather one includes the proxy sleeves)
    quad = None
    if have_macro:
        mu_q = inp["mu_q"]
        states = list(mu_q.index)
        qports = {name: [_ann(float(w @ mu_q.loc[s].values)) for s in states]
                  for name, w in (("1/N", inp["anchors"]["1/N"]),
                                  ("ERC (anchor)", inp["anchors"]["ERC (anchor)"]))}
        for name, res in portfolios.items():
            qports[name] = [_ann(res["per_quadrant_monthly"][s]) for s in states]
        quad = dict(states=[_short(s) for s in states], portfolios=qports)

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
        cone_sets = {name: dict(zip(series, map(float, inp["anchors"][name])))
                     for name in ("1/N", "ERC (anchor)", "Min-variance")}
        cone_sets.update({name: dict(zip(res["all_series"], map(float, res["w"])))
                          for name, res in portfolios.items()})
        uni_ext = None
        for name, full_w in cone_sets.items():
            full_w = {s: v for s, v in full_w.items() if v > 0}
            u = uni
            if not set(full_w) <= set(uni["series"]):
                if uni_ext is None:
                    try:
                        uni_ext = build_universe(include_asset_classes=True)
                    except Exception:
                        uni_ext = {}
                if not (uni_ext and set(full_w) <= set(uni_ext["series"])):
                    continue
                u = uni_ext
            cones.append(dict(name=name, **{k: v for k, v in portfolio_cone(full_w, uni=u).items()
                                            if k not in ("scenario", "years")}))

    # roster holdings: the actual sleeves+weights each strategy lands on (grounds the formulas).
    # Anchors are vectors on the equity universe; flagships carry their own weights/geo dicts
    # (the all-weather one holds proxy sleeves the equity series list doesn't know).
    roster_weights = {}
    Z, zones = inp["geo_Z"], inp["geo_zones"]
    for name, w in inp["anchors"].items():
        pairs = sorted([[series[i].replace(" | ", " · "), round(float(w[i]), 4)]
                        for i in range(len(series)) if w[i] > 0.001], key=lambda kv: -kv[1])
        geo = {z: round(float(w @ Z[:, j]), 3) for j, z in enumerate(zones)}
        roster_weights[name] = dict(holdings=pairs, n_total=len(pairs), geo=geo)
    for name, res in portfolios.items():
        pairs = sorted([[s.replace(" | ", " · "), round(float(v), 4)]
                        for s, v in res["weights"].items()], key=lambda kv: -kv[1])
        roster_weights[name] = dict(holdings=pairs, n_total=len(pairs),
                                    geo={z: round(float(v), 3)
                                         for z, v in res["geo_exposure"].items()})

    # 8. long-history reality check (Fama-French factors x 66-year quadrant classification)
    longhist = None
    if C.FF_FACTORS_MONTHLY.exists():
        from portfolio_lab.analytics.long_history import build as lh_build, _agreement, FACTOR_LABEL
        st, freq, lmeta = lh_build()
        agree = _agreement(st)
        long_c = [c for c in agree.columns if c.startswith("long")][0]
        mod_c = [c for c in agree.columns if c.startswith("modern")][0]
        grid = [dict(state=_short(r.state), factor=r.factor, label=FACTOR_LABEL[r.factor],
                     long=float(r[long_c]), modern=float(r[mod_c]), agree=bool(r.signs_agree))
                for _, r in agree.iterrows()]
        # per-quadrant annualized return, modern vs long, for the two view-feeding factors
        def _by(fac):
            sub = st[st.factor == fac]
            states = [_short(s) for s in
                      ["Goldilocks (disinflationary growth)", "Reflation (overheating)",
                       "Stagflation (growth-inflation squeeze)", "Deflationary bust (recession/slowdown)"]]
            g = lambda samp: [float(sub[(sub.state.str.startswith(s.split()[0])) &
                              (sub['sample'].str.startswith(samp))].ann_return.iloc[0])
                              if len(sub[(sub.state.str.startswith(s.split()[0])) &
                                         (sub['sample'].str.startswith(samp))]) else None
                              for s in states]
            return dict(states=states, modern=g("modern"), long=g("long"))
        longhist = dict(meta=lmeta,
                        freq=dict(states=[_short(s) for s in freq.index],
                                  long=[int(freq.iloc[:, 0][s]) for s in freq.index],
                                  modern=[int(freq.iloc[:, 1][s]) for s in freq.index]),
                        hml=_by("hml"), mom=_by("mom"),
                        n_agree=int(agree.signs_agree.sum()), n_total=int(len(agree)),
                        flips=[f"{g['label']} in {g['state']}" for g in grid if not g["agree"]])

    # 9-12. phase-A research evidence (cached CSVs + a fresh profiles solve)
    phase_a = {}
    if C.PROXY_BACKTEST_SUMMARY.exists():
        phase_a["race"] = pd.read_csv(C.PROXY_BACKTEST_SUMMARY).round(4).to_dict("records")
    if C.PROXY_BACKTEST_DISPERSION.exists():
        dp = pd.read_csv(C.PROXY_BACKTEST_DISPERSION)
        agg = (dp.groupby(["race", "portfolio"]).oos_sharpe
               .agg(median="median", lo="min", hi="max").round(3).reset_index())
        one_n = dp[dp.portfolio == "1/N"].set_index(["race", "offset_months"]).oos_sharpe
        beats = (dp.set_index(["race", "offset_months"])
                 .assign(b=lambda d: d.oos_sharpe > one_n.reindex(d.index))
                 .groupby(["race", "portfolio"]).b.mean().round(2).rename("beats").reset_index())
        phase_a["dispersion"] = agg.merge(beats, on=["race", "portfolio"]).to_dict("records")
    if C.STRESS_SUMMARY.exists():
        phase_a["stress"] = pd.read_csv(C.STRESS_SUMMARY).round(4).to_dict("records")
    try:
        profs = opt.run_profiles(inp)
        phase_a["profiles"] = [
            dict(name=n, cagr=p["res"]["performance"]["CAGR"],
                 vol=p["res"]["performance"]["ann_vol"], sleeves=len(p["res"]["weights"]),
                 twin_cagr=p["twin"]["performance"]["CAGR"],
                 twin_vol=p["twin"]["performance"]["ann_vol"],
                 twin_sleeves=len(p["twin"]["weights"]), twin_label=p["twin_label"])
            for n, p in profs.items()]
    except Exception as e:
        print(f"[visualize] WARN profiles skipped ({e})")

    outlook = ({_short(k): round(float(v), 3) for k, v in inp["outlook"].items()}
               if inp["outlook"] else None)
    return dict(window=f"{rets.index[0].date()} → {rets.index[-1].date()}", T=inp["T"],
                n=len(series), delta_star=round(inp["delta_star"], 3), outlook=outlook,
                wf=wf, sleeves=sleeve_pts, portfolios=port_pts, quad=quad, bl=bl, wrc=wrc,
                cones=cones, roster_weights=roster_weights, longhist=longhist,
                phase_a=phase_a)


TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Optimizer — comparisons &amp; evidence</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Instrument+Sans:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@1,6..72,500;1,6..72,600&display=swap" rel="stylesheet">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root{--paper:#FBFBFD;--ink:#1D1D1F;--mut:#6E6E73;--line:#E3E3E8}
  body{background:var(--paper);color:var(--ink);margin:0;padding:0 22px 90px;
       font:15px/1.6 "Instrument Sans",-apple-system,Segoe UI,sans-serif;max-width:1060px;
       margin-inline:auto;-webkit-font-smoothing:antialiased}
  header{padding-top:42px}
  .wordmark{font:italic 600 21px/1 "Newsreader",Georgia,serif;letter-spacing:.01em;
    color:var(--ink);margin:0 0 18px}
  .wordmark em{font-style:italic;color:var(--mut)}
  h1{font-size:31px;font-weight:700;letter-spacing:-.022em;line-height:1.12;margin:0 0 10px}
  .ribbon{display:flex;height:3px;border-radius:2px;overflow:hidden;margin:16px 0 14px;
    max-width:820px}
  .ribbon span{flex:1}
  h2{font-size:20px;font-weight:650;letter-spacing:-.012em;margin:2px 0 4px}
  .eyebrow{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:11px;font-weight:500;
    letter-spacing:.14em;text-transform:uppercase;color:var(--mut);margin:58px 0 6px}
  .sub{color:var(--mut);font-size:14px;max-width:820px;margin:0 0 6px}
  .meta{font-size:12px;color:var(--mut);margin:0}
  .cap{color:var(--mut);font-size:13.5px;max-width:820px;margin:2px 0 12px}
  .cap b{color:var(--ink)}
  .chart{border:1px solid var(--line);border-radius:12px;background:#fff;padding:10px;
    box-shadow:0 1px 2px rgba(29,29,31,.04)}
  .num{font-family:"IBM Plex Mono",ui-monospace,monospace}
  hr{border:0;border-top:1px solid var(--line);margin:44px 0 20px}
  a:focus-visible,summary:focus-visible{outline:2px solid #3B6FD4;outline-offset:2px;border-radius:4px}
  details.more{max-width:820px;margin:0 0 14px;border:1px solid var(--line);border-radius:10px;
    background:#fff;font-size:13.5px;color:var(--mut);box-shadow:0 1px 2px rgba(29,29,31,.03)}
  details.more summary{cursor:pointer;padding:8px 14px;color:var(--mut);font-weight:500;
    font-size:11px;font-family:"IBM Plex Mono",ui-monospace,monospace;letter-spacing:.12em;
    text-transform:uppercase;list-style-position:inside}
  details.more summary:hover{color:var(--ink)}
  details.more[open] summary{border-bottom:1px solid var(--line);color:var(--ink)}
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
  .roster .rp{padding:10px 0 10px 12px;border-top:1px solid var(--line);
    border-left:3px solid transparent;margin-left:-12px}
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
<header>
<div class="wordmark">portfolio <em>lab</em></div>
<h1>Portfolio optimizer — comparisons &amp; evidence</h1>
<p class="sub">Every chart is a claim from <b>info/portfolio_optimization.md</b> made visible —
and judged on months it never saw. Label: <b>historically optimal under stated priorities —
not a forecast.</b></p>
<div class="ribbon" id="ribbon" aria-hidden="true"></div>
<p class="meta num">window <span id="win"></span> · shrinkage δ* <span id="dstar"></span> · returns net of costs · portfolio/visualize.py</p>
</header>

<details class="more intro"><summary>New here? Meet the portfolios these charts compare — principles, formulas &amp; papers</summary><div class="body">
<p>Every chart on this page pits the same allocation strategies against each other. Four are
established methods from the portfolio-construction literature; the ones marked ★ are ours,
built on top of that literature. The deepest thing separating them is <b>how much each one bets
on predicted returns</b> — the input the research says is the least trustworthy of all.</p>
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
<div class="rp" data-port="Maximin (diversified)"><span class="dot" style="background:#1F8A99"></span><b>★ Maximin, diversified — robust without the corner bets</b><br>
Unconstrained maximin is structurally concentrated: a linear objective lands on corners (3–4
sleeves, one factor, one region), betting on whichever per-quadrant history <i>looks</i> best —
noisy estimates, Michaud's trap per quadrant. This preset closes all three concentration axes
with hard caps: <b>sleeve ≤ 25%</b> (forces ≥ 4 holdings), <b>look-through geography ≤ 40%</b>
per zone, <b>factor bucket ≤ 40%</b> (no more all-Enhanced-Value). Within the caps the objective
still picks the best sleeves — spread by constraint, never filler.
<code>max_w min_q wᵀμ̂_q   s.t.  w ≤ 25%, wᵀZ_zone ≤ 40%, wᵀF_factor ≤ 40%</code><br>
<span class="p mut">Constraints as implicit shrinkage: Jagannathan &amp; Ma (2003), <i>JF</i> — and our own walk-forward: the capped maximin beat the unconstrained one out of sample. The honest trade-off, measured: on equities alone the stagflation floor nearly vanishes when you force spread (it WAS the concentrated Value bet); with bonds/gold in the menu it barely costs anything.</span>
<div class="holds"></div></div>
<div class="rp" data-port="Maximin (all-weather: +bonds/gold/cash)"><span class="dot" style="background:#8C6D1F"></span><b>★ Maximin, all-weather — the opt-in with bonds, gold &amp; cash</b><br>
The diversified preset (same three cap families) over a menu extended with three <b>non-equity
proxy sleeves</b> (10y Treasuries, gold, T-bills) — assets that structurally win where equities
lose: bonds in deflationary busts, gold in stagflation. The measured punchline: with real
diversifiers in the menu, <b>diversification is nearly free</b> — the worst-quadrant floor stays
close to the concentrated version's (+0.59 vs +0.73%/mo) at 11% volatility and −28% drawdown,
while on equities alone forcing the same spread erases the floor. <b>Equity-only remains the
product default</b> (the house thesis: equities are the productive asset); this is the profile
toggle for who wants the full all-weather.<br>
<span class="p mut">Bridgewater's All Weather (1996) made literal; bond returns constructed per Swinkels (2019), <i>Data</i> 4(3):91. Proxies, not investable sleeves — see the ETF-menu roadmap item.</span>
<div class="holds"></div></div>
</div>
<p class="key"><b>The pattern to watch across the charts:</b> the four methods that bet <i>least</i>
on predicted returns (1/N, min-variance, ERC, HRP) are exactly the ones that win out of sample —
the literature's core lesson that at ~27 years of data, humility about return forecasts beats
cleverness. Full canon + verdicts: <span class="num">info/literature.md</span> and the deep dives
in <span class="num">info/literature/</span>.</p>
</div></details>

<div class="eyebrow">Chart 01</div>
<h2>The walk-forward race (out of sample)</h2>
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

<div class="eyebrow">Chart 02</div>
<h2>Out-of-sample scoreboard</h2>
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

<div class="eyebrow">Chart 03</div>
<h2>The risk/return map</h2>
<p class="cap">Grey dots are the 21 individual sleeves over the full window; colored markers are
whole portfolios. <b>Diversified blends sit further left (less risk) than almost any single
sleeve at similar return</b> — that is the whole free lunch, and the different engines are just
different choices of where to sit on the cloud's edge.</p>
<p class="cap mut">From here on the charts show the <b>static portfolios</b> — allocations you
hold and can decompose (weights, risk, per-quadrant, scenarios). The two dynamic rule strategies
from the scoreboard (momentum, vol-target) have <i>no fixed weights</i> — they change holdings or
exposure every period — so they only have meaning in the walk-forward above and aren't plotted
here. Forcing a single point for them would mix time windows and mislead.</p>
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
<p style="margin-top:10px"><b>Why this chart's CAGR differs from the scoreboard's (chart 2).</b>
Same portfolio, two different measurements. Here every point is measured over the <b>full common
window (1999–2026)</b> with each portfolio's final weights held fixed — so it includes the
dot-com crash and 2008, when min-variance made just +0.2%/yr and drew down −41%. The scoreboard
instead measures only the <b>out-of-sample window (2009–2026)</b>, which skipped those bear
markets (they're the walk-forward's 10-year training warmup) and happened to be a strong bull
run. Concretely for min-variance: the exact same weights earn <b>9.2%/yr over 1999–2026</b> but
<b>14.7%/yr over just 2009–2026</b> — the ~6-point gap is almost entirely the window, not the
method (re-estimating yearly adds only ~0.4pt, to the 15.1% on the scoreboard). Neither number
lies: this map describes behaviour across all the history we have; the scoreboard tests only
unseen months — and honestly flags that those unseen months were an unusually kind era with no
prolonged bear market to survive out of sample.</p>
<ul class="src">
<li>Markowitz (1952), "Portfolio Selection" — <i>JF</i>; Nobel Prize 1990</li>
<li>Ledoit &amp; Wolf (2004), "Honey, I Shrunk the Sample Covariance Matrix" — <a href="http://www.ledoit.net/honey.pdf">JPM 30(4)</a></li>
<li>López de Prado (2016), "Building Diversified Portfolios that Outperform Out-of-Sample" — <a href="https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678">JPM 42(4)</a> (HRP)</li>
<li>Repo deep dives: <span class="num">ledoit-wolf-shrinkage.md</span>, <span class="num">hierarchical-risk-parity.md</span> · code: <span class="num">portfolio/shrinkage.py</span>, <span class="num">anchors.py</span></li>
</ul></div></details>
<div id="map" class="chart" style="height:480px"></div>

<div id="quadsec">
<div class="eyebrow">Chart 04</div>
<h2>Per-quadrant behaviour — the maximin story</h2>
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

<div class="eyebrow">Chart 05</div>
<h2>What the views changed — Π vs μ_BL</h2>
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

<div class="eyebrow">Chart 06</div>
<h2>Where the money sits vs where the risk sits</h2>
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
<div class="eyebrow">Chart 07</div>
<h2>Scenario cones (validator, not objective)</h2>
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

<div id="lhsec">
<div class="eyebrow">Appendix · the 66-year reality check</div>
<h2>Are our regime patterns real, or a 28-year mirage?</h2>
<p class="cap">The optimizer's regime views rest on how each factor behaves per macro quadrant —
measured on 1997–2026. Are those patterns structural, or luck of a short window? We re-ran the
same classifier over <b>Fama-French factor history back to 1960</b> (research proxies, not
investable sleeves) and compared. <b id="lhverdict"></b> Where an era agrees, the views now
shrink their estimate toward the century of data; where it flips, the modern reading is kept but
flagged as era-specific.</p>
<p class="cap mut" id="lhgain"></p>
<div id="lhval" class="chart" style="height:340px"></div>
<div style="height:10px"></div>
<div id="lhmom" class="chart" style="height:340px"></div>
<p class="cap" id="lhflip" style="margin-top:12px"></p>
<details class="more"><summary>Method, math &amp; sources</summary><div class="body">
The classifier's composite scores are computed on the full macro history, so extending the clip
back to 1960 (core PCE's start) changes <i>which</i> months are labelled, never a month's label.
Factors are Ken French's monthly research series (Mkt-RF / SMB / HML / Mom, free, not FRED). Each
quadrant's bar is the annualized return of that factor pooled over its months in that state.
Agreement = the long and modern samples share the sign of the factor's mean. Feeding it back:
the regime view's per-quadrant excess <code>d</code> blends by months of evidence,
<code>d = (n_mod·d_mod + n_long·β·f_long) / (n_mod + n_long)</code>, where β (OLS) maps the
long-short academic factor into long-only MSCI-sleeve-excess space — only in agreeing cells.
<ul class="src">
<li>Fama &amp; French (1993) · Jegadeesh &amp; Titman (1993, momentum) — the factors</li>
<li>Repo: <span class="num">ingest/ff_factors.py</span>, <span class="num">analytics/long_history.py</span>, <span class="num">portfolio/views.py::regime_views(long_prior=)</span> · report <span class="num">REPORT_long_history.md</span></li>
</ul></div></details>
</div>

<div id="pa1">
<div class="eyebrow">Evidence · the 90-year race</div>
<h2>Which construction rules survive nine decades?</h2>
<p class="cap">The same rules as chart 2, raced on the proxy universe: 6 long-only Fama-French
size×value portfolios (equity race, OOS <b>1936–2026</b>) and the same plus bonds/gold/cash
(multi-asset, OOS <b>1972–2026</b>, the real 1970s included; Sharpe measured over cash).
<b>Min-variance's modern win does not generalize</b> — over 90 years the structure rules
(HRP, ERC) match or edge 1/N and min-var trails. In multi-asset, risk balance (ERC) wins and
the diversified maximin beats 1/N through the real stagflation decade.</p>
<div id="parace" class="chart" style="height:420px"></div>
</div>

<div id="pa2">
<div class="eyebrow">Evidence · window robustness</div>
<h2>Does the winner depend on when you start looking?</h2>
<p class="cap">Each race re-run dropping the first 3/6/9 years of history. Dots are the median
OOS Sharpe across window variants, whiskers span min→max; the label shows how often each rule
beats 1/N. <b>HRP and ERC beat 1/N in 100% of equity windows</b> — a finding, not an era
artifact. A rule whose whisker crosses the pack (min-variance) needed a particular era.</p>
<div id="padisp" class="chart" style="height:420px"></div>
</div>

<div id="pa3">
<div class="eyebrow">Evidence · a century of storms</div>
<h2>Named episodes: what would each shape have done?</h2>
<p class="cap">Constant-mix replay of hand-dated episodes. Top: static allocation ARCHETYPES on
the proxy universe — pure shapes, no optimizer estimates. The row that settles the all-weather
argument: <b>OPEC stagflation 1973-74, all-weather +9.8% while pure equity lost 44.6%</b>.
Bottom: today's recommended flagships through the modern storms (a stress replay, not a claim
we'd have held them then).</p>
<div id="pastress_h" class="chart" style="height:380px"></div>
<div style="height:10px"></div>
<div id="pastress_m" class="chart" style="height:380px"></div>
</div>

<div id="pa4">
<div class="eyebrow">Evidence · the price of preferences</div>
<h2>User profiles: what your guardrails cost — and buy</h2>
<p class="cap">Preferences are personal; their cost is measurable. Each profile (solid) is a
preference bundle under the diversified caps (sleeve ≤25%, geo ≤40%, factor ≤40%); its
unrestricted twin (pale) drops the caps. The gap is the price of the guardrails in CAGR — paid
in exchange for lower volatility and more spread. In-sample; note the same caps <b>improved</b>
out-of-sample results in every test we ran.</p>
<div id="paprof" class="chart" style="height:380px"></div>
</div>

<hr><p class="cap">Companions: <span class="num">REPORT_optimizer.md</span> (numbers),
<span class="num">REPORT_proxy_backtest.md</span> + <span class="num">REPORT_window_robustness.md</span>
(the 90-year race), <span class="num">REPORT_stress.md</span> (episodes),
<span class="num">REPORT_long_history.md</span> (the 66-year study),
<span class="num">info/portfolio_optimization.md</span> (method),
<span class="num">info/literature.md</span> (evidence). Charts need internet once for the
Plotly CDN.</p>

<script>
const DATA = __DATA__;
const INK='#1D1D1F', MUT='#6E6E73', LINE='#E3E3E8';
const PCOLOR={'1/N':'#8E8E93','ERC (anchor)':'#3B6FD4','ERC':'#3B6FD4','HRP':'#7A5FD0',
  'Min-variance':'#2E9E68','Balanced sliders (5/5/5)':'#E08A00',
  'Maximin (worst quadrant)':'#C94F4F','Maximin (unconstrained)':'#C94F4F',
  'Maximin (sleeve ≤25%)':'#1F8A99'};
function pc(n){ if(PCOLOR[n]) return PCOLOR[n];
  if(n.startsWith('Maximin (geo')||n.startsWith('Maximin (diversified')) return '#1F8A99';
  if(n.startsWith('Maximin (all-weather')) return '#8C6D1F';
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
const rb=document.getElementById('ribbon');
['1/N','Min-variance','ERC (anchor)','HRP','Balanced sliders (5/5/5)','Maximin (worst quadrant)','Maximin (diversified)','Maximin (all-weather: +bonds/gold/cash)']
 .forEach(n=>{const sp=document.createElement('span');sp.style.background=pc(n);rb.appendChild(sp);});
document.querySelectorAll('.roster .rp[data-port]').forEach(rp=>{rp.style.borderLeftColor=pc(rp.dataset.port);});

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

// 8 long-history reality check
if(DATA.longhist){
 const lh=DATA.longhist, m=lh.meta;
 document.getElementById('lhverdict').textContent=
   lh.n_agree+' of '+lh.n_total+' factor×quadrant patterns hold across both eras.';
 document.getElementById('lhgain').innerHTML='The long sample classifies <b>'+m.long_months+
   ' months</b> ('+m.long_start+'→'+m.long_end+') vs '+m.modern_months+
   ' modern — roughly ×'+(m.long_months/m.modern_months).toFixed(1)+
   ' more history per quadrant, finally including the real 1970s stagflation.';
 const bars=(id,d,title)=>Plotly.newPlot(id,[
   {x:d.states,y:d.modern.map(v=>v==null?null:v),name:'modern (1997–2026)',type:'bar',
    marker:{color:'#C9C9D2'}},
   {x:d.states,y:d.long.map(v=>v==null?null:v),name:'long (66 years)',type:'bar',
    marker:{color:'#3B6FD4'}}],
   L({barmode:'group',title:{text:title,font:{size:13},x:0,xanchor:'left'},
      yaxis:{title:'annualized return',tickformat:'.0%',gridcolor:LINE},
      margin:{l:60,r:20,t:34,b:40}}),CFG);
 bars('lhval',lh.hml,'Value (HML) per quadrant — does the premium survive 66 years?');
 bars('lhmom',lh.mom,'Momentum (Mom) per quadrant — same test');
 document.getElementById('lhflip').innerHTML= lh.flips.length
   ? '<b>The one flip:</b> '+lh.flips.join(', ')+'. The modern "equities always crash in '+
     'stagflation" reading is a 2021–22 artifact — over 66 years the market factor was roughly '+
     'flat in stagflation, not catastrophic. Exactly the cell a 28-year window would overfit, '+
     'so the views keep it modern-only and say so.'
   : 'Every modern per-quadrant sign survived the long sample.';
}else{document.getElementById('lhsec').style.display='none'}

// 9-12 phase-A research evidence
const PA=DATA.phase_a||{};
const hideIf=(cond,id)=>{if(cond)document.getElementById(id).style.display='none';};
// 9 the 90-year race
if(PA.race){
 const races=[...new Set(PA.race.map(r=>r.race))];
 Plotly.newPlot('parace',races.map(rc=>{
   const sub=PA.race.filter(r=>r.race===rc);
   return {y:sub.map(r=>r.portfolio),x:sub.map(r=>r.oos_sharpe),name:rc.replace('_',' '),
     type:'bar',orientation:'h',marker:{color:sub.map(r=>pc(r.portfolio)),
     opacity:rc==='equity'?1:.55},
     hovertemplate:'%{y} ('+rc+')<br>Sharpe %{x:.2f}<extra></extra>'};}),
  L({barmode:'group',xaxis:{title:'OOS Sharpe (equity: rf=0 · multi-asset: over cash)',gridcolor:LINE},
     yaxis:{automargin:true,autorange:'reversed'},margin:{l:190,r:20,t:10,b:45}}),CFG);
}else hideIf(true,'pa1');
// 10 window robustness
if(PA.dispersion){
 const races=[...new Set(PA.dispersion.map(r=>r.race))];
 const traces=[];
 races.forEach((rc,i)=>{const sub=PA.dispersion.filter(r=>r.race===rc);
  traces.push({y:sub.map(r=>r.portfolio+(i?'  ·M':'  ·E')),x:sub.map(r=>r.median),
   mode:'markers+text',name:rc.replace('_',' '),
   text:sub.map(r=>' beats 1/N '+Math.round(r.beats*100)+'%'),textposition:'middle right',
   textfont:{size:10.5,color:MUT},
   error_x:{type:'data',symmetric:false,array:sub.map(r=>r.hi-r.median),
            arrayminus:sub.map(r=>r.median-r.lo),color:'#B9B9C0'},
   marker:{size:10,color:sub.map(r=>pc(r.portfolio))}});});
 Plotly.newPlot('padisp',traces,
  L({xaxis:{title:'OOS Sharpe across window variants (median, min→max)',gridcolor:LINE},
     yaxis:{automargin:true,autorange:'reversed'},margin:{l:210,r:110,t:10,b:45},showlegend:false}),CFG);
}else hideIf(true,'pa2');
// 11 stress episodes
if(PA.stress){
 const ACOL={'Pure equity (1/N of 6)':'#8E8E93','60/40 stocks/bonds':'#3B6FD4','All-weather static':'#8C6D1F'};
 const hist=PA.stress.filter(r=>r.table==='historic');
 const eps=[...new Set(hist.map(r=>r.episode))];
 Plotly.newPlot('pastress_h',Object.keys(ACOL).map(a=>({x:eps,
   y:eps.map(e=>{const m=hist.find(r=>r.episode===e&&r.portfolio===a);return m?m.cum_return:null;}),
   name:a,type:'bar',marker:{color:ACOL[a]}})),
  L({barmode:'group',title:{text:'Static archetypes — a century of storms',font:{size:13},x:0},
     yaxis:{title:'cumulative return in episode',tickformat:'.0%',gridcolor:LINE},margin:{l:60,r:20,t:34,b:60}}),CFG);
 const mod=PA.stress.filter(r=>r.table==='modern');
 const want=['1/N','Min-variance','Balanced sliders (5/5/5)','Maximin (diversified)','Maximin (all-weather)'];
 const ports=want.filter(p=>mod.some(r=>r.portfolio===p));
 const meps=[...new Set(mod.map(r=>r.episode))];
 Plotly.newPlot('pastress_m',ports.map(p=>({x:meps,
   y:meps.map(e=>{const m=mod.find(r=>r.episode===e&&r.portfolio===p);return m?m.cum_return:null;}),
   name:p,type:'bar',marker:{color:pc(p)}})),
  L({barmode:'group',title:{text:"Today's flagships — modern storms (stress replay)",font:{size:13},x:0},
     yaxis:{title:'cumulative return in episode',tickformat:'.0%',gridcolor:LINE},margin:{l:60,r:20,t:34,b:60}}),CFG);
}else{hideIf(true,'pa3');}
// 12 profiles: price of preferences
if(PA.profiles&&PA.profiles.length){
 const ps=PA.profiles;
 Plotly.newPlot('paprof',[
  {x:ps.map(p=>p.name),y:ps.map(p=>p.cagr),name:'profile (capped)',type:'bar',
   marker:{color:'#3B6FD4'},text:ps.map(p=>p.sleeves+' sleeves'),textposition:'outside',
   hovertemplate:'%{x}<br>CAGR %{y:.2%} · vol %{customdata:.1%}<extra>profile</extra>',
   customdata:ps.map(p=>p.vol)},
  {x:ps.map(p=>p.name),y:ps.map(p=>p.twin_cagr),name:'unrestricted twin',type:'bar',
   marker:{color:'#3B6FD4',opacity:.35},text:ps.map(p=>p.twin_sleeves+' sleeves'),
   textposition:'outside',
   hovertemplate:'%{x}<br>CAGR %{y:.2%} · vol %{customdata:.1%}<extra>twin</extra>',
   customdata:ps.map(p=>p.twin_vol)}],
  L({barmode:'group',yaxis:{title:'historical CAGR (common window)',tickformat:'.0%',gridcolor:LINE},
     xaxis:{automargin:true},margin:{l:60,r:20,t:10,b:70}}),CFG);
}else hideIf(true,'pa4');
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
