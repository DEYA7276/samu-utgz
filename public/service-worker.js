// Datos clínicos, sesiones, API y PDF NUNCA se almacenan en caché.
const CACHE='samu-assets-v2.6.5';
const ASSETS=['/','/static/style.css?v=2.6.5','/static/app.js?v=2.6.5','/static/assets/samu-original.png','/static/assets/icon-192.png','/static/assets/icon-512.png'];
self.addEventListener('install', event=>event.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
 const req=event.request; const url=new URL(req.url);
 if(req.method!=='GET'||url.origin!==self.location.origin||url.pathname.startsWith('/api/')||url.pathname.startsWith('/descargar/')||url.pathname==='/login'||url.pathname==='/enfermeria'||url.pathname==='/alumno'||url.pathname==='/importar'||url.pathname==='/dashboard'||url.pathname==='/')return;
 event.respondWith(fetch(req).then(res=>{if(res.ok){const copy=res.clone();caches.open(CACHE).then(c=>c.put(req,copy));}return res;}).catch(()=>caches.match(req)));
});
