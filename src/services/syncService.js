/**
 * Data Sync Service
 * Coordinates synchronization between local and remote data
 */

import { offlineDB, STORES } from '../utils/indexedDB';
import { offlineQueue } from './offlineQueue';

class SyncService {
    constructor() {
        this.isSyncing = false;
        this.lastSyncTime = null;
    }

    /**
     * Preload data when online
     * Called after login or when connection is restored
     */
    async preloadData(apiClient, organizationId, storeId) {
        console.log('[Sync] Preloading data for offline use...');

        try {
            const results = {
                products: 0,
                customers: 0,
                organizations: 0,
                stores: 0
            };

            // Fetch and cache products
            const productsResponse = await apiClient.get(`/api/v1/products?organization_id=${organizationId}&store_id=${storeId}`);
            if (productsResponse.data) {
                await offlineDB.bulkPut(STORES.PRODUCTS, productsResponse.data);
                results.products = productsResponse.data.length;
            }

            // Fetch and cache customers
            const customersResponse = await apiClient.get(`/api/v1/customers?organization_id=${organizationId}`);
            if (customersResponse.data) {
                await offlineDB.bulkPut(STORES.CUSTOMERS, customersResponse.data);
                results.customers = customersResponse.data.length;
            }

            // Fetch and cache organization
            const orgResponse = await apiClient.get(`/api/v1/organizations/${organizationId}`);
            if (orgResponse.data) {
                await offlineDB.put(STORES.ORGANIZATIONS, orgResponse.data);
                results.organizations = 1;
            }

            // Fetch and cache stores
            const storesResponse = await apiClient.get(`/api/v1/stores?organization_id=${organizationId}`);
            if (storesResponse.data) {
                await offlineDB.bulkPut(STORES.STORES, storesResponse.data);
                results.stores = storesResponse.data.length;
            }

            console.log('[Sync] Preload complete:', results);
            this.lastSyncTime = new Date().toISOString();

            return results;
        } catch (error) {
            console.error('[Sync] Preload failed:', error);
            throw error;
        }

    /**
     * Sync all pending data to server
     */
    async syncAll(apiClient) {
        if (this.isSyncing) {
            console.log('[Sync] Sync already in progress');
            return { inProgress: true };
        }

        this.isSyncing = true;
        console.log('[Sync] Starting full sync...');

        try {
            const results = {
                queue_results: null,
                refreshed_data: null
            };

            // 1. Process sync queue
            results.queue_results = await offlineQueue.processQueue(apiClient);

            // 2. Refresh cached data (products, customers)
            // Get current organization/store from app context
            const currentOrg = await this.getCurrentOrganization();
            const currentStore = await this.getCurrentStore();

            if (currentOrg && currentStore) {
                results.refreshed_data = await this.preloadData(
                    apiClient,
                    currentOrg.id,
                    currentStore.id
                );
            }

            this.lastSyncTime = new Date().toISOString();
            console.log('[Sync] Full sync complete:', results);

            return results;
        } catch (error) {
            console.error('[Sync] Sync failed:', error);
            throw error;
        } finally {
            this.isSyncing = false;
        }

    /**
     * Sync specific type of data
     */
    async syncByType(type, apiClient) {
        console.log(`[Sync] Syncing ${type}...`);

        try {
            switch (type) {
                case 'invoices':
                    return await this.syncInvoices(apiClient);

                case 'payments':
                    return await this.syncPayments(apiClient);

                case 'inventory':
                    return await this.syncInventory(apiClient);

                default:
                    throw new Error(`Unknown sync type: ${type}`);
            }
        } catch (error) {
            console.error(`[Sync] Failed to sync ${type}:`, error);
            throw error;
        }

    /**
     * Sync pending invoices
     */
    async syncInvoices(apiClient) {
        const pending = await offlineDB.query(STORES.PENDING_INVOICES, 'synced', false);
        const results = { total: pending.length, synced: 0, failed: 0 };

        for (const invoice of pending) {
            try {
                const response = await apiClient.post('/api/v1/invoices', invoice);

                // Update with server ID
                await offlineDB.put(STORES.PENDING_INVOICES, {
                    ...invoice,
                    server_id: response.id,
                    synced: true,
                    synced_at: new Date().toISOString()
                });

                results.synced++;
            } catch (error) {
                console.error('[Sync] Invoice sync failed:', error);
                results.failed++;
            }

        return results;
    }

    /**
     * Sync pending payments
     */
    async syncPayments(apiClient) {
        const pending = await offlineDB.query(STORES.PENDING_PAYMENTS, 'synced', false);
        const results = { total: pending.length, synced: 0, failed: 0 };

        for (const payment of pending) {
            try {
                const response = await apiClient.post('/api/v1/payments', payment);

                await offlineDB.put(STORES.PENDING_PAYMENTS, {
                    ...payment,
                    server_id: response.id,
                    synced: true,
                    synced_at: new Date().toISOString()
                });

                results.synced++;
            } catch (error) {
                console.error('[Sync] Payment sync failed:', error);
                results.failed++;
            }

        return results;
    }

    /**
     * Sync inventory updates
     */
    async syncInventory(apiClient) {
        const pending = await offlineDB.query(STORES.INVENTORY_UPDATES, 'synced', false);
        const results = { total: pending.length, synced: 0, failed: 0 };

        for (const update of pending) {
            try {
                await apiClient.put(`/api/v1/inventory/${update.product_id}`, update);

                // Remove from pending updates
                await offlineDB.delete(STORES.INVENTORY_UPDATES, update.local_id);

                results.synced++;
            } catch (error) {
                console.error('[Sync] Inventory sync failed:', error);
                results.failed++;
            }

        return results;
    }

    /**
     * Get current organization from cache
     */
    async getCurrentOrganization() {
        try {
            const orgs = await offlineDB.getAll(STORES.ORGANIZATIONS);
            return orgs[0] || null; // Return first org (for demo)
        } catch (error) {
            console.error('[Sync] Failed to get current org:', error);
            return null;
        }

    /**
     * Get current store from cache
     */
    async getCurrentStore() {
        try {
            const stores = await offlineDB.getAll(STORES.STORES);
            return stores[0] || null; // Return first store (for demo)
        } catch (error) {
            console.error('[Sync] Failed to get current store:', error);
            return null;
        }

    /**
     * Get sync status
     */
    getSyncStatus() {
        return {
            is_syncing: this.isSyncing,
            last_sync_time: this.lastSyncTime
        };
    }

    /**
     * Clear all offline data (for logout)
     */
    async clearAllData() {
        console.log('[Sync] Clearing all offline data...');

        try {
            await offlineDB.clear(STORES.PRODUCTS);
            await offlineDB.clear(STORES.CUSTOMERS);
            await offlineDB.clear(STORES.PENDING_INVOICES);
            await offlineDB.clear(STORES.PENDING_PAYMENTS);
            await offlineDB.clear(STORES.SYNC_QUEUE);
            await offlineDB.clear(STORES.INVENTORY_UPDATES);
            await offlineDB.clear(STORES.ORGANIZATIONS);
            await offlineDB.clear(STORES.STORES);

            this.lastSyncTime = null;

            console.log('[Sync] All data cleared');
        } catch (error) {
            console.error('[Sync] Failed to clear data:', error);
            throw error;
        }

    /**
     * Get storage usage
     */
    async getStorageInfo() {
        if ('storage' in navigator && 'estimate' in navigator.storage) {
            try {
                const estimate = await navigator.storage.estimate();
                const usage = estimate.usage || 0;
                const quota = estimate.quota || 0;
                const percentUsed = quota > 0 ? (usage / quota) * 100 : 0;

                return {
                    usage_bytes: usage,
                    quota_bytes: quota,
                    usage_mb: (usage / (1024 * 1024)).toFixed(2),
                    quota_mb: (quota / (1024 * 1024)).toFixed(2),
                    percent_used: percentUsed.toFixed(2)
                };
            } catch (error) {
                console.error('[Sync] Failed to get storage info:', error);
                return null;
            }

        return null;
    }

// Export singleton instance
export const syncService = new SyncService();

// Export class for testing
export { SyncService };
