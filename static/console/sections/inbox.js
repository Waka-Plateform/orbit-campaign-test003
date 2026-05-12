(function(){
const root=document.getElementById('console-inbox'); if(!root) return;
const list=document.getElementById('inbox-list'), channel=document.getElementById('inbox-channel');
function row(m){return `<div class="orbit-row"><span>${m.received_at||m.created_at||''} ${m.from||m.sender||m.contact_id||''}<br><small>${m.body||m.text||m.subject||JSON.stringify(m)}</small></span><strong>${m.status||m.channel||''}</strong></div>`}
async function load(){try{const d=await OrbitConsole.fetchJson(`/api/console/inbox/${channel.value}`);const items=d.messages||d.rows||d.items||[];list.innerHTML=items.map(row).join('')||'<p class="orbit-muted">Aucun message entrant.</p>';}catch(e){list.innerHTML=`<div class="orbit-error">${e.message}</div>`;}}
document.getElementById('inbox-refresh').addEventListener('click',load);channel.addEventListener('change',load);load();
})();
