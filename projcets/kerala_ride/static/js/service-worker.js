const CACHE_NAME = 'keralaride-v1';
// Assets to cache immediately on first load
const ASSETS_TO_CACHE = [
    '/',
    '/static/css/style.css',
    '/static/js/driver_dashboard.js', // or whatever your JS file is named
    'https://cdn.socket.io/4.7.2/socket.io.min.js'
];

// 1. Install Event: Cache core layouts instantly
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('📦 Service Worker: Pre-caching structural assets');
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
    self.skipWaiting();
});

// 2. Activate Event: Clean up old historical caches if code changes
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cache) => {
                    if (cache !== CACHE_NAME) {
                        console.log('🧹 Service Worker: Clearing old cache storage layers');
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// 3. Intercept Requests: Cache-First Strategy for static layouts, Network-First for APIs
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Skip intercepting live tracking WebSocket traffic or API bookings
    if (url.pathname.startsWith('/socket.io') || event.request.method !== 'GET') {
        return;
    }

    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                // Instantly return the file from phone memory (0ms delay!)
                return cachedResponse;
            }

            // Otherwise, fetch it from the Render server normally
            return fetch(event.request).then((networkResponse) => {
                // If it's a static file, save a copy in the phone cache for next time
                if (networkResponse.status === 200 && url.pathname.startsWith('/static/')) {
                    return caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, networkResponse.clone());
                        return networkResponse;
                    });
                }
                return networkResponse;
            }).catch(() => {
                // Fallback offline logic if network goes completely dead
                return caches.match('/');
            });
        })
    );
});
