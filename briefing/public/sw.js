// sw.js — service worker voor offline shell
// Versie bumpen bij elke deploy om cache te invalideren

const CACHE_VERSION = 'briefing-v1';
const SHELL = [
  '/',
  '/index.html',
  '/app.js',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(SHELL))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // API calls: NEVER cache — moet vers zijn
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  // Shell assets: cache-first, fallback naar network
  if (event.request.method === 'GET') {
    event.respondWith(
      caches.match(event.request).then((cached) =>
        cached || fetch(event.request).then((res) => {
          // achtergrond-update cache
          if (res.ok && SHELL.some((p) => url.pathname === p || url.pathname.endsWith(p))) {
            const copy = res.clone();
            caches.open(CACHE_VERSION).then((cache) => cache.put(event.request, copy));
          }
          return res;
        })
      )
    );
  }
});
