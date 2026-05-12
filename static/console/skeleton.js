window.OrbitConsole={fetchJson:async function(url,options){const response=await fetch(url,options||{});if(!response.ok){throw new Error('HTTP '+response.status+' for '+url)}return response.json();}};
