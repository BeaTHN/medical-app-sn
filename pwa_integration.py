"""
Module d'intégration PWA pour l'application médicale Streamlit
Gestion du manifest, service worker et fonctionnalités hors ligne
"""

import streamlit as st
import json
import os
from pathlib import Path

def inject_pwa_components():
    """Injecte les composants PWA dans l'application Streamlit"""
    
    # Chemin vers les fichiers statiques
    static_dir = Path(__file__).parent / "static"
    
    # HTML pour l'intégration PWA
    pwa_html = f"""
    <script>
        // Configuration PWA
        const PWA_CONFIG = {{
            manifestPath: '/static/manifest.json',
            swPath: '/static/sw.js',
            enableNotifications: false,
            enableBackgroundSync: false
        }};
        
        // Vérification du support PWA
        function checkPWASupport() {{
            const support = {{
                serviceWorker: 'serviceWorker' in navigator,
                manifest: 'manifest' in document.createElement('link'),
                notifications: 'Notification' in window,
                pushManager: 'PushManager' in window
            }};
            
            console.log('Support PWA:', support);
            return support;
        }}
        
        // Installation du Service Worker
        async function installServiceWorker() {{
            if (!('serviceWorker' in navigator)) {{
                console.warn('Service Worker non supporté');
                return false;
            }}
            
            try {{
                const registration = await navigator.serviceWorker.register(PWA_CONFIG.swPath);
                console.log('Service Worker enregistré:', registration);
                
                // Écouter les mises à jour
                registration.addEventListener('updatefound', () => {{
                    console.log('Mise à jour du Service Worker disponible');
                    const newWorker = registration.installing;
                    
                    newWorker.addEventListener('statechange', () => {{
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {{
                            showUpdateNotification();
                        }}
                    }});
                }});
                
                return true;
            }} catch (error) {{
                console.error('Erreur lors de l\'enregistrement du Service Worker:', error);
                return false;
            }}
        }}
        
        // Afficher notification de mise à jour
        function showUpdateNotification() {{
            const notification = document.createElement('div');
            notification.innerHTML = `
                <div style="
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #4F46E5;
                    color: white;
                    padding: 1rem;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    z-index: 10000;
                    max-width: 300px;
                ">
                    <div style="font-weight: 600; margin-bottom: 0.5rem;">
                        🔄 Mise à jour disponible
                    </div>
                    <div style="font-size: 0.9rem; margin-bottom: 1rem;">
                        Une nouvelle version de l'application est disponible.
                    </div>
                    <button onclick="updateApp()" style="
                        background: white;
                        color: #4F46E5;
                        border: none;
                        padding: 0.5rem 1rem;
                        border-radius: 4px;
                        font-weight: 600;
                        cursor: pointer;
                        margin-right: 0.5rem;
                    ">
                        Mettre à jour
                    </button>
                    <button onclick="this.parentElement.parentElement.remove()" style="
                        background: transparent;
                        color: white;
                        border: 1px solid white;
                        padding: 0.5rem 1rem;
                        border-radius: 4px;
                        cursor: pointer;
                    ">
                        Plus tard
                    </button>
                </div>
            `;
            document.body.appendChild(notification);
        }}
        
        // Mettre à jour l'application
        function updateApp() {{
            if ('serviceWorker' in navigator) {{
                navigator.serviceWorker.getRegistration().then(registration => {{
                    if (registration && registration.waiting) {{
                        registration.waiting.postMessage({{ type: 'SKIP_WAITING' }});
                        window.location.reload();
                    }}
                }});
            }}
        }}
        
        // Gestion de l'installation PWA
        let deferredPrompt;
        
        window.addEventListener('beforeinstallprompt', (e) => {{
            console.log('Événement beforeinstallprompt déclenché');
            e.preventDefault();
            deferredPrompt = e;
            showInstallButton();
        }});
        
        function showInstallButton() {{
            // Vérifier si déjà installé
            if (window.matchMedia('(display-mode: standalone)').matches) {{
                console.log('Application déjà installée');
                return;
            }}
            
            const installButton = document.createElement('div');
            installButton.innerHTML = `
                <div id="pwa-install-banner" style="
                    position: fixed;
                    bottom: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: linear-gradient(135deg, #4F46E5, #7C3AED);
                    color: white;
                    padding: 1rem 1.5rem;
                    border-radius: 12px;
                    box-shadow: 0 8px 25px rgba(79, 70, 229, 0.3);
                    z-index: 10000;
                    display: flex;
                    align-items: center;
                    gap: 1rem;
                    max-width: 90vw;
                    animation: slideUp 0.3s ease-out;
                ">
                    <div style="font-size: 1.5rem;">📱</div>
                    <div>
                        <div style="font-weight: 600; margin-bottom: 0.25rem;">
                            Installer l'application
                        </div>
                        <div style="font-size: 0.9rem; opacity: 0.9;">
                            Accès rapide depuis votre écran d'accueil
                        </div>
                    </div>
                    <button onclick="installPWA()" style="
                        background: white;
                        color: #4F46E5;
                        border: none;
                        padding: 0.75rem 1.5rem;
                        border-radius: 8px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: transform 0.2s ease;
                    " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                        Installer
                    </button>
                    <button onclick="document.getElementById('pwa-install-banner').remove()" style="
                        background: transparent;
                        color: white;
                        border: none;
                        padding: 0.5rem;
                        cursor: pointer;
                        font-size: 1.2rem;
                    ">
                        ✕
                    </button>
                </div>
                <style>
                    @keyframes slideUp {{
                        from {{ transform: translateX(-50%) translateY(100%); opacity: 0; }}
                        to {{ transform: translateX(-50%) translateY(0); opacity: 1; }}
                    }}
                </style>
            `;
            document.body.appendChild(installButton);
        }}
        
        async function installPWA() {{
            if (!deferredPrompt) {{
                console.log('Prompt d\'installation non disponible');
                return;
            }}
            
            try {{
                deferredPrompt.prompt();
                const {{ outcome }} = await deferredPrompt.userChoice;
                
                if (outcome === 'accepted') {{
                    console.log('Installation acceptée');
                    document.getElementById('pwa-install-banner')?.remove();
                }} else {{
                    console.log('Installation refusée');
                }}
                
                deferredPrompt = null;
            }} catch (error) {{
                console.error('Erreur lors de l\'installation:', error);
            }}
        }}
        
        // Gestion du mode hors ligne
        function handleOnlineStatus() {{
            const updateOnlineStatus = () => {{
                const status = navigator.onLine ? 'en ligne' : 'hors ligne';
                console.log('Statut réseau:', status);
                
                if (!navigator.onLine) {{
                    showOfflineNotification();
                }} else {{
                    hideOfflineNotification();
                }}
            }};
            
            window.addEventListener('online', updateOnlineStatus);
            window.addEventListener('offline', updateOnlineStatus);
            updateOnlineStatus();
        }}
        
        function showOfflineNotification() {{
            if (document.getElementById('offline-notification')) return;
            
            const notification = document.createElement('div');
            notification.id = 'offline-notification';
            notification.innerHTML = `
                <div style="
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    background: #F59E0B;
                    color: white;
                    padding: 0.75rem;
                    text-align: center;
                    z-index: 10001;
                    font-weight: 600;
                ">
                    📡 Mode hors ligne - Fonctionnalités limitées
                </div>
            `;
            document.body.appendChild(notification);
            
            // Ajuster le padding du body
            document.body.style.paddingTop = '50px';
        }}
        
        function hideOfflineNotification() {{
            const notification = document.getElementById('offline-notification');
            if (notification) {{
                notification.remove();
                document.body.style.paddingTop = '0';
            }}
        }}
        
        // Initialisation PWA
        function initPWA() {{
            console.log('Initialisation PWA...');
            
            const support = checkPWASupport();
            
            if (support.serviceWorker) {{
                installServiceWorker();
            }}
            
            handleOnlineStatus();
            
            // Ajouter les meta tags pour PWA si manquants
            addPWAMetaTags();
            
            console.log('PWA initialisée');
        }}
        
        function addPWAMetaTags() {{
            const metaTags = [
                {{ name: 'mobile-web-app-capable', content: 'yes' }},
                {{ name: 'apple-mobile-web-app-capable', content: 'yes' }},
                {{ name: 'apple-mobile-web-app-status-bar-style', content: 'default' }},
                {{ name: 'apple-mobile-web-app-title', content: 'Medical AI' }},
                {{ name: 'application-name', content: 'Medical AI' }},
                {{ name: 'msapplication-TileColor', content: '#4F46E5' }},
                {{ name: 'theme-color', content: '#4F46E5' }}
            ];
            
            metaTags.forEach(tag => {{
                if (!document.querySelector(`meta[name="${{tag.name}}"]`)) {{
                    const meta = document.createElement('meta');
                    meta.name = tag.name;
                    meta.content = tag.content;
                    document.head.appendChild(meta);
                }}
            }});
            
            // Ajouter le lien vers le manifest si manquant
            if (!document.querySelector('link[rel="manifest"]')) {{
                const link = document.createElement('link');
                link.rel = 'manifest';
                link.href = PWA_CONFIG.manifestPath;
                document.head.appendChild(link);
            }}
        }}
        
        // Démarrer l'initialisation quand le DOM est prêt
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', initPWA);
        }} else {{
            initPWA();
        }}
        
        // Fonctions utilitaires pour Streamlit
        window.PWA = {{
            isInstalled: () => window.matchMedia('(display-mode: standalone)').matches,
            isOnline: () => navigator.onLine,
            clearCache: () => {{
                if ('serviceWorker' in navigator) {{
                    navigator.serviceWorker.getRegistration().then(registration => {{
                        if (registration && registration.active) {{
                            registration.active.postMessage({{ type: 'CLEAR_CACHE' }});
                        }}
                    }});
                }}
            }},
            checkForUpdates: () => {{
                if ('serviceWorker' in navigator) {{
                    navigator.serviceWorker.getRegistration().then(registration => {{
                        if (registration) {{
                            registration.update();
                        }}
                    }});
                }}
            }}
        }};
    </script>
    """
    
    # Injecter le HTML dans Streamlit
    st.components.v1.html(pwa_html, height=0)

