(function(){
const root=document.getElementById('console-channels'); if(!root) return;
const fmt=v=>v===null||v===undefined?'—':(typeof v==='object'?JSON.stringify(v):String(v));
const kpi=(label,value)=>`<div class="orbit-kpi"><span class="orbit-muted">${label}</span><strong>${value}</strong></div>`;
async function load(){try{const d=await OrbitConsole.fetchJson(root.dataset.api);const channels=d.channels||d.active_channels||d||{};const entries=Array.isArray(channels)?channels.map(c=>[c.channel||c,c]):Object.entries(channels);document.getElementById('channels-summary').innerHTML=entries.map(([name,c])=>kpi(name,c.enabled===false?'Inactif':'Actif')).join('')||'<p class="orbit-muted">Aucun canal.</p>';const management=d.management||d.manage||{};document.getElementById('channels-manage').innerHTML=entries.map(([name,c])=>`<article class="orbit-card"><h2>${name}</h2><pre>${JSON.stringify(c,null,2)}</pre><p class="orbit-muted">${fmt(management[name]?.options||management[name]?.select||'Configuration lecture seule')}</p></article>`).join('');}catch(e){root.insertAdjacentHTML('beforeend',`<div class="orbit-error">${e.message}</div>`);}}
load();
})();
