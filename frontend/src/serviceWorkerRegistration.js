/**
 * Service Worker Registration
 * Registers the service worker and handles updates
 */

export function register(config) {
    if ('serviceWorker' in navigator) {
        // Wait for page load
        window.addEventListener('load', () => {
            const swUrl = `/service-worker.js`;

            registerValidSW(swUrl, config);
        });
    }

function registerValidSW(swUrl, config) {
    navigator.serviceWorker
        .register(swUrl)
        .then((registration) => {
            console.log('[SW] Registered successfully:', registration.scope);

            // Handle updates
            registration.onupdatefound = () => {
                const installingWorker = registration.installing;

                if (installingWorker == null) {
                    return;
                }

                installingWorker.onstatechange = () => {
                    if (installingWorker.state === 'installed') {
                        if (navigator.serviceWorker.controller) {
                            // New update available
                            console.log('[SW] New content available; please refresh.');

                            // Show update notification
                            if (config && config.onUpdate) {
                                config.onUpdate(registration);
                            }
                        } else {
                            // Content cached for offline use
                            console.log('[SW] Content cached for offline use.');

                            if (config && config.onSuccess) {
                                config.onSuccess(registration);
                            }
                    }
                };
            };
        })
        .catch((error) => {
            console.error('[SW] Registration failed:', error);
        });
}

export function unregister() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready
            .then((registration) => {
                registration.unregister();
            })
            .catch((error) => {
                console.error(error.message);
            });
    }

/**
 * Check if service worker is updated
 */
export function checkForUpdates() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.ready.then((registration) => {
            registration.update();
        });
    }

/**
 * Skip waiting and activate new service worker immediately
 */
export function skipWaiting() {
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
        navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
    }
