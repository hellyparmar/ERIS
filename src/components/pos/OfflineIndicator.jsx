import { useState, useEffect } from 'react';

export default function OfflineIndicator() {
    const [isOnline, setIsOnline] = useState(navigator.onLine);
    const [queuedCount, setQueuedCount] = useState(0);

    useEffect(() => {
        const handleOnline = () => setIsOnline(true);
        const handleOffline = () => setIsOnline(false);

        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        // Check IndexedDB for queued transactions
        const checkQueue = async () => {
            try {
                const db = await openDB();
                const tx = db.transaction('offline_transactions', 'readonly');
                const store = tx.objectStore('offline_transactions');
                const count = await store.count();
                setQueuedCount(count);
            } catch (err) {
                console.error('Failed to check offline queue:', err);
            }
        };

        checkQueue();
        const interval = setInterval(checkQueue, 5000); // Check every 5s

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
            clearInterval(interval);
        };
    }, []);

    // Auto-sync when coming back online
    useEffect(() => {
        if (isOnline && queuedCount > 0) {
            syncOfflineTransactions();
        }
    }, [isOnline, queuedCount]);

    const openDB = () => {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('pos_offline_db', 1);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('offline_transactions')) {
                    db.createObjectStore('offline_transactions', { keyPath: 'client_transaction_id' });
                }
            };
        });
    };

    const syncOfflineTransactions = async () => {
        try {
            const db = await openDB();
            const tx = db.transaction('offline_transactions', 'readonly');
            const store = tx.objectStore('offline_transactions');
            const transactions = await store.getAll();

            if (transactions.length === 0) return;

            const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await fetch(`${API_BASE}/offline/sync`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ transactions })
            });

            if (response.ok) {
                const result = await response.json();

                // Remove successfully synced transactions
                const deleteTx = db.transaction('offline_transactions', 'readwrite');
                const deleteStore = deleteTx.objectStore('offline_transactions');

                for (const txn of result.results) {
                    if (txn.status === 'success') {
                        await deleteStore.delete(txn.client_transaction_id);
                    }
                }

                console.log(`✅ Synced ${result.successful}/${result.total} offline transactions`);
                setQueuedCount(result.failed);
            }
        } catch (err) {
            console.error('Offline sync failed:', err);
        }
    };

    if (isOnline && queuedCount === 0) {
        return null; // Don't show indicator when online with no queue
    }

    return (
        <div className={`fixed bottom-4 right-4 px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 ${isOnline ? 'bg-green-500' : 'bg-orange-500'
            } text-white`}>
            <div className={`w-2 h-2 rounded-full ${isOnline ? 'bg-white' : 'bg-white animate-pulse'
                }`} />
            <span className="text-sm font-medium">
                {isOnline
                    ? queuedCount > 0 ? `Syncing ${queuedCount} transactions...` : 'Online'
                    : `Offline — ${queuedCount} queued`
                }
            </span>
        </div>
    );
}