def add_pwa_meta_tags():
    """Ajoute les meta tags PWA à l'application"""
    
    pwa_meta = """
    <link rel="manifest" href="/static/manifest.json">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="Medical AI">
    <meta name="application-name" content="Medical AI">
    <meta name="msapplication-TileColor" content="#4F46E5">
    <meta name="theme-color" content="#4F46E5">
    
    <!-- Icônes Apple -->
    <link rel="apple-touch-icon" sizes="152x152" href="/static/icons/icon-152x152.png">
    <link rel="apple-touch-icon" sizes="192x192" href="/static/icons/icon-192x192.png">
    
    <!-- Icônes Android -->
    <link rel="icon" type="image/png" sizes="192x192" href="/static/icons/icon-192x192.png">
    <link rel="icon" type="image/png" sizes="512x512" href="/static/icons/icon-512x512.png">
    
    <!-- Splash screens iOS -->
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="apple-touch-startup-image" href="/static/icons/icon-512x512.png">
    """
    
    st.markdown(pwa_meta, unsafe_allow_html=True)

def show_pwa_status():
    """Affiche le statut PWA dans l'interface"""
    
    status_html = """
    <div id="pwa-status" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 0.75rem;
        font-size: 0.8rem;
        color: #64748B;
        z-index: 1000;
        display: none;
    ">
        <div id="pwa-online-status">🟢 En ligne</div>
        <div id="pwa-install-status">📱 PWA prête</div>
    </div>
    
    <script>
        // Afficher le statut PWA en mode développement
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            document.getElementById('pwa-status').style.display = 'block';
            
            // Mettre à jour le statut en temps réel
            setInterval(() => {
                const onlineStatus = document.getElementById('pwa-online-status');
                const installStatus = document.getElementById('pwa-install-status');
                
                if (onlineStatus) {
                    onlineStatus.textContent = navigator.onLine ? '🟢 En ligne' : '🔴 Hors ligne';
                }
                
                if (installStatus && window.PWA) {
                    installStatus.textContent = window.PWA.isInstalled() ? '📱 Installée' : '📱 PWA prête';
                }
            }, 1000);
        }
    </script>
    """
    
    st.components.v1.html(status_html, height=0)

