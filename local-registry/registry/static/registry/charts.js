'use strict';
(() => {
  const dataNode = document.getElementById('report-data');
  if (!dataNode) return;
  const report = JSON.parse(dataNode.textContent);
  const svgNS = 'http://www.w3.org/2000/svg';
  const el = (name, attrs, text) => {const n = document.createElementNS(svgNS, name); Object.entries(attrs).forEach(([k,v]) => n.setAttribute(k,v)); if(text !== undefined)n.textContent=text; return n;};
  const labels = {baseline:'Baseline',postop:'Post-op','3m':'3 months','6m':'6 months','9m':'9 months','1y':'1 year','2y':'2 years'};
  const chart = document.getElementById('recovery-chart');
  const select = document.getElementById('chart-score');
  const render = () => {
    const score = select.value, max = score==='vas_main'?10:100;
    const rows = report.summary.filter(r=>r.score===score);
    const svg = el('svg',{viewBox:'0 0 700 310',role:'img','aria-label':`${select.selectedOptions[0].textContent}: mean scores by recorded visit. Sample sizes shown below.`});
    svg.append(el('title',{},'Mean scores at each visit. Available records; this is not a paired trajectory.'));
    for(let i=0;i<=5;i++){let y=245-i*42;svg.append(el('line',{x1:48,y1:y,x2:665,y2:y,stroke:'#e1e9ec'}));svg.append(el('text',{x:38,y:y+4,'text-anchor':'end',fill:'#647685','font-size':12},(i*max/5).toString()));}
    let prev=null;
    rows.forEach((r,i)=>{let x=65+i*96;svg.append(el('text',{x,y:275,'text-anchor':'middle',fill:'#647685','font-size':12},labels[r.timepoint]));if(r.mean===null){prev=null;return;}let y=245-r.mean/max*210;if(prev)svg.append(el('line',{x1:prev.x,y1:prev.y,x2:x,y2:y,stroke:'#087f80','stroke-width':3}));let dot=el('circle',{cx:x,cy:y,r:5,fill:'#087f80'});dot.append(el('title',{},`${labels[r.timepoint]}: mean ${r.mean}, n=${r.n}, missing ${r.missing}`));svg.append(dot);prev={x,y};});
    chart.replaceChildren(svg);
    document.getElementById('chart-counts').textContent=rows.map(r=>`${labels[r.timepoint]}: n=${r.n}`).join(' · ');
  };
  select.addEventListener('change',render);render();
  const download=document.createElement('button');download.type='button';download.textContent='Export chart (SVG)';download.addEventListener('click',()=>{const svg=chart.querySelector('svg').cloneNode(true);svg.setAttribute('xmlns',svgNS);const url=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml'}));const a=document.createElement('a');a.href=url;a.download=`zoe-${select.value}-${report.cutoff}.svg`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});chart.after(download);
  const mix=document.getElementById('approach-chart');
  Object.entries(report.approaches).forEach(([name,count])=>{const row=document.createElement('div');row.className='mix-row';const label=document.createElement('span');label.textContent=name;const bar=document.createElement('div');bar.className='mix-bar';const fill=document.createElement('span');fill.style.width=`${report.procedures?count/report.procedures*100:0}%`;bar.append(fill);const n=document.createElement('b');n.textContent=count;row.append(label,bar,n);mix.append(row);});
  if(!report.procedures)mix.textContent='No operations in this cohort.';
})();
