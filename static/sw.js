const CACHE_NAME = 'futamigo-v2-hotfix';
const urlsToCache = [
    '/',
    '/static/futfavi.webp',
    '/static/futamigo-preview.png'
];

// Evento de instalação
self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                // Cache apenas recursos básicos para evitar conflitos
                return cache.addAll(['/']).catch(function(error) {
                    // Erro silencioso
                });
            })
    );
    // Ativa imediatamente o novo service worker
    self.skipWaiting();
});

// Evento de fetch para interceptar requisições
self.addEventListener('fetch', function(event) {
    // Só intercepta requisições GET para recursos estáticos
    if (event.request.method !== 'GET') {
        return;
    }
    
    // Não intercepta requisições críticas que precisam ser atuais
    if (event.request.url.includes('/login/') || 
        event.request.url.includes('/logout/') || 
        event.request.url.includes('/admin/') ||
        event.request.url.includes('/offline/') || // IMPORTANTE: não interceptar página offline
        event.request.url.includes('/manifest.json') || // não interceptar manifest
        event.request.url.includes('/sw.js') || // não interceptar o próprio SW
        event.request.url.includes('api/') ||
        event.request.url.includes('/perfil/') ||
        event.request.url.includes('/palpites/') ||
        event.request.url.includes('/classificacao/') ||
        event.request.url.includes('?') || // URLs com parâmetros
        event.request.headers.get('X-Requested-With') === 'XMLHttpRequest') { // AJAX
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                // Cache hit - return response
                if (response) {
                    return response;
                }
                
                // Fazer requisição normal
                return fetch(event.request).catch(function() {
                    // Se falhar, retorna página offline básica apenas para navegação principal
                    if (event.request.destination === 'document') {
                        return caches.match('/');
                    }
                });
            })
    );
});

// Evento de ativação - limpar caches antigos
self.addEventListener('activate', function(event) {
    var cacheWhitelist = [CACHE_NAME];

    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            // Toma controle imediatamente de todas as páginas
            return self.clients.claim();
        })
    );
});

// Evento para lidar com sincronização em background
self.addEventListener('sync', function(event) {
    if (event.tag === 'futamigo-sync') {
        // Lógica de sincronização futura
    }
});

// Evento para lidar com notificações push (preparado para futuro)
self.addEventListener('push', function(event) {
    
    let notificationData = {
        title: 'FutAmigo',
        body: 'Nova notificação do seu bolão!',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-72x72.png',
        tag: 'futamigo-notification',
        vibrate: [200, 100, 200],
        data: {
            url: '/',
            timestamp: Date.now()
        },
        actions: [
            {
                action: 'view',
                title: 'Ver Agora',
                icon: '/static/icons/icon-72x72.png'
            }
        ],
        // Configurações específicas para mobile
        requireInteraction: false,
        silent: false,
        renotify: true
    };
    
    // Se há dados no push, usar eles
    if (event.data) {
        try {
            const pushData = event.data.json();
            notificationData = {
                ...notificationData,
                ...pushData
            };
        } catch (e) {
            notificationData.body = event.data.text();
        }
    }
    
    // Mostrar notificação
    event.waitUntil(
        self.registration.showNotification(notificationData.title, notificationData)
    );
});

// Evento para lidar com cliques em notificações
self.addEventListener('notificationclick', function(event) {
    event.notification.close();

    const urlToOpen = event.notification.data?.url || '/';
    
    // Abrir ou focar na aplicação
    event.waitUntil(
        clients.matchAll({type: 'window', includeUncontrolled: true})
            .then(function(clientList) {
                // Se já tem uma janela aberta, focar nela
                for (let client of clientList) {
                    if (client.url === urlToOpen && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                // Senão, abrir nova janela
                if (clients.openWindow) {
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});