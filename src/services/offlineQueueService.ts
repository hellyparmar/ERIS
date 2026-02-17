/**
 * Offline Transaction Queue Service
 * Stores transactions in IndexedDB when offline
 * Syncs with backend when connectivity restored
 */

interface OfflineTransaction {
  id: string;
  timestamp: number;
  type: 'sale' | 'refund' | 'adjustment';
  items: any[];
  total_amount: number;
  payment_method: string;
  customer_id?: number;
  status: 'pending' | 'synced' | 'failed';
  retry_count: number;
  error_message?: string;
}

interface SyncResponse {
  success: boolean;
  synced: OfflineTransaction[];
  failed: OfflineTransaction[];
  errors: Array<{ transaction_id: string; error: string }>;
}

class OfflineQueueService {
  private dbName = 'rdios_offline';
  private storeName = 'transactions';
  private db: IDBDatabase | null = null;
  private isOnline = navigator.onLine;
  private syncInProgress = false;
  private maxRetries = 3;
  private retryDelay = 5000; // 5 seconds

  constructor() {
    this.initializeDB();
    this.setupNetworkListener();
  }

  /**
   * Initialize IndexedDB database
   */
  private async initializeDB(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);

      request.onerror = () => {
        console.error('Failed to open IndexedDB');
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        console.log('✓ Offline queue database initialized');
        resolve();
      };

      request.onupgradeneeded = (event: any) => {
        const db = event.target.result;
        if (!db.objectStoreNames.contains(this.storeName)) {
          const store = db.createObjectStore(this.storeName, { keyPath: 'id' });
          store.createIndex('status', 'status', { unique: false });
          store.createIndex('timestamp', 'timestamp', { unique: false });
          console.log('✓ Created transactions object store');
        }
      };
    });
  }

  /**
   * Setup network connectivity listener
   */
  private setupNetworkListener(): void {
    window.addEventListener('online', () => {
      console.log('✓ Network restored');
      this.isOnline = true;
      this.syncPendingTransactions();
    });

    window.addEventListener('offline', () => {
      console.warn('✗ Network disconnected - switching to offline mode');
      this.isOnline = false;
    });
  }

  /**
   * Queue a transaction for offline storage
   */
  async queueTransaction(transaction: Omit<OfflineTransaction, 'id' | 'status' | 'retry_count'>): Promise<string> {
    if (!this.db) {
      await this.initializeDB();
    }

    const id = `TXN-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const offlineTransaction: OfflineTransaction = {
      ...transaction,
      id,
      status: 'pending',
      retry_count: 0,
    };

    return new Promise((resolve, reject) => {
      const transaction_db = this.db!.transaction([this.storeName], 'readwrite');
      const store = transaction_db.objectStore(this.storeName);
      const request = store.add(offlineTransaction);

      request.onerror = () => {
        console.error('Failed to queue transaction');
        reject(request.error);
      };

      request.onsuccess = () => {
        console.log(`✓ Transaction queued: ${id}`);
        resolve(id);
      };
    });
  }

  /**
   * Get all pending transactions
   */
  async getPendingTransactions(): Promise<OfflineTransaction[]> {
    if (!this.db) {
      await this.initializeDB();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], 'readonly');
      const store = transaction.objectStore(this.storeName);
      const index = store.index('status');
      const request = index.getAll('pending');

      request.onerror = () => {
        reject(request.error);
      };

      request.onsuccess = () => {
        resolve(request.result);
      };
    });
  }

  /**
   * Sync pending transactions with backend
   */
  async syncPendingTransactions(): Promise<SyncResponse> {
    if (this.syncInProgress || !this.isOnline) {
      return { success: false, synced: [], failed: [], errors: [] };
    }

    this.syncInProgress = true;

    try {
      const pendingTransactions = await this.getPendingTransactions();

      if (pendingTransactions.length === 0) {
        console.log('✓ No pending transactions to sync');
        return { success: true, synced: [], failed: [], errors: [] };
      }

      console.log(`Syncing ${pendingTransactions.length} transactions...`);

      const response = await fetch('/api/v1/pos/sync-offline', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({ transactions: pendingTransactions }),
      });

      if (!response.ok) {
        throw new Error(`Sync failed: ${response.statusText}`);
      }

      const result: SyncResponse = await response.json();

      // Update transaction statuses
      for (const synced of result.synced) {
        await this.updateTransactionStatus(synced.id, 'synced');
      }

      for (const error of result.errors) {
        const txn = pendingTransactions.find(t => t.id === error.transaction_id);
        if (txn) {
          txn.retry_count++;
          if (txn.retry_count >= this.maxRetries) {
            await this.updateTransactionStatus(error.transaction_id, 'failed', error.error);
          }
        }
      }

      console.log(`✓ Synced: ${result.synced.length}, Failed: ${result.failed.length}`);
      return result;
    } catch (error) {
      console.error('Sync error:', error);
      return {
        success: false,
        synced: [],
        failed: [],
        errors: [{ transaction_id: 'all', error: String(error) }],
      };
    } finally {
      this.syncInProgress = false;

      // Schedule retry if there are still pending transactions
      const remaining = await this.getPendingTransactions();
      if (remaining.length > 0 && this.isOnline) {
        setTimeout(() => this.syncPendingTransactions(), this.retryDelay);
      }
    }
  }

  /**
   * Update transaction status
   */
  private async updateTransactionStatus(
    id: string,
    status: 'synced' | 'failed',
    errorMessage?: string
  ): Promise<void> {
    if (!this.db) {
      await this.initializeDB();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      const request = store.get(id);

      request.onerror = () => {
        reject(request.error);
      };

      request.onsuccess = () => {
        const txn = request.result;
        if (txn) {
          txn.status = status;
          if (errorMessage) {
            txn.error_message = errorMessage;
          }
          store.put(txn);
          resolve();
        }
      };
    });
  }

  /**
   * Clear all synced transactions
   */
  async clearSyncedTransactions(): Promise<void> {
    if (!this.db) {
      await this.initializeDB();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], 'readwrite');
      const store = transaction.objectStore(this.storeName);
      const index = store.index('status');
      const request = index.getAll('synced');

      request.onerror = () => {
        reject(request.error);
      };

      request.onsuccess = () => {
        for (const txn of request.result) {
          store.delete(txn.id);
        }
        console.log('✓ Cleared synced transactions');
        resolve();
      };
    });
  }

  /**
   * Get queue statistics
   */
  async getQueueStats(): Promise<{ pending: number; failed: number; total: number }> {
    if (!this.db) {
      await this.initializeDB();
    }

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.storeName], 'readonly');
      const store = transaction.objectStore(this.storeName);
      const request = store.getAll();

      request.onerror = () => {
        reject(request.error);
      };

      request.onsuccess = () => {
        const transactions = request.result;
        const pending = transactions.filter(t => t.status === 'pending').length;
        const failed = transactions.filter(t => t.status === 'failed').length;
        resolve({ pending, failed, total: transactions.length });
      };
    });
  }

  /**
   * Check if currently online
   */
  isConnected(): boolean {
    return this.isOnline;
  }

  /**
   * Manually trigger sync
   */
  async manualSync(): Promise<SyncResponse> {
    if (!this.isOnline) {
      console.warn('Cannot sync - device is offline');
      return { success: false, synced: [], failed: [], errors: [] };
    }
    return this.syncPendingTransactions();
  }
}

// Export singleton instance
export const offlineQueueService = new OfflineQueueService();
