// VARUNA Marine Offline Service Worker
// Provides intelligent CacheStorage for Leaflet map tiles (CARTO/Esri/OSM)
// and static web assets for uninterrupted sea-borne operation.

const CACHE_NAME = 'varuna-map-cache-v1';
const TILE_DOMAINS = ['basemaps.cartocdn.com', 'arcgisonline.com', 'openstreetmap.org', 'tile.openstreetmap.org'];

self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Strategy for map tile requests: Stale-While-Revalidate with Cache Fallback
  if (TILE_DOMAINS.some((domain) => url.hostname.includes(domain))) {
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((cachedResponse) => {
          const fetchPromise = fetch(event.request)
            .then((networkResponse) => {
              if (networkResponse && networkResponse.status === 200) {
                cache.put(event.request, networkResponse.clone());
              }
              return networkResponse;
            })
            .catch(() => cachedResponse);

          return cachedResponse || fetchPromise;
        });
      })
    );
    return;
  }

  // Standard network-first for local API / assets with offline cache fallback
  if (event.request.method === 'GET' && !url.pathname.startsWith('/api') && !url.pathname.startsWith('/v1')) {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(event.request))
    );
  }
});
