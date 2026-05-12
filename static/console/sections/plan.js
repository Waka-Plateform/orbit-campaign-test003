(function(){
const root=document.getElementById('console-plan'); if(!root) return;
const row=(a,b)=>`<div class="orbit-row"><span>${a}</span><strong>${b}</strong></div>`;
async function load(){try{const d=await OrbitConsole.fetchJson(root.dataset.api);document.getElementById('plan-json').textContent=JSON.stringify(d,null,2);document.getElementById('plan-runtime').innerHTML=Object.entries(d.runtime_state||{}).map(([k,v])=>row(k,v)).join('')||'<p class="orbit-muted">Runtime vide.</p>';}catch(e){root.insertAdjacentHTML('beforeend',`<div class="orbit-error">${e.message}</div>`);}}
document.querySelectorAll('[data-plan-action]').forEach(b=>b.addEventListener('click',async()=>{try{const action=b.dataset.planAction;const r=await OrbitConsole.fetchJson(`/api/console/plan/${action}`,{method:'POST'});alert(`OK: ${r.new_status||action}`);load();}catch(e){alert(e.message)}}));load();
})();
