// EMERGENCY: Force unregister all service workers
// This file will self-destruct after forcing browser to update

console.log('[EMERGENCY] Force unregistering all service workers...');

self.addEventListener('install', (event) => {
  console.log('[EMERGENCY] Killing old service worker...');
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('[EMERGENCY] Cleaning all caches...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          console.log('[EMERGENCY] Deleting cache:', cacheName);
          return caches.delete(cacheName);
        })
      );
    }).then(() => {
      console.log('[EMERGENCY] All caches deleted. Unregistering self...');
      return self.registration.unregister();
    }).then(() => {
      console.log('[EMERGENCY] Service worker unregistered. Reloading page...');
      return clients.matchAll({ type: 'window' });
    }).then((clients) => {
      clients.forEach((client) => {
        console.log('[EMERGENCY] Reloading client:', client.url);
        client.navigate(client.url);
      });
    })
  );
});

self.addEventListener('fetch', (event) => {
  // Pass through - no caching
  event.respondWith(fetch(event.request));
});
