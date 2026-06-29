/* sw.js — офлайн-кэш оболочки приложения. */
const CACHE = 'bez-cenzury-v1';
const ASSETS = [
  './',
  './index.html',
  './styles.css',
  './app.js',
  './dialogue.js',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  // Запросы к API и любую стороннюю сеть не трогаем — пусть идут напрямую.
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;

  // Оболочку отдаём из кэша, в фоне обновляем (stale-while-revalidate).
  e.respondWith(
    caches.match(req).then((cached) => {
      const network = fetch(req).then((res) => {
        if (res && res.status === 200) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return res;
      }).catch(() => cached);
      return cached || network;
    })
  );
});
