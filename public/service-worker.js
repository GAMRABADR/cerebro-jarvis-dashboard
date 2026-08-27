// E.B. Autonomous PWA Service Worker v1.0
const CACHE_NAME = 'eb-supreme-v1003.0';
const ASSETS = [
  '/',
  '/index.html',
  '/style.css?v=103.0',
  '/app.js?v=103.0',
  '/synaptic_3d_lab.js?v=103.0',
  '/manifest.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((k) => {
          if (k !== CACHE_NAME) return caches.delete(k);
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // Network first, fallback to cache for static assets
  if (e.request.url.includes('/api/')) {
    return; // Pass dynamic API calls straight to network
  }
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