def create_offline_fallback():
    """Crée une page de fallback pour le mode hors ligne"""
    
    offline_html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Medical Center - Mode Hors Ligne</title>
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
            .container {
                background: white;
                border-radius: 16px;
                padding: 3rem;
                text-align: center;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
                max-width: 500px;
            }
            .icon {
                font-size: 4rem;
                margin-bottom: 1rem;
            }
            .title {
                font-size: 2rem;
                font-weight: 700;
                color: #4F46E5;
                margin-bottom: 1rem;
            }
            .message {
                color: #64748B;
                line-height: 1.6;
                margin-bottom: 2rem;
            }
            .button {
                background: #4F46E5;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.3s ease;
                margin: 0.5rem;
            }
            .button:hover {
                background: #3730A3;
            }
            .features {
                text-align: left;
                margin-top: 2rem;
                padding: 1rem;
                background: #F8FAFC;
                border-radius: 8px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="icon">📱</div>
            <h1 class="title">Mode Hors Ligne</h1>
            <p class="message">
                Vous utilisez actuellement l'application en mode hors ligne. 
                Certaines fonctionnalités sont limitées pour garantir la sécurité des données médicales.
            </p>
            
            <div class="features">
                <h3 style="color: #4F46E5; margin-top: 0;">Fonctionnalités disponibles hors ligne:</h3>
                <ul style="color: #64748B;">
                    <li>✅ Consultation des informations générales</li>
                    <li>✅ Lecture de la documentation</li>
                    <li>✅ Accès aux pages d'aide</li>
                </ul>
                
                <h3 style="color: #F59E0B;">Nécessite une connexion:</h3>
                <ul style="color: #64748B;">
                    <li>🔒 Analyse d'images médicales</li>
                    <li>🔒 Génération de rapports PDF</li>
                    <li>🔒 Envoi de formulaires de contact</li>
                </ul>
            </div>
            
            <button class="button" onclick="window.location.reload()">
                🔄 Vérifier la connexion
            </button>
            
            <button class="button" onclick="history.back()">
                ← Retour
            </button>
        </div>
        
        <script>
            // Vérifier périodiquement la connexion
            setInterval(() => {
                if (navigator.onLine) {
                    window.location.reload();
                }
            }, 5000);
        </script>
    </body>
    </html>
    """
    
    # Sauvegarder la page de fallback
    offline_path = Path(__file__).parent / "static" / "offline.html"
    with open(offline_path, 'w', encoding='utf-8') as f:
        f.write(offline_html)

def get_pwa_installation_guide():
    """Retourne le guide d'installation PWA"""
    
    return """
    ## 📱 Guide d'Installation PWA
    
    ### Sur Android (Chrome/Edge)
    1. Ouvrez l'application dans votre navigateur
    2. Appuyez sur le menu (⋮) en haut à droite
    3. Sélectionnez "Ajouter à l'écran d'accueil" ou "Installer l'application"
    4. Confirmez l'installation
    
    ### Sur iOS (Safari)
    1. Ouvrez l'application dans Safari
    2. Appuyez sur le bouton de partage (□↗)
    3. Faites défiler et sélectionnez "Sur l'écran d'accueil"
    4. Personnalisez le nom si souhaité et appuyez sur "Ajouter"
    
    ### Sur Desktop (Chrome/Edge/Firefox)
    1. Recherchez l'icône d'installation dans la barre d'adresse
    2. Cliquez sur l'icône ou utilisez le menu "Installer Medical AI"
    3. Confirmez l'installation dans la boîte de dialogue
    
    ### Avantages de l'installation
    - 🚀 Lancement rapide depuis l'écran d'accueil
    - 📱 Interface native sans barre de navigation
    - 🔄 Fonctionnement partiel hors ligne
    - 🔔 Notifications de mise à jour
    - 💾 Moins d'utilisation de données
    """

# Fonction principale d'intégration
def setup_pwa():
    """Configure tous les composants PWA"""
    
    # Créer la page de fallback hors ligne
    create_offline_fallback()
    
    # Ajouter les meta tags PWA
    add_pwa_meta_tags()
    
    # Injecter les composants JavaScript
    inject_pwa_components()
    
    # Afficher le statut en mode développement
    show_pwa_status()

