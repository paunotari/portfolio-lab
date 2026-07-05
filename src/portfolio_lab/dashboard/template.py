"""Static HTML shell + browser JS for the dashboard (kept separate from build logic).

`__DATA__` is replaced with a JSON blob and `__JS__` with the JS string by dashboard.build.
"""

HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MSCI Factor / Region Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
:root{--bg:#0f1420;--panel:#171d2b;--ink:#e6ebf5;--mut:#8b97ad;--line:#26304a;
--acc:#5b9dff;--warn:#ff6b6b;--good:#39d98a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
header{padding:18px 24px;border-bottom:1px solid var(--line)}
h1{margin:0;font-size:18px;font-weight:650;letter-spacing:.2px}
.sub{color:var(--mut);font-size:12px;margin-top:3px}
nav{display:flex;gap:4px;padding:10px 20px;border-bottom:1px solid var(--line);flex-wrap:wrap}
nav button{background:transparent;color:var(--mut);border:1px solid transparent;
padding:8px 14px;border-radius:8px;cursor:pointer;font-size:13px}
nav button:hover{color:var(--ink)}nav button.on{background:var(--panel);color:var(--ink);
border-color:var(--line)}
main{padding:20px 24px;max-width:1200px}
.tab{display:none}.tab.on{display:block}
.card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:18px}
.grid{display:grid;gap:16px}.g2{grid-template-columns:1fr 1fr}@media(max-width:900px){.g2{grid-template-columns:1fr}}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{padding:6px 10px;border-bottom:1px solid var(--line);text-align:right}
th:first-child,td:first-child{text-align:left}th{color:var(--mut);cursor:pointer;user-select:none}
tr:hover td{background:#1c2436}
.warn{color:var(--warn);font-weight:600}.good{color:var(--good)}
h2{font-size:15px;margin:0 0 10px}h3{font-size:13px;color:var(--mut);margin:14px 0 6px;font-weight:600}
select,input{background:#0d1220;color:var(--ink);border:1px solid var(--line);border-radius:8px;padding:6px 8px}
.pill{display:inline-block;background:#0d1220;border:1px solid var(--line);border-radius:20px;
padding:2px 10px;margin:2px;font-size:12px}
.anno p{margin:4px 0}.anno b{color:var(--acc)}
.wrow{display:grid;grid-template-columns:1fr 90px;gap:8px;align-items:center;margin:4px 0}
.wrow label{font-size:12px;color:var(--mut)}
.metric{display:inline-block;margin-right:18px}.metric b{font-size:16px}
.muted{color:var(--mut);font-size:12px}
</style></head><body>
<header><h1>MSCI Factor / Region Dashboard</h1>
<div class="sub" id="sub"></div></header>
<nav id="nav"></nav>
<main>
 <section class="tab" id="t-perf">
   <div class="card">
     <h2>Date range</h2>
     <div class="muted">CAGR, volatility, Sharpe and max drawdown below are all computed over this
       single window — defaults to the common window (every index has data). Pick any range to
       compare performance over a specific period instead.</div>
     <div style="display:flex;gap:10px;align-items:center;margin-top:10px;flex-wrap:wrap">
       <label class="muted">From <input type="date" id="perfFrom"></label>
       <label class="muted">To <input type="date" id="perfTo"></label>
       <button onclick="resetPerfRange()">reset to common window</button>
       <span class="muted" id="perfRangeNote"></span>
     </div>
   </div>
   <div class="card"><h2>Risk / return</h2><div id="scatter" style="height:420px"></div>
     <div class="muted">Bubble size = max drawdown depth, over the selected date range.</div></div>
   <div class="card"><h2>Cumulative growth <span class="muted">(rebased to 100 at the start of the selected range, log scale)</span></h2>
     <div class="muted">Toggle series in the legend. Click a legend item to hide. Every line starts at 100 so the comparison is fair regardless of each index's own inception date.</div>
     <div id="cum" style="height:460px"></div></div>
   <div class="card"><h2>Performance table</h2><div id="perftbl"></div></div>
 </section>

 <section class="tab" id="t-fvr">
   <div class="card"><h2>Excess CAGR: factor minus its region reference</h2>
     <div class="muted">All 14 factor variants beat their reference over the full sample — bar = annualized excess.</div>
     <div id="fvrbar" style="height:460px"></div></div>
   <div class="card"><h2>Monthly win-rate vs reference</h2>
     <div id="fvrhit" style="height:380px"></div></div>
 </section>

 <section class="tab" id="t-reg">
   <div class="card"><h2>Regime explorer</h2>
     <select id="regsel"></select>
     <div class="anno" id="reganno" style="margin-top:12px"></div></div>
   <div class="card"><h2>Annualized return by index in this regime</h2><div id="regbar" style="height:520px"></div></div>
   <div class="card"><h2>Factor excess vs reference — all regimes (heatmap)</h2>
     <div class="muted">Green = factor beat its reference (annualized) in that regime; red = lagged.</div>
     <div id="regheat" style="height:420px"></div></div>
 </section>

 <section class="tab" id="t-corr">
   <div class="card"><h2>Correlation heatmap (monthly returns)</h2>
     <select id="corrsel"></select><div id="corrheat" style="height:640px"></div></div>
   <div class="card"><h2>Diversification over time</h2>
     <div class="muted">36-month rolling average pairwise correlation across the 7 regional references.
       High = crisis co-movement (diversification failing).</div>
     <div id="rollchart" style="height:340px"></div></div>
 </section>

 <section class="tab" id="t-macro">
   <div class="card"><h2>Macro indicator over time</h2>
     <select id="macrosel"></select>
     <div class="muted" id="macronote" style="margin-top:6px"></div>
     <div id="macrochart" style="height:380px"></div>
     <div class="muted">Shaded bands = macro regimes (see Regimes tab). Hover a band top label for the regime name.</div></div>
   <div class="card"><h2>Index ↔ macro correlation heatmap <span class="muted">(contemporaneous, monthly)</span></h2>
     <select id="macrobasis">
       <option value="chg">Δ change basis (sensitivity to surprises)</option>
       <option value="level">level basis (regime context — interpret with care)</option>
     </select>
     <div id="macroheat" style="height:560px"></div>
     <div class="muted">Blank cells = insufficient overlapping history (&lt;36 months).</div></div>
   <div class="card"><h2>Top macro drivers for one series</h2>
     <select id="macrodrvsel"></select>
     <div id="macrodrv" style="height:360px"></div></div>
 </section>

 <section class="tab" id="t-div">
   <div class="grid g2">
     <div class="card"><h2>Portfolio sleeves (weights, %)</h2>
       <div class="muted">Weights must sum to 100% — a portfolio can't hold more or less than
         itself. Set 0 to drop a sleeve.</div>
       <div id="winputs" style="margin-top:10px;max-height:420px;overflow:auto"></div>
       <div style="margin-top:10px;display:flex;align-items:center;gap:10px;flex-wrap:wrap">
        <button onclick="preset()">example preset</button>
        <button onclick="clearw()">clear</button>
        <span id="wtotal" class="pill"></span></div></div>
     <div class="card"><h2>Concentration summary</h2><div id="divsummary"></div></div>
   </div>
   <div class="card"><h2>Portfolio performance <span class="muted">(constant-mix blend, over the selected sleeves' overlapping history)</span></h2>
     <div id="divperf"></div></div>
   <div class="grid g2">
     <div class="card"><h2>Sector look-through</h2><div id="divsector" style="height:340px"></div></div>
     <div class="card"><h2>Country look-through</h2><div id="divcountry" style="height:340px"></div></div>
   </div>
   <div class="card"><h2>Single-stock look-through <span class="muted">(top-10 holdings only — lower bound)</span></h2>
     <div id="divstock" style="height:420px"></div></div>
 </section>
</main>
<script>const DATA=__DATA__;</script>
<script>__JS__</script>
</body></html>"""

JS = r"""
const $=s=>document.querySelector(s);
const pct=x=>x==null?'—':(x*100).toFixed(1)+'%';
const P={paper_bgcolor:'#171d2b',plot_bgcolor:'#171d2b',font:{color:'#e6ebf5',size:12},
  margin:{l:60,r:20,t:20,b:60},legend:{font:{size:11}}};
const FCOLOR={Reference:'#8b97ad',Momentum:'#5b9dff','Enhanced Value':'#f4a259',Quality:'#39d98a'};

// header
const allDates=DATA.levels.dates;
$('#sub').textContent=`${allDates[0]} → ${allDates[allDates.length-1]} · ${DATA.indices.length} indices · 7 regions × 4 factor types · monthly net USD`;

// nav/tabs
const TABS=[['perf','Performance'],['fvr','Factor vs Reference'],['reg','Regimes'],
  ['corr','Correlations'],['macro','Macro'],['div','Diversification']];
const nav=$('#nav');
TABS.forEach(([id,label],i)=>{const b=document.createElement('button');b.textContent=label;
  b.onclick=()=>show(id,b);if(i==0)b.classList.add('on');nav.appendChild(b);});
function show(id,btn){document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));
  $('#t-'+id).classList.add('on');document.querySelectorAll('nav button').forEach(x=>x.classList.remove('on'));
  btn.classList.add('on');window.dispatchEvent(new Event('resize'));}
$('#t-perf').classList.add('on');

// ---------- Performance (single CAGR, driven by a user-adjustable date range) ----------
// commonStart = earliest date where every series has data (mirrors engine.py's
// lv.dropna(how="any").index.min()); commonEnd = last date in the dataset.
const commonStart=(()=>{ const names=Object.keys(DATA.levels.series);
  for(const d of allDates){ if(names.every(n=>DATA.levels.series[n][allDates.indexOf(d)]!=null)) return d; }
  return allDates[0]; })();
const commonEnd=allDates[allDates.length-1];

// Shared stats formula (CAGR/vol/Sharpe/maxDD from a dense level array + its parallel dates
// array) — mirrors analytics/engine.py's _perf_stats. Used by both the Performance tab's
// date-range recompute AND the Diversification tab's blended-portfolio recompute, so there is
// exactly one JS implementation of this math to keep in sync with the Python one (see
// info/CLAUDE.md caveat on stats being computed in two places).
function computeSeriesStats(lv,dates){
  if(lv.length<2) return null;
  const n=lv.length-1;
  const cagr=Math.pow(lv[lv.length-1]/lv[0],12/n)-1;
  const rets=[]; for(let i=1;i<lv.length;i++) rets.push(lv[i]/lv[i-1]-1);
  const mean=rets.reduce((a,b)=>a+b,0)/rets.length;
  const variance=rets.reduce((a,b)=>a+(b-mean)*(b-mean),0)/(rets.length-1||1);
  const annVol=Math.sqrt(variance)*Math.sqrt(12);
  const sharpe=annVol?( (mean*12)/annVol ):null;
  let peak=-Infinity, maxDD=0;
  for(const v of lv){ peak=Math.max(peak,v); maxDD=Math.min(maxDD, v/peak-1); }
  return {CAGR:cagr, ann_vol:annVol, sharpe_rf0:sharpe, max_drawdown:maxDD,
          months:n, start:dates[0], end:dates[dates.length-1]};
}

function statsForRange(name,fromD,toD){
  const dates=allDates, vals=DATA.levels.series[name];
  const idx=[]; for(let i=0;i<dates.length;i++){ if(dates[i]>=fromD&&dates[i]<=toD&&vals[i]!=null) idx.push(i); }
  if(idx.length<2) return null;
  return computeSeriesStats(idx.map(i=>vals[i]), idx.map(i=>dates[i]));
}

const SERIES_META=DATA.perf.map(r=>({series:r.series,region:r.region,factor:r.factor}));
function computePerf(fromD,toD){
  return SERIES_META.map(row=>{
    const s=statsForRange(row.series,fromD,toD);
    return {...row, ...s, insufficient: s===null};
  });
}

let currentPerf=[], curSort='CAGR', curAsc=false;

// Rebase every series to 100 at its own first available point within [fromD,toD] — that's what
// makes the growth chart a FAIR comparison: a series with a strong 1997-98 doesn't start "ahead"
// just because the raw base-100 index level happened to already be higher by the range start.
function rebasedTraces(fromD,toD){
  const dates=allDates;
  let i0=dates.findIndex(d=>d>=fromD);
  if(i0<0) i0=0;
  let i1=dates.length-1;
  while(i1>i0 && dates[i1]>toD) i1--;
  const xs=dates.slice(i0,i1+1);
  return Object.keys(DATA.levels.series).map(name=>{
    const fac=name.split(' | ')[1];
    const raw=DATA.levels.series[name].slice(i0,i1+1);
    const baseIdx=raw.findIndex(v=>v!=null);
    const base=baseIdx<0?null:raw[baseIdx];
    const y=raw.map(v=>(v==null||base==null)?null:(v/base*100));
    return {x:xs,y,name,mode:'lines',connectgaps:false,
      line:{width:1.3,color:FCOLOR[fac]||'#5b9dff'},opacity:.85};
  });
}

function refreshPerf(fromD,toD){
  currentPerf=computePerf(fromD,toD);
  const ok=currentPerf.filter(r=>!r.insufficient);
  const nBad=currentPerf.length-ok.length;
  $('#perfRangeNote').textContent = nBad>0
    ? `${ok.length}/${currentPerf.length} series have >=2 data points in this range (${nBad} excluded).`
    : `${ok.length} series, common window default = ${commonStart} → ${commonEnd}.`;

  const x=ok.map(r=>r.ann_vol*100), y=ok.map(r=>r.CAGR*100);
  const size=ok.map(r=>8+Math.abs(r.max_drawdown)*40);
  const col=ok.map(r=>FCOLOR[r.factor]);
  const txt=ok.map(r=>`${r.series}<br>CAGR ${pct(r.CAGR)} · vol ${pct(r.ann_vol)}`
    +`<br>Sharpe ${r.sharpe_rf0==null?'—':r.sharpe_rf0.toFixed(2)} · maxDD ${pct(r.max_drawdown)}`);
  Plotly.react('scatter',[{x,y,text:txt,mode:'markers',type:'scatter',
    marker:{size,color:col,line:{color:'#0f1420',width:1}},hoverinfo:'text'}],
    {...P,xaxis:{title:'Annualized volatility %',gridcolor:'#26304a'},
     yaxis:{title:'CAGR %',gridcolor:'#26304a'}},{displayModeBar:false});

  Plotly.react('cum',rebasedTraces(fromD,toD),{...P,margin:{l:55,r:10,t:10,b:40},
    yaxis:{type:'log',gridcolor:'#26304a',title:'Growth of 100'},xaxis:{gridcolor:'#26304a'},
    legend:{orientation:'h',font:{size:9},y:-0.12}},{displayModeBar:false});

  perfTable(curSort,curAsc);
}

(function(){
  const from=$('#perfFrom'), to=$('#perfTo');
  from.value=commonStart; to.value=commonEnd;
  const onRangeChange=()=>refreshPerf(from.value,to.value);
  from.onchange=onRangeChange; to.onchange=onRangeChange;
  refreshPerf(commonStart,commonEnd);
})();

function resetPerfRange(){
  $('#perfFrom').value=commonStart; $('#perfTo').value=commonEnd;
  refreshPerf(commonStart,commonEnd);
}

function perfTable(sortKey,asc){
  curSort=sortKey; curAsc=asc;
  const rows=[...currentPerf].filter(r=>!r.insufficient)
    .sort((a,b)=>asc?a[sortKey]-b[sortKey]:b[sortKey]-a[sortKey]);
  const cols=[['series','Series'],['CAGR','CAGR'],['ann_vol','Ann vol'],
    ['sharpe_rf0','Sharpe'],['max_drawdown','Max DD']];
  let h='<table><thead><tr>'+cols.map(c=>`<th data-k="${c[0]}">${c[1]}</th>`).join('')+'</tr></thead><tbody>';
  rows.forEach(r=>{h+='<tr><td>'+r.series+'</td>'
    +`<td>${pct(r.CAGR)}</td><td>${pct(r.ann_vol)}</td><td>${r.sharpe_rf0==null?'—':r.sharpe_rf0.toFixed(2)}</td>`
    +`<td class="${r.max_drawdown<-0.55?'warn':''}">${pct(r.max_drawdown)}</td></tr>`;});
  h+='</tbody></table>';$('#perftbl').innerHTML=h;
  $('#perftbl').querySelectorAll('th').forEach(th=>th.onclick=()=>{
    const k=th.dataset.k;perfTable(k,k==='series'?true:(sortKey===k?!asc:false));});
}

// ---------- Factor vs Reference ----------
(function(){
  const facs=['Momentum','Enhanced Value','Quality'];
  const regions=[...new Set(DATA.fvr.map(r=>r.region))];
  const tr=facs.map(f=>({name:f,type:'bar',marker:{color:FCOLOR[f]},
    x:regions,y:regions.map(rg=>{const m=DATA.fvr.find(r=>r.region===rg&&r.factor===f);
      return m?+(m.excess_CAGR*100).toFixed(2):null;})}));
  Plotly.newPlot('fvrbar',tr,{...P,barmode:'group',yaxis:{title:'Excess CAGR (pp)',gridcolor:'#26304a'},
    xaxis:{gridcolor:'#26304a'}},{displayModeBar:false});
  const tr2=facs.map(f=>({name:f,type:'bar',marker:{color:FCOLOR[f]},
    x:regions,y:regions.map(rg=>{const m=DATA.fvr.find(r=>r.region===rg&&r.factor===f);
      return m?+(m.monthly_hit_rate*100).toFixed(1):null;})}));
  Plotly.newPlot('fvrhit',tr2,{...P,barmode:'group',
    yaxis:{title:'% months factor > reference',range:[45,62],gridcolor:'#26304a'},
    xaxis:{gridcolor:'#26304a'},shapes:[{type:'line',x0:-.5,x1:regions.length-.5,y0:50,y1:50,
      line:{color:'#8b97ad',dash:'dot',width:1}}]},{displayModeBar:false});
})();

// ---------- Regimes ----------
(function(){
  const sel=$('#regsel');
  DATA.regime_meta.forEach(r=>{const o=document.createElement('option');o.value=r.id;
    o.textContent=`${r.name}  (${r.start} → ${r.end})`;sel.appendChild(o);});
  sel.onchange=()=>drawRegime(sel.value);
  // heatmap: regime x series excess
  const series=[...new Set(DATA.regperf.filter(r=>r.factor!=='Reference').map(r=>r.series))];
  const regs=DATA.regime_meta.map(r=>r.id);
  const z=regs.map(id=>series.map(s=>{const m=DATA.regperf.find(r=>r.regime===id&&r.series===s);
    return m&&m.excess_vs_ref!=null?+(m.excess_vs_ref*100).toFixed(1):null;}));
  Plotly.newPlot('regheat',[{z,x:series,y:DATA.regime_meta.map(r=>r.name),type:'heatmap',
    colorscale:[[0,'#ff6b6b'],[.5,'#171d2b'],[1,'#39d98a']],zmid:0,
    colorbar:{title:'excess pp'}}],{...P,margin:{l:210,r:20,t:10,b:150},
    xaxis:{tickangle:-40,tickfont:{size:9}},yaxis:{tickfont:{size:10}}},{displayModeBar:false});
  drawRegime(regs[0]);
})();
function drawRegime(id){
  const rg=DATA.regime_meta.find(r=>r.id===id);
  $('#reganno').innerHTML=`<p><b>Macro:</b> ${rg.macro}</p><p><b>Factors:</b> ${rg.factors}</p>`
    +`<p><b>Regions:</b> ${rg.regions}</p><p><b>Shift:</b> ${rg.shift}</p>`;
  const rows=DATA.regperf.filter(r=>r.regime===id).sort((a,b)=>b.annualized-a.annualized);
  Plotly.newPlot('regbar',[{type:'bar',orientation:'h',
    y:rows.map(r=>r.series),x:rows.map(r=>+(r.annualized*100).toFixed(1)),
    marker:{color:rows.map(r=>FCOLOR[r.factor])}}],
    {...P,margin:{l:210,r:20,t:10,b:40},xaxis:{title:'Annualized return %',gridcolor:'#26304a'},
     yaxis:{autorange:'reversed',tickfont:{size:10}}},{displayModeBar:false});
}

// ---------- Correlations ----------
(function(){
  const sel=$('#corrsel');
  const opts=[['full','Full sample (common window)']].concat(DATA.regime_meta.map(r=>[r.id,r.name]));
  opts.forEach(([v,l])=>{if(DATA.corr[v]){const o=document.createElement('option');o.value=v;o.textContent=l;sel.appendChild(o);}});
  sel.onchange=()=>drawCorr(sel.value);drawCorr('full');
  Plotly.newPlot('rollchart',[{x:DATA.rolling.dates,y:DATA.rolling.vals,mode:'lines',
    line:{color:'#5b9dff',width:1.6},fill:'tozeroy',fillcolor:'rgba(91,157,255,.12)'}],
    {...P,margin:{l:50,r:10,t:10,b:40},yaxis:{title:'avg pairwise corr',range:[0.6,1],gridcolor:'#26304a'},
     xaxis:{gridcolor:'#26304a'}},{displayModeBar:false});
})();
function drawCorr(k){const c=DATA.corr[k];
  Plotly.newPlot('corrheat',[{z:c.z,x:c.labels,y:c.labels,type:'heatmap',
    colorscale:[[0,'#0f1420'],[.5,'#2a4a7a'],[1,'#ff6b6b']],zmin:0,zmax:1,
    colorbar:{title:'ρ'}}],{...P,margin:{l:190,r:20,t:10,b:170},
    xaxis:{tickangle:-45,tickfont:{size:9}},yaxis:{tickfont:{size:9},autorange:'reversed'}},
    {displayModeBar:false});}

// ---------- Macro ----------
(function(){
  if(!DATA.macro){ $('#t-macro').innerHTML='<div class="card"><h2>Macro</h2>'
    +'<div class="muted">No macro data baked — run the pipeline with the FRED ingest + macro_link steps.</div></div>'; return; }
  const meta={}; DATA.macro_meta.forEach(m=>meta[m.name]=m);
  // regime shading shapes + labels (reused by the series chart)
  const bands=DATA.regime_meta.map((r,i)=>({type:'rect',xref:'x',yref:'paper',
    x0:r.start,x1:r.end,y0:0,y1:1,fillcolor:i%2?'rgba(91,157,255,.07)':'rgba(244,162,89,.07)',
    line:{width:0},layer:'below'}));
  const bandLabels=DATA.regime_meta.map(r=>({x:r.start,y:1,xref:'x',yref:'paper',
    text:r.name.split(' ')[0],showarrow:false,font:{size:8,color:'#8b97ad'},
    xanchor:'left',yanchor:'bottom',hovertext:r.name}));

  // (a) indicator time series with regime bands
  const msel=$('#macrosel');
  Object.keys(DATA.macro.series).forEach(name=>{const o=document.createElement('option');
    o.value=name;o.textContent=`${name} — ${meta[name]?meta[name].units:''}`;msel.appendChild(o);});
  msel.onchange=()=>drawMacroSeries(msel.value);
  function drawMacroSeries(name){
    const m=meta[name]||{};
    $('#macronote').textContent=`${m.units||''} · ${m.transform==='yoy'?'12-month % change of the underlying index':'level as published'} · history ${m.start||'?'} → ${m.end||'?'} (FRED: ${m.id||''})`;
    // default to the analysis window (regime bands readable); drag/zoom out for full history
    Plotly.newPlot('macrochart',[{x:DATA.macro.dates,y:DATA.macro.series[name],mode:'lines',
      line:{color:'#5b9dff',width:1.4},connectgaps:false}],
      {...P,margin:{l:55,r:10,t:18,b:40},
       xaxis:{gridcolor:'#26304a',range:['1997-01-01',DATA.macro.dates[DATA.macro.dates.length-1]]},
       yaxis:{gridcolor:'#26304a'},shapes:bands,annotations:bandLabels},{displayModeBar:false});
  }
  drawMacroSeries(Object.keys(DATA.macro.series)[0]);

  // (b) index<->macro correlation heatmap with basis toggle
  const bsel=$('#macrobasis');
  bsel.onchange=()=>drawMacroHeat(bsel.value);
  function drawMacroHeat(basis){
    const c=DATA.macro_corr[basis];
    Plotly.newPlot('macroheat',[{z:c.z,x:c.indicators,y:c.series,type:'heatmap',
      colorscale:[[0,'#ff6b6b'],[.5,'#171d2b'],[1,'#39d98a']],zmid:0,zmin:-1,zmax:1,
      colorbar:{title:'corr'},hoverongaps:false}],
      {...P,margin:{l:210,r:20,t:10,b:120},xaxis:{tickangle:-40,tickfont:{size:9}},
       yaxis:{tickfont:{size:9},autorange:'reversed'}},{displayModeBar:false});
  }
  drawMacroHeat('chg');

  // (c) top drivers bar for one series (uses the currently selected basis)
  const dsel=$('#macrodrvsel');
  DATA.macro_corr.chg.series.forEach(s=>{const o=document.createElement('option');
    o.value=s;o.textContent=s;dsel.appendChild(o);});
  function drawDrivers(){
    const basis=bsel.value, c=DATA.macro_corr[basis];
    const i=c.series.indexOf(dsel.value);
    const pairs=c.indicators.map((ind,j)=>[ind,c.z[i][j]]).filter(p=>p[1]!=null)
      .sort((a,b)=>Math.abs(b[1])-Math.abs(a[1]));
    Plotly.newPlot('macrodrv',[{type:'bar',orientation:'h',
      y:pairs.map(p=>p[0]),x:pairs.map(p=>p[1]),
      marker:{color:pairs.map(p=>p[1]>=0?'#39d98a':'#ff6b6b')}}],
      {...P,margin:{l:170,r:20,t:6,b:40},
       xaxis:{title:`corr (${basis} basis)`,range:[-1,1],gridcolor:'#26304a'},
       yaxis:{autorange:'reversed',tickfont:{size:10}}},{displayModeBar:false});
  }
  dsel.onchange=drawDrivers;
  bsel.addEventListener('change',drawDrivers);
  drawDrivers();
})();

// ---------- Diversification (live) ----------
const EXAMPLE={"MSCI USA Momentum Index":40,"MSCI AC Asia ex Japan Momentum Index":30,"MSCI Emerging Markets Index":30};
function buildInputs(){const box=$('#winputs');box.innerHTML='';
  DATA.indices.forEach(idx=>{const row=document.createElement('div');row.className='wrow';
    row.innerHTML=`<label>${idx}</label><input type="number" min="0" step="1" value="${EXAMPLE[idx]||0}" data-idx="${idx}">`;
    box.appendChild(row);});
  box.querySelectorAll('input').forEach(i=>i.oninput=recompute);}
function preset(){$('#winputs').querySelectorAll('input').forEach(i=>i.value=EXAMPLE[i.dataset.idx]||0);recompute();}
function clearw(){$('#winputs').querySelectorAll('input').forEach(i=>i.value=0);recompute();}
function hhi(obj){const f=Object.values(obj).map(v=>v/100);const h=f.reduce((a,x)=>a+x*x,0);
  return{h,eff:h?1/h:0};}
function rollup(){
  const w={};let tot=0;
  $('#winputs').querySelectorAll('input').forEach(i=>{const v=+i.value||0;if(v>0){w[i.dataset.idx]=v;tot+=v;}});
  const validTotal=tot>0 && Math.abs(tot-100)<=DATA.weight_tolerance_pct;
  const sec={},ctry={},stk={};
  if(validTotal){
    for(const idx in w){const sw=w[idx]/100; // weights sum to ~100 -> this is the fraction, no rescaling
      const S=DATA.sec_by[idx]||{};for(const s in S)sec[s]=(sec[s]||0)+sw*S[s];
      let C=DATA.ctry_by[idx];if(!C)C=DATA.usa_idx.includes(idx)?{"United States":100}:{};
      for(const c0 in C){const c=DATA.country_fix[c0]||c0;ctry[c]=(ctry[c]||0)+sw*C[c0];}
      const K=DATA.stk_by[idx]||{};for(const k in K)stk[k]=(stk[k]||0)+sw*K[k];}
  }
  return{w,tot,validTotal,sec,ctry,stk};}

// Blended (constant-mix) portfolio performance from the sleeves' own return series, over their
// overlapping history — mirrors portfolio/diversification.py::portfolio_performance in Python.
function portfolioPerf(w){
  const idxs=Object.keys(w);
  const keys=idxs.map(i=>DATA.idx_series_key[i]);
  if(!idxs.length || keys.some(k=>k==null)) return null;
  const dates=allDates, okIdx=[];
  for(let i=0;i<dates.length;i++){ if(keys.every(k=>DATA.levels.series[k][i]!=null)) okIdx.push(i); }
  if(okIdx.length<2) return null;
  let level=100; const path=[level];
  for(let j=1;j<okIdx.length;j++){
    const i0=okIdx[j-1], i1=okIdx[j]; let r=0;
    for(const idx of idxs){ const key=DATA.idx_series_key[idx];
      const v0=DATA.levels.series[key][i0], v1=DATA.levels.series[key][i1];
      r += (w[idx]/100)*(v1/v0-1); }
    level*=(1+r); path.push(level);
  }
  return computeSeriesStats(path, okIdx.map(i=>dates[i]));
}
function sortObj(o){return Object.entries(o).sort((a,b)=>b[1]-a[1]);}
function barh(el,entries,thr,color){
  const over=entries.filter(([k,v])=>v>thr).map(e=>e[0]);
  Plotly.newPlot(el,[{type:'bar',orientation:'h',y:entries.map(e=>e[0]),x:entries.map(e=>+e[1].toFixed(2)),
    marker:{color:entries.map(e=>e[1]>thr?'#ff6b6b':color)}}],
    {...P,margin:{l:170,r:20,t:6,b:30},xaxis:{title:'%',gridcolor:'#26304a'},
     yaxis:{autorange:'reversed',tickfont:{size:10}}},{displayModeBar:false});
  return over;}
function recompute(){
  const {w,tot,validTotal,sec,ctry,stk}=rollup();
  const T=DATA.thresh;

  const totalPill=$('#wtotal');
  totalPill.textContent=`Total: ${tot.toFixed(1)}%`;
  totalPill.className='pill'+(tot===0?'':(validTotal?' good':' warn'));

  if(tot===0){
    $('#divsummary').innerHTML='<div class="muted">No sleeves selected.</div>';
    $('#divperf').innerHTML='';
    ['divsector','divcountry','divstock'].forEach(id=>Plotly.purge(id));
    return;
  }
  if(!validTotal){
    $('#divsummary').innerHTML=`<div class="warn">Weights sum to ${tot.toFixed(1)}%, not 100%. `
      +`A portfolio can't hold more or less than itself — adjust the sleeve weights above so `
      +`they add up to 100.</div>`;
    $('#divperf').innerHTML='';
    ['divsector','divcountry','divstock'].forEach(id=>Plotly.purge(id));
    return;
  }

  const se=sortObj(sec),ce=sortObj(ctry),ke=sortObj(stk).slice(0,22);
  const so=barh('divsector',se,T.sector,'#5b9dff');
  const co=barh('divcountry',ce,T.country,'#f4a259');
  const ko=barh('divstock',ke,T.stock,'#39d98a');
  const hs=hhi(sec),hc=hhi(ctry),hk=hhi(stk);
  const flag=arr=>arr.length?`<span class="warn">${arr.join(', ')}</span>`:'<span class="good">none</span>';
  $('#divsummary').innerHTML=
    `<div class="metric">Sector HHI <b>${hs.h.toFixed(3)}</b><div class="muted">eff # ${hs.eff.toFixed(1)}</div></div>`
   +`<div class="metric">Country HHI <b>${hc.h.toFixed(3)}</b><div class="muted">eff # ${hc.eff.toFixed(1)}</div></div>`
   +`<div class="metric">Stock HHI <b>${hk.h.toFixed(3)}</b><div class="muted">eff # ${hk.eff.toFixed(1)}</div></div>`
   +`<h3>Flags (sector>${T.sector}%, country>${T.country}%, stock>${T.stock}%)</h3>`
   +`<p>Sector: ${flag(so)}</p><p>Country: ${flag(co)}</p><p>Single-stock: ${flag(ko)}</p>`
   +`<div class="muted">Top-1 sector ${se[0][1].toFixed(1)}% · top-1 country ${ce[0][1].toFixed(1)}% · top-3 stocks ${(ke[0][1]+ke[1][1]+ke[2][1]).toFixed(1)}%</div>`;

  const perf=portfolioPerf(w);
  $('#divperf').innerHTML = perf==null
    ? '<div class="muted">Insufficient overlapping history among the selected sleeves.</div>'
    : `<div class="metric">CAGR <b>${pct(perf.CAGR)}</b></div>`
     +`<div class="metric">Ann vol <b>${pct(perf.ann_vol)}</b></div>`
     +`<div class="metric">Sharpe(rf0) <b>${perf.sharpe_rf0==null?'—':perf.sharpe_rf0.toFixed(2)}</b></div>`
     +`<div class="metric">Max drawdown <b>${pct(perf.max_drawdown)}</b></div>`
     +`<div class="muted">Window: ${perf.start} → ${perf.end} (${perf.months} months)</div>`;
}
buildInputs();recompute();
"""
