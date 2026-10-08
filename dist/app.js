import {mean,summary,paired,filterCohort,toCSV} from './analytics.js';
const $=id=>document.getElementById(id); let all=[], cohort=[], page=0, score='vas'; const size=10;
const fmt=(n, decimals=1)=>n===null?'—':n.toFixed(decimals); const percentage=(n,d)=>d?fmt(100*n/d)+'%':'—';
function bars(id, values, denominator){$(id).innerHTML=values.map(([label,n])=>`<div class="bar-row"><div class="bar-label"><span>${label}</span><span>${n} · ${percentage(n,denominator)}</span></div><div class="bar-track"><div class="bar-fill" style="width:${denominator?100*n/denominator:0}%"></div></div></div>`).join('');}
function renderRecovery(){
 const times=['baseline','3m','6m'], names=['Preoperative','3 months','6 months']; const max=score==='vas'?10:100;
 const means=times.map(t=>mean(cohort.map(r=>r[score+'_'+t]))), counts=times.map(t=>cohort.filter(r=>r[score+'_'+t]!==null).length);
 if(!cohort.length){$('recovery').innerHTML='<div class="empty">No patients match these filters.</div>'; $('visit-counts').textContent=''; return;}
 const xs=[65,275,485], y=v=>180-v/max*145;
 let svg=`<svg viewBox="0 0 550 215" role="img" aria-label="Mean ${score.toUpperCase()} scores at baseline, 3 months and 6 months"><title>Mean ${score.toUpperCase()} scores: ${means.map(v=>fmt(v)).join(', ')}</title>`;
 for(let i=0;i<=5;i++){const value=max*i/5;svg+=`<line x1="45" x2="515" y1="${y(value)}" y2="${y(value)}" stroke="#e9efeb"/><text x="28" y="${y(value)+4}" text-anchor="end" fill="#78918a" font-size="10">${value}</text>`;}
 for(let i=1;i<3;i++)if(means[i]!==null&&means[i-1]!==null)svg+=`<line x1="${xs[i-1]}" y1="${y(means[i-1])}" x2="${xs[i]}" y2="${y(means[i])}" stroke="#148472" stroke-width="3"/>`;
 means.forEach((m,i)=>{if(m!==null)svg+=`<circle cx="${xs[i]}" cy="${y(m)}" r="5" fill="#148472" stroke="white" stroke-width="2"/><text x="${xs[i]}" y="${y(m)-12}" text-anchor="middle" font-size="12" fill="#156e5e">${fmt(m)}</text>`;svg+=`<text x="${xs[i]}" y="205" text-anchor="middle" font-size="10" fill="#78918a">${names[i]}</text>`;});
 $('recovery').innerHTML=svg+'</svg>'; $('visit-counts').textContent=names.map((n,i)=>`${n}: n=${counts[i]}`).join('   ·   ')+' · Lower scores indicate improvement.';
}
function renderTable(){
 const query=$('search').value.trim().toLowerCase(); const rows=cohort.filter(r=>r.patient_id.toLowerCase().includes(query)); const pages=Math.ceil(rows.length/size);page=Math.max(0,Math.min(page,pages-1));
 $('rows').innerHTML=rows.slice(page*size,(page+1)*size).map(r=>`<tr><td>${r.patient_id}</td><td>${r.age} / ${r.sex}</td><td>${r.diagnosis}</td><td>${r.procedure}</td><td>${r.hospital_days} d</td><td>${r.vas_baseline} → ${r.vas_6m??'Not recorded'}</td><td>${r.odi_baseline} → ${r.odi_6m??'Not recorded'}</td><td class="${r.complication==='None'?'ok':''}">${r.complication}</td></tr>`).join('')||'<tr><td colspan="8">No matching patients.</td></tr>';
 $('page-info').textContent=rows.length?`${page*size+1}–${Math.min((page+1)*size,rows.length)} of ${rows.length} patients`:'0 patients';$('prev').disabled=page===0;$('next').disabled=page+1>=pages;
}
function render(){cohort=filterCohort(all,Object.fromEntries(['procedure','diagnosis','sex','age'].map(k=>[k,$(k).value])));const s=summary(cohort);
 $('status').textContent=`${s.count} of ${all.length} synthetic patients selected · Surgery dates: 2024–2025`;
 const items=[['Patients in cohort',s.count,'Fictional surgical records'],['Mean hospital stay',fmt(s.stay)+' d',`Available records: n=${s.count}`],['Any complication',percentage(s.complications,s.count),`${s.complications} / ${s.count} patients`],['6-month follow-up',percentage(s.followup,s.count),`${s.followup} recorded · ${s.count-s.followup} missing`]];
 $('metrics').innerHTML=items.map(([label,value,sub])=>`<article class="metric"><div class="label">${label}</div><div class="value">${value}</div><div class="sub">${sub}</div></article>`).join('');
 bars('procedures',['Full endoscopic','UBE','Open decompression','Decompression + fusion'].map(p=>[p,cohort.filter(r=>r.procedure===p).length]),s.count);
 bars('complications',['Dural tear','Superficial infection','Transient neurological deficit'].map(c=>[c,cohort.filter(r=>r.complication===c).length]),s.count);
 $('paired').innerHTML='<div class="paired-grid">'+['vas','odi'].map(k=>{const changes=paired(cohort,k);return `<div><div class="paired-title">Mean ${k.toUpperCase()} reduction</div><div class="paired-value">${fmt(mean(changes))}<span style="font-size:12px"> points</span></div><div class="paired-sub">Paired observations: n=${changes.length}</div></div>`;}).join('')+'</div>';renderRecovery();renderTable();$('export').disabled=!cohort.length;
}
['procedure','diagnosis','sex','age'].forEach(k=>$(k).addEventListener('change',()=>{page=0;render();}));$('reset').onclick=()=>{['procedure','diagnosis','sex','age'].forEach(k=>$(k).value='');$('search').value='';page=0;render();};$('search').oninput=()=>{page=0;renderTable();};$('prev').onclick=()=>{page--;renderTable();};$('next').onclick=()=>{page++;renderTable();};
document.querySelectorAll('[data-score]').forEach(b=>b.onclick=()=>{score=b.dataset.score;document.querySelectorAll('[data-score]').forEach(t=>t.classList.toggle('selected',t===b));renderRecovery();});
$('export').onclick=()=>{const blob=new Blob([toCSV(cohort,Object.keys(all[0]))],{type:'text/csv;charset=utf-8;'});const a=document.createElement('a');const url=URL.createObjectURL(blob);a.href=url;a.download='synthetic-spine-cohort.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
try{const response=await fetch('patients.json');if(!response.ok)throw new Error('Data unavailable');all=await response.json();for(const k of ['procedure','diagnosis'])for(const value of [...new Set(all.map(r=>r[k]))].sort()){const o=document.createElement('option');o.value=value;o.textContent=value;$(k).append(o);}render();}catch(e){$('status').textContent='Unable to load synthetic data. Serve the project using a local web server and reload.';$('export').disabled=true;console.error(e);}
