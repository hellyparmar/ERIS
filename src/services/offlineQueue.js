/**
 * Offline Queue Service
 * Manages offline operations and syncs them when connection is restored
 */

import { offlineDB, STORES } from '../utils/indexedDB';

// Operation types
export const OPERATION_TYPES = {
    CREATE_INVOICE: 'CREATE_INVOICE',
    CREATE_PAYMENT: 'CREATE_PAYMENT',
    UPDATE_INVENTORY: 'UPDATE_INVENTORY',
    UPDATE_CUSTOMER: 'UPDATE_CUSTOMER',
    UPDATE_PRODUCT: 'UPDATE_PRODUCT'
};

// Operation statuses
export const OPERATION_STATUS = {
    PENDING: 'pending',
    SYNCING: 'syncing',
    COMPLETED: 'completed',
    FAILED: 'failed',
    CONFLICT: 'conflict'
};

class OfflineQueue {
    constructor() {
        this.syncInProgress = false;
    }

    /**
     * Add operation to sync queue
     */
    async enqueue(operation) {
        try {
            const queueItem = {
                operation_type: operation.type,
                data: operation.data,
                local_id: operation.local_id,
                timestamp: new Date().toISOString(),
                status: OPERATION_STATUS.PENDING,
                retries: 0,
                max_retries: 5,
                error: null
            };

            await offlineDB.add(STORES.SYNC_QUEUE, queueItem);
            console.log('[OfflineQueue] Operation enqueued:', operation.type);

            return queueItem;
        } catch (error) {
            console.error('[OfflineQueue] Failed to enqueue:', error);
            throw error;
        }
    }

    /**
     * Get all pending operations
     */
    async getPending() {
        try {
            const allOps = await offlineDB.query(STORES.SYNC_QUEUE, 'status', OPERATION_STATUS.PENDING);

            // Sort by timestamp (oldest first)
            allOps.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

            return allOps;
        } catch (error) {
            console.error('[OfflineQueue] Failed to get pending:', error);
            return [];
        }
    }

    /**
     * Get failed operations
     */
    async getFailed() {
        try {
            return await offlineDB.query(STORES.SYNC_QUEUE, 'status', OPERATION_STATUS.FAILED);
        } catch (error) {
            console.error('[OfflineQueue] Failed to get failed:', error);
            return [];
        }
    }

    /**
     * Get operations with conflicts
     */
    async getConflicts() {
        try {
            return await offlineDB.query(STORES.SYNC_QUEUE, 'status', OPERATION_STATUS.CONFLICT);
        } catch (error) {
            console.error('[OfflineQueue] Failed to get conflicts:', error);
            return [];
        }
    }

    /**
     * Process entire queue
     */
    async processQueue(apiClient) {
        if (this.syncInProgress) {
            console.log('[OfflineQueue] Sync already in progress');
            return { inProgress: true };
        }

        this.syncInProgress = true;
        console.log('[OfflineQueue] Starting queue processing...');

        try {
            const pending = await this.getPending();

            const results = {
                total: pending.length,
                success: 0,
                failed: 0,
                conflicts: 0
            };

            for (const operation of pending) {
                try {
                    // Update status to syncing
                    await this.updateOperationStatus(operation.id, OPERATION_STATUS.SYNCING);

                    // Process based on operation type
                    let result;
                    switch (operation.operation_type) {
                        case OPERATION_TYPES.CREATE_INVOICE:
                            result = await this.syncInvoice(operation, apiClient);
                            break;

                        case OPERATION_TYPES.CREATE_PAYMENT:
                            result = await this.syncPayment(operation, apiClient);
                            break;

                        case OPERATION_TYPES.UPDATE_INVENTORY:
                            result = await this.syncInventory(operation, apiClient);
                            break;

                        case OPERATION_TYPES.UPDATE_CUSTOMER:
                            result = await this.syncCustomer(operation, apiClient);
                            break;

                        default:
                            throw new Error(`Unknown operation type: ${operation.operation_type}`);
                    }

                    // Mark as completed
                    await this.updateOperationStatus(operation.id, OPERATION_STATUS.COMPLETED);
                    await offlineDB.delete(STORES.SYNC_QUEUE, operation.id);
                    results.success++;

                } catch (error) {
                    console.error('[OfflineQueue] Operation failed:', error);

                    if (error.conflict) {
                        // Mark as conflict - requires manual resolution
                        await this.updateOperationStatus(operation.id, OPERATION_STATUS.CONFLICT, error.message);
                        results.conflicts++;
                    } else {
                        // Increment retry count
                        const newRetries = (operation.retries || 0) + 1;

                        if (newRetries >= operation.max_retries) {
                            // Max retries reached - mark as failed
                            await this.updateOperationStatus(operation.id, OPERATION_STATUS.FAILED, error.message);
                            results.failed++;
                        } else {
                            // Reset to pending for retry
                            await offlineDB.put(STORES.SYNC_QUEUE, {
                                ...operation,
                                status: OPERATION_STATUS.PENDING,
                                retries: newRetries,
                                error: error.message
                            });
                        }
                    }
                }
            }

            console.log('[OfflineQueue] Queue processed:', results);
            return results;

        } finally {
            this.syncInProgress = false;
        }
    }

