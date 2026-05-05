/**
 * Service Worker for Relai Map Analysis
 * Caches static assets including Plan 2031 image
 */

const CACHE_NAME = 'relai-map-cache-v2';
const STATIC_ASSETS = [
  'https://ihraowxbduhlichzszgk.supabase.co/storage/v1/object/public/map-assets/hmda_test_300dpi.png',
  'data/hmda_masterplan.png',
  // Add other static assets as needed
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS.map(url => {
          // Handle relative URLs
          return new Request(url, { cache: 'reload' });
        })).catch(err => {
          console.warn('Service Worker: Some assets failed to cache', err);
          // Don't fail the entire installation if some assets fail
        });
      })
      .then(() => {
        console.log('Service Worker: Installed successfully');
        return self.skipWaiting(); // Activate immediately
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              console.log('Service Worker: Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activated');
        return self.clients.claim(); // Take control immediately
      })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Only cache GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  // Check if this is a request for a static asset we want to cache
  const shouldCache = STATIC_ASSETS.some(asset => url.pathname.includes(asset));

  if (shouldCache) {
    event.respondWith(
      caches.match(event.request)
        .then((cachedResponse) => {
          if (cachedResponse) {
            console.log('Service Worker: Serving from cache:', url.pathname);
            return cachedResponse;
          }

          // Not in cache, fetch from network and cache it
          return fetch(event.request)
            .then((response) => {
              // Check if valid response
              if (!response || response.status !== 200 || response.type !== 'basic') {
                return response;
              }

              // Clone the response
              const responseToCache = response.clone();

              caches.open(CACHE_NAME)
                .then((cache) => {
                  console.log('Service Worker: Caching new resource:', url.pathname);
                  cache.put(event.request, responseToCache);
                });

              return response;
            })
            .catch((error) => {
              console.error('Service Worker: Fetch failed:', error);
              throw error;
            });
        })
    );
  }
});

// Message event - handle cache updates
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.delete(CACHE_NAME)
        .then(() => {
          console.log('Service Worker: Cache cleared');
          return self.clients.matchAll();
        })
        .then((clients) => {
          clients.forEach(client => {
            client.postMessage({ type: 'CACHE_CLEARED' });
          });
        })
    );
  }
});
