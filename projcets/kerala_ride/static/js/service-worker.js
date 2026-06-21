const CACHE_NAME = 'keralaride-v4'; // Bumped cache version to force client update activation loops

// ⚡ Structural assets to bundle and cache immediately on first network boot configuration
const ASSETS_TO_CACHE = [
    '/',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/js/socket.js',
    'https://cdn.socket.io/4.7.2/socket.io.min.js',
    
    // 🗺️ CRITICAL MAP FIX: Cache external Leaflet assets directly on local device storage
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css',
    'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js'
];

// 1. Install Event: Cache core layouts instantly
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('📦 Service Worker: Pre-caching functional layout vector dependencies and map assets');
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
                        console.log('🧹 Service Worker: Clearing obsolete cache blocks completely');
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// 3. Intercept Requests: Cache-First Strategy for layouts, Network-First for APIs
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Skip intercepting live tracking WebSocket traffic or active database POST operations mutations
    if (url.pathname.startsWith('/socket.io') || event.request.method !== 'GET') {
        return;
    }

    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
                // Instantly return the file from phone memory cache storage (0ms layout render latency!)
                return cachedResponse;
            }

            // Otherwise, fetch it from the Render engine production deployment host environment normally
            return fetch(event.request).then((networkResponse) => {
                if (!networkResponse || networkResponse.status !== 200) {
                    return networkResponse;
                }

                // If it's a structural asset style or an OpenStreetMap/CartoDB layout tile asset, save a proxy copy safely
                const isStaticAsset = url.pathname.startsWith('/static/');
                const isLeafletCDNAsset = url.hostname.includes('cdnjs.cloudflare.com');
                // ⚡ FIX: Added cartocdn.com so your new premium map tiles cache correctly offline!
                const isMapTileAsset = url.hostname.includes('openstreetmap.org') || url.hostname.includes('cartocdn.com') || url.pathname.endsWith('.png');

                if (isStaticAsset || isLeafletCDNAsset || isMapTileAsset) {
                    return caches.open(CACHE_NAME).then((cache) => {
                        // Dynamically cache runtime resources to speed up future map loading states
                        cache.put(event.request, networkResponse.clone());
                        return networkResponse;
                    });
                }
                
                return networkResponse;
            }).catch(() => {
                // Fallback architecture resolution pipeline mapping layers if cellular signal is completely lost
                if (event.request.mode === 'navigate') {
                    return caches.match('/');
                }
                return null;
            });
        })
    );
});
