// Service Worker pour Medical Center - Diagnostic IA
// Version 1.0.0

const CACHE_NAME = 'medical-ai-v1.0.0';
const STATIC_CACHE_NAME = 'medical-ai-static-v1.0.0';
const DYNAMIC_CACHE_NAME = 'medical-ai-dynamic-v1.0.0';

// Fichiers à mettre en cache pour le fonctionnement hors ligne
const STATIC_FILES = [
  '/',
  '/static/manifest.json',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  // Note: Les fichiers Streamlit seront ajoutés dynamiquement
];

// Fichiers à ne jamais mettre en cache (pour la sécurité)
const NEVER_CACHE = [
  '/upload',
  '/api/predict',
  '/api/analyze',
  // Toute URL contenant des données sensibles
];

// Installation du Service Worker
self.addEventListener('install', event => {
  console.log('[SW] Installation en cours...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then(cache => {
        console.log('[SW] Mise en cache des fichiers statiques');
        return cache.addAll(STATIC_FILES);
      })
      .then(() => {
        console.log('[SW] Installation terminée');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('[SW] Erreur lors de l\'installation:', error);
      })
  );
});

// Activation du Service Worker
self.addEventListener('activate', event => {
  console.log('[SW] Activation en cours...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            // Supprimer les anciens caches
            if (cacheName !== STATIC_CACHE_NAME && 
                cacheName !== DYNAMIC_CACHE_NAME &&
                cacheName.startsWith('medical-ai-')) {
              console.log('[SW] Suppression de l\'ancien cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[SW] Activation terminée');
        return self.clients.claim();
      })
      .catch(error => {
        console.error('[SW] Erreur lors de l\'activation:', error);
      })
  );
});

// Interception des requêtes réseau
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);
  
  // Ne pas mettre en cache les requêtes sensibles
  if (shouldNeverCache(request)) {
    console.log('[SW] Requête sensible, pas de cache:', url.pathname);
    event.respondWith(fetch(request));
    return;
  }
  
  // Stratégie Cache First pour les fichiers statiques
  if (isStaticFile(request)) {
    event.respondWith(cacheFirst(request));
    return;
  }
  
  // Stratégie Network First pour les autres requêtes
  event.respondWith(networkFirst(request));
});

// Vérifier si une requête ne doit jamais être mise en cache
function shouldNeverCache(request) {
  const url = new URL(request.url);
  
  // Requêtes POST (upload de fichiers)
  if (request.method !== 'GET') {
    return true;
  }
  
  // URLs sensibles
  return NEVER_CACHE.some(pattern => url.pathname.includes(pattern));
}

// Vérifier si c'est un fichier statique
function isStaticFile(request) {
  const url = new URL(request.url);
  return url.pathname.startsWith('/static/') || 
         url.pathname.endsWith('.css') ||
         url.pathname.endsWith('.js') ||
         url.pathname.endsWith('.png') ||
         url.pathname.endsWith('.jpg') ||
         url.pathname.endsWith('.ico');
}

// Stratégie Cache First
async function cacheFirst(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('[SW] Réponse depuis le cache:', request.url);
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    
    // Mettre en cache la réponse si elle est valide
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
      console.log('[SW] Fichier mis en cache:', request.url);
    }
    
    return networkResponse;
  } catch (error) {
    console.error('[SW] Erreur Cache First:', error);
    
    // Retourner une réponse de fallback si disponible
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Page d'erreur hors ligne
    if (request.destination === 'document') {
      return new Response(getOfflinePage(), {
        headers: { 'Content-Type': 'text/html' }
      });
    }
    
    throw error;
  }
}

// Stratégie Network First
async function networkFirst(request) {
  try {
    const networkResponse = await fetch(request);
    
    // Mettre en cache les réponses valides (sauf les sensibles)
    if (networkResponse.ok && !shouldNeverCache(request)) {
      const cache = await caches.open(DYNAMIC_CACHE_NAME);
      cache.put(request, networkResponse.clone());
      console.log('[SW] Réponse mise en cache:', request.url);
    }
    
    return networkResponse;
  } catch (error) {
    console.log('[SW] Réseau indisponible, tentative depuis le cache:', request.url);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Page d'erreur hors ligne pour les documents
    if (request.destination === 'document') {
      return new Response(getOfflinePage(), {
        headers: { 'Content-Type': 'text/html' }
      });
    }
    
    throw error;
  }
}

// Page d'erreur hors ligne
function getOfflinePage() {
  return `
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Medical Center - Hors ligne</title>
        <style>
            body {
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .offline-container {
                background: white;
                border-radius: 16px;
                padding: 3rem;
                text-align: center;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
                max-width: 500px;
            }
            .offline-icon {
                font-size: 4rem;
                margin-bottom: 1rem;
            }
            .offline-title {
                font-size: 2rem;
                font-weight: 700;
                color: #4F46E5;
                margin-bottom: 1rem;
            }
            .offline-message {
                color: #64748B;
                line-height: 1.6;
                margin-bottom: 2rem;
            }
            .retry-button {
                background: #4F46E5;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.3s ease;
            }
            .retry-button:hover {
                background: #3730A3;
            }
        </style>
    </head>
    <body>
        <div class="offline-container">
            <div class="offline-icon">📱</div>
            <h1 class="offline-title">Mode Hors Ligne</h1>
            <p class="offline-message">
                Vous êtes actuellement hors ligne. Certaines fonctionnalités peuvent être limitées.
                <br><br>
                <strong>Note importante:</strong> L'analyse d'images nécessite une connexion internet 
                pour garantir la sécurité et la précision des diagnostics.
            </p>
            <button class="retry-button" onclick="window.location.reload()">
                🔄 Réessayer
            </button>
        </div>
    </body>
    </html>
  `;
}

// Gestion des messages du client
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CLEAR_CACHE') {
    clearAllCaches();
  }
});

// Nettoyer tous les caches
async function clearAllCaches() {
  try {
    const cacheNames = await caches.keys();
    await Promise.all(
      cacheNames.map(cacheName => {
        if (cacheName.startsWith('medical-ai-')) {
          console.log('[SW] Suppression du cache:', cacheName);
          return caches.delete(cacheName);
        }
      })
    );
    console.log('[SW] Tous les caches ont été supprimés');
  } catch (error) {
    console.error('[SW] Erreur lors de la suppression des caches:', error);
  }
}

// Notification de mise à jour
self.addEventListener('updatefound', () => {
  console.log('[SW] Mise à jour disponible');
});

console.log('[SW] Service Worker Medical AI chargé');

