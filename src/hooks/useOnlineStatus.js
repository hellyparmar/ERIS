/**
 * Online/Offline Status Hook
 * Detects network connectivity and triggers sync when online
 */

import { useState, useEffect } from 'react';

export function useOnlineStatus() {
    const [isOnline, setIsOnline] = useState(navigator.onLine);
    const [wasOffline, setWasOffline] = useState(false);

    useEffect(() => {
        const handleOnline = () => {
            console.log('[Network] Connection restored');
            setIsOnline(true);

            // Trigger background sync if we were offline
            if (wasOffline) {
                triggerBackgroundSync();
                setWasOffline(false);
                showNotification('Back Online', 'Syncing your data...');
            }
        };

        const handleOffline = () => {
            console.log('[Network] Connection lost');
            setIsOnline(false);
            setWasOffline(true);
            showNotification('Offline Mode', 'Working offline. Changes will sync when connection is restored.');
        };

        // Add event listeners
        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        // Periodic connectivity check
        const intervalId = setInterval(() => {
            const currentStatus = navigator.onLine;
            if (currentStatus !== isOnline) {
                setIsOnline(currentStatus);
            }
        }, 30000); // Check every 30 seconds

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
            clearInterval(intervalId);
        };
    }, [isOnline, wasOffline]);

    return isOnline;
}

/**
 * Trigger background sync
 */
function triggerBackgroundSync() {
    if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
        navigator.serviceWorker.ready.then((registration) => {
            return registration.sync.register('sync-all');
        }).then(() => {
            console.log('[Sync] Background sync registered');
        }).catch((err) => {
            console.error('[Sync] Background sync failed:', err);
        });
    }

/**
 * Show browser notification
 */
function showNotification(title, body) {
    if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, {
            body,
            icon: '/logo192.png',
            badge: '/badge-72x72.png'
        });
    }

/**
 * Request notification permission
 */
export function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then((permission) => {
            console.log('[Notification] Permission:', permission);
        });
    }
