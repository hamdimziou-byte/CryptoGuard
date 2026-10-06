// CryptoGuard Service Worker
// Version 1.0.0

const CACHE_NAME = 'cryptoguard-v1';

self.addEventListener('install', function(event) {
    console.log('[Service Worker] Installing...');
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    console.log('[Service Worker] Activating...');
    event.waitUntil(clients.claim());
});

self.addEventListener('push', function(event) {
    console.log('[Service Worker] Push received:', event);
    
    let data = { title: '🛡️ CryptoGuard', body: 'Nouvelle alerte!' };
    
    if (event.data) {
        try {
            data = event.data.json();
        } catch (e) {
            data.body = event.data.text();
        }
    }
    
    const options = {
        body: data.body || '',
        icon: '/static/icon-192.png',
        badge: '/static/icon-72.png',
        vibrate: [200, 100, 200],
        data: { url: data.url || '/' },
        actions: [
            { action: 'open', title: '📊 Voir' },
            { action: 'close', title: 'Fermer' }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title || '🛡️ CryptoGuard', options)
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    if (event.action === 'close') return;
    
    const url = event.notification.data.url || '/';
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(function(windowClients) {
            for (let client of windowClients) {
                if (client.url === url && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});