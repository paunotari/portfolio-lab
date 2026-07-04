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
   <div class="card"><h2>Risk / return (common window)</h2><div id="scatter" style="height:420px"></div>
     <div class="muted">Bubble size = max drawdown depth. Common window shown in header.</div></div>
   <div class="card"><h2>Cumulative growth (base 100, log scale)</h2>
     <div class="muted">Toggle series in the legend. Click a legend item to hide.</div>
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
       <div class="muted">Type weights (need not sum to 100 — auto-normalized). Set 0 to drop a sleeve.</div>
       <div id="winputs" style="margin-top:10px;max-height:420px;overflow:auto"></div>
       <div style="margin-top:10px"><button onclick="preset()">example preset</button>
        <button onclick="clearw()">clear</button></div></div>
     <div class="card"><h2>Concentration summary</h2><div id="divsummary"></div></div>
   </div>
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
const cw=DATA.perf[0];
$('#sub').textContent=`Common window ${cw.cw_start} → ${cw.cw_end} · ${DATA.indices.length} indices · 7 regions × 4 factor types · monthly net USD`;

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

// ---------- Performance ----------
(function(){
  const x=DATA.perf.map(r=>r.cw_ann_vol*100), y=DATA.perf.map(r=>r.cw_CAGR*100);
  const size=DATA.perf.map(r=>8+Math.abs(r.cw_max_drawdown)*40);
  const col=DATA.perf.map(r=>FCOLOR[r.factor]);
  const txt=DATA.perf.map(r=>`${r.series}<br>CAGR ${pct(r.cw_CAGR)} · vol ${pct(r.cw_ann_vol)}`
    +`<br>Sharpe ${r.cw_sharpe_rf0.toFixed(2)} · maxDD ${pct(r.cw_max_drawdown)}`);
  Plotly.newPlot('scatter',[{x,y,text:txt,mode:'markers',type:'scatter',
    marker:{size,color:col,line:{color:'#0f1420',width:1}},hoverinfo:'text'}],
    {...P,xaxis:{title:'Annualized volatility %',gridcolor:'#26304a'},
     yaxis:{title:'CAGR %',gridcolor:'#26304a'}},{displayModeBar:false});
  // cumulative
  const tr=Object.keys(DATA.levels.series).map(name=>{
    const fac=name.split(' | ')[1];
    return {x:DATA.levels.dates,y:DATA.levels.series[name],name,mode:'lines',
      line:{width:1.3,color:FCOLOR[fac]||'#5b9dff'},opacity:.85};});
  Plotly.newPlot('cum',tr,{...P,margin:{l:55,r:10,t:10,b:40},
    yaxis:{type:'log',gridcolor:'#26304a'},xaxis:{gridcolor:'#26304a'},
    legend:{orientation:'h',font:{size:9},y:-0.12}},{displayModeBar:false});
  // table
  perfTable('cw_CAGR',false);
})();
function perfTable(sortKey,asc){
  const rows=[...DATA.perf].sort((a,b)=>asc?a[sortKey]-b[sortKey]:b[sortKey]-a[sortKey]);
  const cols=[['series','Series'],['cw_CAGR','CAGR'],['cw_ann_vol','Ann vol'],
    ['cw_sharpe_rf0','Sharpe'],['cw_max_drawdown','Max DD'],['full_CAGR','Full CAGR']];
  let h='<table><thead><tr>'+cols.map(c=>`<th data-k="${c[0]}">${c[1]}</th>`).join('')+'</tr></thead><tbody>';
  rows.forEach(r=>{h+='<tr><td>'+r.series+'</td>'
    +`<td>${pct(r.cw_CAGR)}</td><td>${pct(r.cw_ann_vol)}</td><td>${r.cw_sharpe_rf0.toFixed(2)}</td>`
    +`<td class="${r.cw_max_drawdown<-0.55?'warn':''}">${pct(r.cw_max_drawdown)}</td><td>${pct(r.full_CAGR)}</td></tr>`;});
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
  const sec={},ctry={},stk={};
  for(const idx in w){const sw=w[idx]/tot;
    const S=DATA.sec_by[idx]||{};for(const s in S)sec[s]=(sec[s]||0)+sw*S[s];
    let C=DATA.ctry_by[idx];if(!C)C=DATA.usa_idx.includes(idx)?{"United States":100}:{};
    for(let c in C){c=DATA.country_fix[c]||c;} // normalize keys below
    for(const c0 in C){const c=DATA.country_fix[c0]||c0;ctry[c]=(ctry[c]||0)+sw*C[c0];}
    const K=DATA.stk_by[idx]||{};for(const k in K)stk[k]=(stk[k]||0)+sw*K[k];}
  return{w,tot,sec,ctry,stk};}
function sortObj(o){return Object.entries(o).sort((a,b)=>b[1]-a[1]);}
function barh(el,entries,thr,color){
  const over=entries.filter(([k,v])=>v>thr).map(e=>e[0]);
  Plotly.newPlot(el,[{type:'bar',orientation:'h',y:entries.map(e=>e[0]),x:entries.map(e=>+e[1].toFixed(2)),
    marker:{color:entries.map(e=>e[1]>thr?'#ff6b6b':color)}}],
    {...P,margin:{l:170,r:20,t:6,b:30},xaxis:{title:'%',gridcolor:'#26304a'},
     yaxis:{autorange:'reversed',tickfont:{size:10}}},{displayModeBar:false});
  return over;}
function recompute(){
  const {w,tot,sec,ctry,stk}=rollup();
  const T=DATA.thresh;
  const se=sortObj(sec),ce=sortObj(ctry),ke=sortObj(stk).slice(0,22);
  if(tot===0){$('#divsummary').innerHTML='<div class="muted">No sleeves selected.</div>';
    ['divsector','divcountry','divstock'].forEach(id=>Plotly.purge(id));return;}
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
}
buildInputs();recompute();
"""
