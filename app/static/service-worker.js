// Service Worker PWA para SAMU UTGZ - Soporte Offline y Cache Resiliente
const CACHE = 'samu-pwa-v2.9.0';
const ASSETS = [
  '/',
  '/index.html',
  '/static/style.css?v=2.9.0',
  '/static/app.js?v=2.9.0',
  '/manifest.webmanifest',
  '/static/assets/samu-original.png',
  '/static/assets/icon-192.png',
  '/static/assets/icon-512.png',
  '/static/assets/utgz-logo.png',
  '/static/assets/logo-utgz.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE).then(async cache => {
      // Usamos matchAll/allSettled para que si un asset opcional falta, no rompa la instalación
      const results = await Promise.allSettled(
        ASSETS.map(url => fetch(url).then(res => {
          if (res.ok) return cache.put(url, res);
        }))
      );
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  // Peticiones fuera del origen no se interceptan
  if (url.origin !== self.location.origin) return;

  // Peticiones de API o Descargas de PDFs: se van a la red directo. Si falla la red, que la app lo maneje
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/descargar/')) {
    return;
  }

  // Navegación de páginas HTML (SPA routing: /, /login, /enfermeria, /alumno, /bitacora, etc.)
  if (req.mode === 'navigate' || req.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(req).catch(() => {
        return caches.match('/index.html') || caches.match('/');
      })
    );
    return;
  }

  // Archivos estáticos (CSS, JS, imágenes, iconos, manifest): Cache first con actualización en segundo plano
  event.respondWith(
    caches.match(req).then(cached => {
      const netFetch = fetch(req).then(res => {
        if (res.ok && req.method === 'GET') {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(req, clone));
        }
        return res;
      }).catch(() => null);

      return cached || netFetch;
    })
  );
});
