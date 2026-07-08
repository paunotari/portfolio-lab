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

    outlook = ({_short(k): round(float(v), 3) for k, v in inp["outlook"].items()}
               if inp["outlook"] else None)
    return dict(window=f"{rets.index[0].date()} → {rets.index[-1].date()}", T=inp["T"],
                n=len(series), delta_star=round(inp["delta_star"], 3), outlook=outlook,
                wf=wf, sleeves=sleeve_pts, portfolios=port_pts, quad=quad, bl=bl, wrc=wrc,
                cones=cones)


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
</style></head><body>
<h1>Portfolio optimizer — comparisons &amp; evidence</h1>
<p class="sub">Common window <span class="num" id="win"></span> · covariance shrinkage
δ* <span class="num" id="dstar"></span> · generated by <span class="num">portfolio/visualize.py</span>.
Every chart is a claim from <b>info/portfolio_optimization.md</b> made visible.
Label: <b>historically optimal under stated priorities — not a forecast.</b></p>

<h2>1 · The walk-forward race (out of sample)</h2>
<p class="cap">Each contestant re-estimates everything on an expanding training window and is
judged only on months it never saw (annual refits). <b>This is the honesty test</b>: DeMiguel
(2009) says that at 330 months nothing should reliably beat equal weight — watch whether the
clever lines actually separate from <b>1/N</b>.</p>
<div id="race" class="chart" style="height:440px"></div>

<h2>2 · Out-of-sample scoreboard</h2>
<p class="cap">Same race as numbers. Sharpe is return per unit of risk — the fair lens.
<b>Min-variance winning is itself a literature result</b> (the most-constrained models do best
out of sample); the balanced slider blend not beating 1/N is the expected humility, printed
rather than hidden.</p>
<div id="board" class="chart" style="height:380px"></div>

<h2>3 · The risk/return map</h2>
<p class="cap">Grey dots are the 21 individual sleeves over the full window; colored markers are
whole portfolios. <b>Diversified blends sit further left (less risk) than almost any single
sleeve at similar return</b> — that is the whole free lunch, and the different engines are just
different choices of where to sit on the cloud's edge.</p>
<div id="map" class="chart" style="height:480px"></div>

<div id="quadsec">
<h2>4 · Per-quadrant behaviour — the maximin story</h2>
<p class="cap">Annualized return of each portfolio inside each macro quadrant's months.
<b>Maximin raises the worst bar (usually Stagflation) at the cost of the best bars</b> —
Ang-Bekaert's point that regime value comes from not being destroyed in the bad state,
All Weather's philosophy on our four quadrants.</p>
<div id="quad" class="chart" style="height:420px"></div>
</div>

<h2>5 · What the views changed — Π vs μ_BL</h2>
<p class="cap">Π (hollow) is what the neutral ERC anchor implies each sleeve should return —
say nothing and this is all the optimizer believes. μ_BL (solid) is after the regime views tilt
it, <b>each view weighted by the Markov outlook's own confidence</b><span id="conf"></span>.
The gaps are the entire effect of opinions: small, proportional, auditable. Raw historical
means never enter.</p>
<div id="blchart" class="chart" style="height:520px"></div>

<h2>6 · Where the money sits vs where the risk sits</h2>
<p class="cap">For each recommended portfolio: capital weight (pale) next to the Euler risk
contribution (solid) — the share of portfolio volatility each sleeve is actually responsible
for. <b>They are never the same thing</b>; the risk bar is the honest one.</p>
<div id="wrc"></div>

<div id="conesec">
<h2>7 · Scenario cones (validator, not objective)</h2>
<p class="cap">Each portfolio run through 2,000 regime-persistent bootstrap futures starting
from today's actual quadrant (10y horizon). Boxes span p25–p75, whiskers p5–p95, the tick is
the median. <b>Wide cones are the honest admission of uncertainty</b> — the assumption
("future = re-sequenced 1997–2026") is stated, not hidden.</p>
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
const pc=n=>PCOLOR[n]||'#E08A00';
const L=o=>Object.assign({paper_bgcolor:'rgba(0,0,0,0)',plot_bgcolor:'rgba(0,0,0,0)',
  font:{family:'Instrument Sans, sans-serif',color:INK,size:12.5},
  margin:{l:60,r:20,t:10,b:45},xaxis:{gridcolor:LINE,zerolinecolor:LINE},
  yaxis:{gridcolor:LINE,zerolinecolor:LINE},legend:{orientation:'h',y:1.12}},o);
const CFG={displayModeBar:false,responsive:true};
document.getElementById('win').textContent=DATA.window+'  ('+DATA.T+'m × '+DATA.n+' series)';
document.getElementById('dstar').textContent=DATA.delta_star;

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
    html = TEMPLATE.replace("__DATA__", json.dumps(data))
    C.OPTIMIZER_VIZ.write_text(html)
    print(f"[visualize] wrote {C.OPTIMIZER_VIZ} ({C.OPTIMIZER_VIZ.stat().st_size // 1024} KB) "
          f"— open it in a browser")
    return C.OPTIMIZER_VIZ


if __name__ == "__main__":
    run()
