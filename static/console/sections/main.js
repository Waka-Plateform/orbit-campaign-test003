(function(){
const root=document.getElementById('console-main'); if(!root) return;
const fmt=v=>v===null||v===undefined?'—':(typeof v==='number'?new Intl.NumberFormat('fr-FR').format(v):String(v));
const pct=v=>typeof v==='number'?new Intl.NumberFormat('fr-FR',{style:'percent',maximumFractionDigits:1}).format(v):fmt(v);
const row=(a,b)=>`<div class="orbit-row"><span>${a}</span><strong>${b}</strong></div>`;
const kpi=(label,value)=>`<div class="orbit-kpi"><span class="orbit-muted">${label}</span><strong>${value}</strong></div>`;
async function load(){try{const d=await OrbitConsole.fetchJson(root.dataset.api);document.querySelector('.orbit-hero h1').textContent=d.campaign?.name||d.campaign?.slug||'Campagne';document.querySelector('.orbit-hero p:last-child').textContent=d.campaign?.objective||'Console opérationnelle campagne';const ops=d.kpi_ops||{};document.getElementById('main-kpis').innerHTML=[kpi('Volume cible',fmt(ops.volume_target?.value)),kpi('Volume traité',fmt(ops.volume_processed?.value)),kpi('Ouverts / actifs',fmt(ops.volume_open?.value)),kpi('Clôture',pct(ops.file_closure_rate?.value))].join('');document.getElementById('main-audiences').innerHTML=(d.audiences||[]).map(a=>row(a.name||a.id,fmt(a.count_current))).join('')||'<p class="orbit-muted">Aucune audience.</p>';document.getElementById('main-channels').innerHTML=(d.volume_by_channel||[]).map(c=>row(c.channel,`sent ${fmt(c.sent)} · delivered ${fmt(c.delivered)} · opened ${fmt(c.opened||c.clicked)}`)).join('')||'<p class="orbit-muted">Aucune donnée canal.</p>';document.getElementById('main-resources').innerHTML=Object.entries(d.azure_resources||{}).map(([k,v])=>row(k,fmt(v))).join('');}catch(e){root.insertAdjacentHTML('beforeend',`<div class="orbit-error">${e.message}</div>`);}}
load();
})();
