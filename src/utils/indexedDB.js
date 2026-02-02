/**
 * IndexedDB Wrapper for Offline Data Storage
 * Provides a simple API for storing and retrieving data offline
 */

const DB_NAME = 'rdios-offline';
const DB_VERSION = 1;

// Object store names
export const STORES = {
    PRODUCTS: 'products',
    CUSTOMERS: 'customers',
    PENDING_INVOICES: 'pending_invoices',
    PENDING_PAYMENTS: 'pending_payments',
    SYNC_QUEUE: 'sync_queue',
    INVENTORY_UPDATES: 'inventory_updates',
    ORGANIZATIONS: 'organizations',
    STORES: 'stores'
};

/**
 * IndexedDB Database Class
 */
class OfflineDB {
    constructor() {
        this.db = null;
        this.dbPromise = null;
    }

    /**
     * Open database connection
     */
    async open() {
        if (this.db) {
            return this.db;
        }

        if (this.dbPromise) {
            return this.dbPromise;
        }

        this.dbPromise = new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onerror = () => {
                console.error('[IndexedDB] Failed to open:', request.error);
                reject(request.error);
            };

            request.onsuccess = () => {
                console.log('[IndexedDB] Opened successfully');
                this.db = request.result;
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                console.log('[IndexedDB] Upgrading schema...');
                const db = event.target.result;

                // Products store
                if (!db.objectStoreNames.contains(STORES.PRODUCTS)) {
                    const productsStore = db.createObjectStore(STORES.PRODUCTS, { keyPath: 'id' });
                    productsStore.createIndex('sku', 'sku', { unique: false });
                    productsStore.createIndex('name', 'name', { unique: false });
                    productsStore.createIndex('organization_id', 'organization_id', { unique: false });
                    productsStore.createIndex('store_id', 'store_id', { unique: false });
                }

                // Customers store
                if (!db.objectStoreNames.contains(STORES.CUSTOMERS)) {
                    const customersStore = db.createObjectStore(STORES.CUSTOMERS, { keyPath: 'id' });
                    customersStore.createIndex('phone', 'phone', { unique: false });
                    customersStore.createIndex('email', 'email', { unique: false });
                    customersStore.createIndex('organization_id', 'organization_id', { unique: false });
                }

                // Pending Invoices store
                if (!db.objectStoreNames.contains(STORES.PENDING_INVOICES)) {
                    const invoicesStore = db.createObjectStore(STORES.PENDING_INVOICES, { keyPath: 'local_id' });
                    invoicesStore.createIndex('created_at', 'created_at', { unique: false });
                    invoicesStore.createIndex('status', 'status', { unique: false });
                    invoicesStore.createIndex('organization_id', 'organization_id', { unique: false });
                    invoicesStore.createIndex('synced', 'synced', { unique: false });
                }

                // Pending Payments store
                if (!db.objectStoreNames.contains(STORES.PENDING_PAYMENTS)) {
                    const paymentsStore = db.createObjectStore(STORES.PENDING_PAYMENTS, { keyPath: 'local_id' });
                    paymentsStore.createIndex('created_at', 'created_at', { unique: false });
                    paymentsStore.createIndex('status', 'status', { unique: false });
                    paymentsStore.createIndex('synced', 'synced', { unique: false });
                }

                // Sync Queue store
                if (!db.objectStoreNames.contains(STORES.SYNC_QUEUE)) {
                    const queueStore = db.createObjectStore(STORES.SYNC_QUEUE, { keyPath: 'id', autoIncrement: true });
                    queueStore.createIndex('operation_type', 'operation_type', { unique: false });
                    queueStore.createIndex('status', 'status', { unique: false });
                    queueStore.createIndex('timestamp', 'timestamp', { unique: false });
                    queueStore.createIndex('retries', 'retries', { unique: false });
                }

                // Inventory Updates store
                if (!db.objectStoreNames.contains(STORES.INVENTORY_UPDATES)) {
                    const inventoryStore = db.createObjectStore(STORES.INVENTORY_UPDATES, { keyPath: 'local_id' });
                    inventoryStore.createIndex('product_id', 'product_id', { unique: false });
                    inventoryStore.createIndex('timestamp', 'timestamp', { unique: false });
                    inventoryStore.createIndex('synced', 'synced', { unique: false });
                }

                // Organizations store
                if (!db.objectStoreNames.contains(STORES.ORGANIZATIONS)) {
                    db.createObjectStore(STORES.ORGANIZATIONS, { keyPath: 'id' });
                }

                // Stores store
                if (!db.objectStoreNames.contains(STORES.STORES)) {
                    const storesStore = db.createObjectStore(STORES.STORES, { keyPath: 'id' });
                    storesStore.createIndex('organization_id', 'organization_id', { unique: false });
                }
            };
        });

        return this.dbPromise;
    }

    /**
     * Close database connection
     */
    async close() {
        if (this.db) {
            this.db.close();
            this.db = null;
            this.dbPromise = null;
        }
    }

    /**
     * Get a single item by key
     */
    async get(storeName, key) {
        const db = await this.open();

        return new Promise((resolve, reject) => {
            const transaction = db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.get(key);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get all items from a store
     */
    async getAll(storeName, query, count) {
        const db = await this.open();

        return new Promise((resolve, reject) => {
            const transaction = db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.getAll(query, count);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Query items by index
     */
    async query(storeName, indexName, value) {
        const db = await this.open();

        return new Promise((resolve, reject) => {
            const transaction = db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const index = store.index(indexName);
            const request = index.getAll(value);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Put (add or update) an item
     */
    async put(storeName, data) {
        const db = await this.open();

        return new Promise((resolve, reject) => {
            const transaction = db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.put(data);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Add an item (fails if key exists)
     */
    async add(storeName, data) {
        const db = await this.open();

        return new Promise((resolve, reject) => {
            const transaction = db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.add(data);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Delete an item by key
     */
    async delete(storeName, key) {
        const db = await this.open();

        return new Promise((resolve, reject) => {
            const transaction = db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.delete(key);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Clear all items from a store
     */
    async clear(storeName) {
        const db = await this.open();

        return new Promise((resolve, reject) => {
            const transaction = db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.clear();

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Count items in a store
     */
    async count(storeName, query) {
        const db = await this.open();

        return new Promise((resolve, reject) => {
            const transaction = db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.count(query);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Execute a transaction with multiple operations
     */
    async transaction(storeNames, mode, callback) {
        const db = await this.open();

        return new Promise((resolve, reject) => {
            const transaction = db.transaction(storeNames, mode);

            transaction.oncomplete = () => resolve();
            transaction.onerror = () => reject(transaction.error);
            transaction.onabort = () => reject(new Error('Transaction aborted'));

            try {
                callback(transaction);
            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Bulk insert items
     */
    async bulkPut(storeName, items) {
        const db = await this.open();

        return new Promise((resolve, reject) => {
            const transaction = db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);

            let completed = 0;
            const total = items.length;

            items.forEach((item) => {
                const request = store.put(item);

                request.onsuccess = () => {
                    completed++;
                    if (completed === total) {
                        resolve(completed);
                    }
                };

                request.onerror = () => {
                    console.error('[IndexedDB] Bulk put error:', request.error);
                };
            });

            transaction.onerror = () => reject(transaction.error);
        });
    }
}

// Export singleton instance
export const offlineDB = new OfflineDB();

// Export class for testing
export { OfflineDB };