    /**
     * Sync invoice to server
     */
    async syncInvoice(operation, apiClient) {
        try {
            const invoiceData = operation.data;

            // Send to server
            const response = await apiClient.post('/api/v1/invoices', invoiceData);

            // Update local record with server ID
            const localInvoice = await offlineDB.get(STORES.PENDING_INVOICES, operation.local_id);
            if (localInvoice) {
                await offlineDB.put(STORES.PENDING_INVOICES, {
                    ...localInvoice,
                    server_id: response.id,
                    synced: true,
                    synced_at: new Date().toISOString()
                });
            }

            return response;
        } catch (error) {
            // Check for conflict (e.g., invoice number already exists)
            if (error.response?.status === 409) {
                error.conflict = true;
            }
            throw error;
        }
    }

    /**
     * Sync payment to server
     */
    async syncPayment(operation, apiClient) {
        try {
            const paymentData = operation.data;

            // Send to server
            const response = await apiClient.post('/api/v1/payments', paymentData);

            // Update local record
            const localPayment = await offlineDB.get(STORES.PENDING_PAYMENTS, operation.local_id);
            if (localPayment) {
                await offlineDB.put(STORES.PENDING_PAYMENTS, {
                    ...localPayment,
                    server_id: response.id,
                    synced: true,
                    synced_at: new Date().toISOString()
                });
            }

            return response;
        } catch (error) {
            if (error.response?.status === 409) {
                error.conflict = true;
            }
            throw error;
        }
    }

    /**
     * Sync inventory update to server
     */
    async syncInventory(operation, apiClient) {
        try {
            const inventoryData = operation.data;

            // Send to server
            const response = await apiClient.put(`/api/v1/inventory/${inventoryData.product_id}`, inventoryData);

            // Remove from local updates
            if (operation.local_id) {
                await offlineDB.delete(STORES.INVENTORY_UPDATES, operation.local_id);
            }

            return response;
        } catch (error) {
            if (error.response?.status === 409) {
                error.conflict = true;
            }
            throw error;
        }
    }

    /**
     * Sync customer update to server
     */
    async syncCustomer(operation, apiClient) {
        try {
            const customerData = operation.data;

            // Send to server
            const response = await apiClient.put(`/api/v1/customers/${customerData.id}`, customerData);

            // Update local cache
            await offlineDB.put(STORES.CUSTOMERS, response);

            return response;
        } catch (error) {
            if (error.response?.status === 409) {
                error.conflict = true;
            }
            throw error;
        }
    }

    /**
     * Update operation status
     */
    async updateOperationStatus(operationId, status, error = null) {
        try {
            const operation = await offlineDB.get(STORES.SYNC_QUEUE, operationId);
            if (operation) {
                await offlineDB.put(STORES.SYNC_QUEUE, {
                    ...operation,
                    status,
                    error,
                    updated_at: new Date().toISOString()
                });
            }
        } catch (err) {
            console.error('[OfflineQueue] Failed to update status:', err);
        }
    }

    /**
     * Retry failed operations
     */
    async retryFailed(apiClient) {
        try {
            const failed = await this.getFailed();

            console.log(`[OfflineQueue] Retrying ${failed.length} failed operations`);

            // Reset status to pending
            for (const operation of failed) {
                await offlineDB.put(STORES.SYNC_QUEUE, {
                    ...operation,
                    status: OPERATION_STATUS.PENDING,
                    retries: 0,
                    error: null
                });
            }

            // Process queue
            return await this.processQueue(apiClient);
        } catch (error) {
            console.error('[OfflineQueue] Failed to retry:', error);
            throw error;
        }
    }

    /**
     * Clear completed operations
     */
    async clearCompleted() {
        try {
            const completed = await offlineDB.query(STORES.SYNC_QUEUE, 'status', OPERATION_STATUS.COMPLETED);

            for (const operation of completed) {
                await offlineDB.delete(STORES.SYNC_QUEUE, operation.id);
            }

            console.log(`[OfflineQueue] Cleared ${completed.length} completed operations`);
        } catch (error) {
            console.error('[OfflineQueue] Failed to clear completed:', error);
        }
    }

    /**
     * Get queue statistics
     */
    async getStats() {
        try {
            const all = await offlineDB.getAll(STORES.SYNC_QUEUE);

            const stats = {
                total: all.length,
                pending: 0,
                syncing: 0,
                completed: 0,
                failed: 0,
                conflicts: 0
            };

            all.forEach((op) => {
                stats[op.status] = (stats[op.status] || 0) + 1;
            });

            return stats;
        } catch (error) {
            console.error('[OfflineQueue] Failed to get stats:', error);
            return null;
        }
    }
}

// Export singleton instance
export const offlineQueue = new OfflineQueue();

// Export class for testing
export { OfflineQueue };
