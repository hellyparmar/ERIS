/**
 * Offline Invoice Service
 * Handles invoice creation and management in offline mode
 */

import { offlineDB, STORES } from '../utils/indexedDB';
import { offlineQueue, OPERATION_TYPES } from './offlineQueue';

/**
 * Generate temporary local ID
 */
function generateLocalId() {
    return `local-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Calculate invoice totals locally
 */
function calculateInvoiceTotals(invoiceData) {
    let subtotal = 0;
    let taxable_amount = 0;
    let cgst_amount = 0;
    let sgst_amount = 0;
    let igst_amount = 0;
    let cess_amount = 0;
    let discount_amount = invoiceData.discount_amount || 0;

    // Calculate line items
    const items = invoiceData.items || [];
    items.forEach((item) => {
        const lineTotal = item.quantity * item.unit_price;
        subtotal += lineTotal;

        // Calculate tax based on rates
        if (item.cgst_rate) {
            cgst_amount += (lineTotal * item.cgst_rate) / 100;
        }
        if (item.sgst_rate) {
            sgst_amount += (lineTotal * item.sgst_rate) / 100;
        }
        if (item.igst_rate) {
            igst_amount += (lineTotal * item.igst_rate) / 100;
        }
        if (item.cess_rate) {
            cess_amount += (lineTotal * item.cess_rate) / 100;
        }
    });

    taxable_amount = subtotal - discount_amount;
    const total_tax = cgst_amount + sgst_amount + igst_amount + cess_amount;
    const total_amount = taxable_amount + total_tax;

    // Round off
    const round_off = Math.round(total_amount) - total_amount;

    return {
        subtotal: parseFloat(subtotal.toFixed(2)),
        taxable_amount: parseFloat(taxable_amount.toFixed(2)),
        cgst_amount: parseFloat(cgst_amount.toFixed(2)),
        sgst_amount: parseFloat(sgst_amount.toFixed(2)),
        igst_amount: parseFloat(igst_amount.toFixed(2)),
        cess_amount: parseFloat(cess_amount.toFixed(2)),
        total_tax: parseFloat(total_tax.toFixed(2)),
        total_amount: parseFloat((total_amount + round_off).toFixed(2)),
        round_off: parseFloat(round_off.toFixed(2))
    };
}

/**
 * Create invoice offline
 */
export async function createInvoiceOffline(invoiceData) {
    try {
        // Generate local ID
        const local_id = generateLocalId();

        // Calculate totals
        const totals = calculateInvoiceTotals(invoiceData);

        // Create invoice object
        const invoice = {
            local_id,
            ...invoiceData,
            ...totals,
            status: 'pending_sync',
            synced: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        };

        // Save to IndexedDB
        await offlineDB.put(STORES.PENDING_INVOICES, invoice);
        console.log('[OfflineInvoice] Invoice created offline:', local_id);

        // Add to sync queue
        await offlineQueue.enqueue({
            type: OPERATION_TYPES.CREATE_INVOICE,
            data: invoiceData,
            local_id
        });

        // Register background sync (if supported)
        if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
            const registration = await navigator.serviceWorker.ready;
            await registration.sync.register('sync-invoices');
        }

        return invoice;
    } catch (error) {
        console.error('[OfflineInvoice] Failed to create invoice:', error);
        throw error;
    }

/**
 * Get all pending invoices
 */
export async function getPendingInvoices() {
    try {
        const invoices = await offlineDB.query(STORES.PENDING_INVOICES, 'synced', false);
        return invoices;
    } catch (error) {
        console.error('[OfflineInvoice] Failed to get pending invoices:', error);
        return [];
    }

/**
 * Get invoice by local ID
 */
export async function getInvoiceByLocalId(local_id) {
    try {
        return await offlineDB.get(STORES.PENDING_INVOICES, local_id);
    } catch (error) {
        console.error('[OfflineInvoice] Failed to get invoice:', error);
        return null;
    }

/**
 * Update invoice offline
 */
export async function updateInvoiceOffline(local_id, updates) {
    try {
        const invoice = await offlineDB.get(STORES.PENDING_INVOICES, local_id);

        if (!invoice) {
            throw new Error('Invoice not found');
        }

        // Recalculate totals if items changed
        let totals = {};
        if (updates.items) {
            totals = calculateInvoiceTotals({ ...invoice, ...updates });
        }

        // Update invoice
        const updatedInvoice = {
            ...invoice,
            ...updates,
            ...totals,
            updated_at: new Date().toISOString()
        };

        await offlineDB.put(STORES.PENDING_INVOICES, updatedInvoice);
        console.log('[OfflineInvoice] Invoice updated:', local_id);

        return updatedInvoice;
    } catch (error) {
        console.error('[OfflineInvoice] Failed to update invoice:', error);
        throw error;
    }

/**
 * Delete invoice offline
 */
export async function deleteInvoiceOffline(local_id) {
    try {
        await offlineDB.delete(STORES.PENDING_INVOICES, local_id);
        console.log('[OfflineInvoice] Invoice deleted:', local_id);
    } catch (error) {
        console.error('[OfflineInvoice] Failed to delete invoice:', error);
        throw error;
    }

/**
 * Get invoice statistics
 */
export async function getInvoiceStats() {
    try {
        const all = await offlineDB.getAll(STORES.PENDING_INVOICES);
        const pending = all.filter(inv => !inv.synced);
        const synced = all.filter(inv => inv.synced);

        const totalPendingAmount = pending.reduce((sum, inv) => sum + (inv.total_amount || 0), 0);

        return {
            total: all.length,
            pending: pending.length,
            synced: synced.length,
            total_pending_amount: parseFloat(totalPendingAmount.toFixed(2))
        };
    } catch (error) {
        console.error('[OfflineInvoice] Failed to get stats:', error);
        return null;
    }
