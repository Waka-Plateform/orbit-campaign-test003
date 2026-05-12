(function(){
const root=document.getElementById('console-sources'); if(!root) return;
const list=document.getElementById('sources-list'), detail=document.getElementById('sources-detail');
async function show(id){try{const d=await OrbitConsole.fetchJson(`/api/console/sources/${encodeURIComponent(id)}`);detail.textContent=JSON.stringify(d,null,2);}catch(e){detail.textContent=e.message;}}
async function load(){try{const d=await OrbitConsole.fetchJson(root.dataset.api);const items=d.sources||d.items||[];list.innerHTML=items.map(s=>`<button class="orbit-row" data-id="${s.id||s.artifact_id}"><span>${s.name||s.id||s.artifact_id}</span><strong>${s.kind||s.channel||''}</strong></button>`).join('')||'<p class="orbit-muted">Aucune source.</p>';list.querySelectorAll('[data-id]').forEach(b=>b.addEventListener('click',()=>show(b.dataset.id)));if(items[0])show(items[0].id||items[0].artifact_id);}catch(e){root.insertAdjacentHTML('beforeend',`<div class="orbit-error">${e.message}</div>`);}}
load();
})();
