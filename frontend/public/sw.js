// Service Worker for Trading ETF PWA
const CACHE_NAME = 'trading-etf-v1';
const API_CACHE_NAME = 'trading-etf-api-v1';

// Static assets to cache
const STATIC_ASSETS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json'
];

// API endpoints to cache
const API_ENDPOINTS = [
  '/api/v1/market/etfs',
  '/api/v1/signals/active',
  '/api/v1/user/profile'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        self.clients.claim();
      })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      caches.open(API_CACHE_NAME)
        .then((cache) => {
          return fetch(request)
            .then((response) => {
              // Cache successful GET requests
              if (request.method === 'GET' && response.status === 200) {
                cache.put(request, response.clone());
              }
              return response;
            })
            .catch(() => {
              // Return cached response if network fails
              return cache.match(request);
            });
        })
    );
    return;
  }

  // Handle static assets
  event.respondWith(
    caches.match(request)
      .then((response) => {
        // Return cached version or fetch from network
        return response || fetch(request);
      })
      .catch(() => {
        // Fallback for navigation requests
        if (request.mode === 'navigate') {
          return caches.match('/');
        }
      })
  );
});

// Push notification handling
self.addEventListener('push', (event) => {
  if (!event.data) return;

  const data = event.data.json();
  const options = {
    body: data.body,
    icon: '/logo192.png',
    badge: '/logo192.png',
    vibrate: [200, 100, 200],
    data: {
      url: data.url || '/',
      signal_id: data.signal_id
    },
    actions: [
      {
        action: 'view',
        title: 'View Signal',
        icon: '/logo192.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  if (event.action === 'dismiss') {
    return;
  }

  const urlToOpen = event.notification.data.url || '/';

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if there's already a window/tab open with the target URL
        for (const client of clientList) {
          if (client.url === urlToOpen && 'focus' in client) {
            return client.focus();
          }
        }
        // Open new window/tab
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
  );
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('Background sync triggered:', event.tag);

  if (event.tag === 'signals-sync') {
    event.waitUntil(syncSignals());
  } else if (event.tag === 'market-data-sync') {
    event.waitUntil(syncMarketData());
  } else if (event.tag === 'background-sync') {
    event.waitUntil(Promise.resolve());
  }
});

// Fonction pour synchroniser les signaux
async function syncSignals() {
  try {
    console.log('Syncing signals in background...');
    
    const response = await fetch('/api/v1/signals/advanced?limit=10');
    if (response.ok) {
      const signals = await response.json();
      
      // Vérifier s'il y a de nouveaux signaux avec une confiance élevée
      const highConfidenceSignals = signals.filter(signal => 
        signal.confidence > 80 && 
        (signal.signal_type === 'BUY' || signal.signal_type === 'SELL')
      );

      // Envoyer une notification pour les signaux importants
      for (const signal of highConfidenceSignals) {
        const title = `Signal ${signal.signal_type} Fort!`;
        const body = `${signal.etf_name}: ${signal.signal_type} (Confiance: ${signal.confidence.toFixed(0)}%)`;
        
        await self.registration.showNotification(title, {
          body: body,
          icon: '/logo192.png',
          badge: '/logo192.png',
          tag: `signal-${signal.id}`,
          requireInteraction: true,
          data: { 
            signal: signal,
            url: `/signals?highlight=${signal.id}`
          },
          actions: [
            {
              action: 'view',
              title: 'Voir le signal',
              icon: '/logo192.png'
            },
            {
              action: 'dismiss',
              title: 'Ignorer'
            }
          ]
        });
      }
    }
  } catch (error) {
    console.error('Error syncing signals:', error);
  }
}

// Fonction pour synchroniser les données de marché
async function syncMarketData() {
  try {
    console.log('Syncing market data in background...');
    
    // Synchroniser les ETFs principaux
    const etfs = ['FR0010296061', 'IE00B4L5Y983', 'LU0290358497'];
    
    for (const etfIsin of etfs) {
      try {
        const response = await fetch(`/api/v1/market-data/${etfIsin}?days=1`);
        if (response.ok) {
          const data = await response.json();
          // Les données sont automatiquement mises en cache par le fetch handler
        }
      } catch (error) {
        console.error(`Error syncing data for ${etfIsin}:`, error);
      }
    }
    
    return Promise.resolve();
  } catch (error) {
    console.error('Error syncing market data:', error);
  }
}

// Gestion périodique des données (si supporté)
if ('periodicSync' in self.registration) {
  self.addEventListener('periodicsync', (event) => {
    console.log('Periodic sync:', event.tag);

    if (event.tag === 'market-update') {
      event.waitUntil(syncMarketData());
    } else if (event.tag === 'signals-update') {
      event.waitUntil(syncSignals());
    }
  });
}

// Gestion des événements de connectivité
self.addEventListener('online', () => {
  console.log('Connection restored, syncing data...');
  syncSignals();
  syncMarketData();
});

self.addEventListener('offline', () => {
  console.log('Connection lost, entering offline mode...');
});

// Share target handling et messages améliorés
self.addEventListener('message', (event) => {
  console.log('SW received message:', event.data);

  if (event.data && event.data.type === 'SHARE_TARGET') {
    event.ports[0].postMessage({ success: true });
  }
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'SYNC_SIGNALS') {
    syncSignals();
  }
  
  if (event.data && event.data.type === 'SYNC_MARKET_DATA') {
    syncMarketData();
  }
  
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_NAME });
  }
});