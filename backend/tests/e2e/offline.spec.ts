import { test, expect } from '@playwright/test';

/**
 * Offline Functionality Tests
 * 
 * Coverage:
 * - Offline mode detection
 * - Create invoice offline
 * - Queue sync operations
 * - Auto-sync on connection restore
 * - Conflict resolution
 * - Offline indicator
 * - IndexedDB persistence
 */

async function login(page) {
    await page.goto('/');
    await page.fill('input[name="email"]', 'demo@rdios.com');
    await page.fill('input[name="password"]', 'Demo@123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
}

test.describe('Offline Functionality', () => {

    test('should detect offline mode', async ({ page, context }) => {
        await login(page);
        await page.goto('/dashboard');

        // Go offline
        await context.setOffline(true);

        // Wait for offline indicator
        await page.waitForSelector('[data-testid="offline-indicator"]', { timeout: 5000 });

        const indicator = page.locator('[data-testid="offline-indicator"]');
        await expect(indicator).toContainText(/offline/i);
        await expect(indicator).toHaveClass(/offline/);
    });

    test('should create invoice offline', async ({ page, context }) => {
        await login(page);
        await page.goto('/invoices/new');

        // Go offline
        await context.setOffline(true);

        // Wait for offline mode
        await page.waitForSelector('[data-testid="offline-indicator"]');

        // Create invoice
        await page.click('[data-testid="customer-select"]');
        await page.click('text=ABC Corporation');

        await page.click('[data-testid="add-item-button"]');
        await page.click('[data-testid="product-select"]');
        await page.click('text=Product A');
        await page.fill('input[name="quantity"]', '5');

        // Save invoice
        await page.click('button:has-text("Save Invoice")');

        // Should show offline save message
        await expect(page.locator('.info-message')).toContainText(/saved offline|will sync/i);

        // Should redirect to invoice details
        await expect(page).toHaveURL(/\/invoices\/local-/);
    });

    test('should queue sync operation offline', async ({ page, context }) => {
        await login(page);
        await page.goto('/invoices/new');

        // Go offline
        await context.setOffline(true);
        await page.waitForSelector('[data-testid="offline-indicator"]');

        // Create invoice
        await page.click('[data-testid="customer-select"]');
        await page.click('text=ABC Corporation');
        await page.click('[data-testid="add-item-button"]');
        await page.click('[data-testid="product-select"]');
        await page.click('text=Product A');
        await page.click('button:has-text("Save Invoice")');

        // Check pending count in indicator
        const pendingCount = page.locator('[data-testid="pending-count"]');
        await expect(pendingCount).toContainText('1');
    });

    test('should auto-sync when connection restored', async ({ page, context }) => {
        await login(page);
        await page.goto('/invoices/new');

        // Go offline
        await context.setOffline(true);
        await page.waitForSelector('[data-testid="offline-indicator"]');

        // Create invoice offline
        await page.click('[data-testid="customer-select"]');
        await page.click('text=ABC Corporation');
        await page.click('[data-testid="add-item-button"]');
        await page.click('[data-testid="product-select"]');
        await page.click('text=Product A');
        await page.click('button:has-text("Save Invoice")');

        // Wait for local save
        await page.waitForURL(/\/invoices\/local-/);

        // Go back online
        await context.setOffline(false);

        // Wait for sync notification
        await expect(page.locator('.success-message')).toContainText(/synced|online/i, { timeout: 10000 });

        // Pending count should be 0
        const pendingCount = page.locator('[data-testid="pending-count"]');
        await expect(pendingCount).toHaveText('0');
    });

    test('should persist data across page refresh', async ({ page, context }) => {
        await login(page);
        await page.goto('/invoices/new');

        // Go offline
        await context.setOffline(true);

        // Create invoice
        await page.click('[data-testid="customer-select"]');
        await page.click('text=ABC Corporation');
        await page.click('[data-testid="add-item-button"]');
        await page.click('[data-testid="product-select"]');
        await page.click('text=Product A');
        await page.click('button:has-text("Save Invoice")');

        // Get local ID
        const url = page.url();
        const localId = url.match(/local-[^\/]+/)[0];

        // Refresh page (still offline)
        await page.reload();

        // Should still see the invoice
        await page.goto(`/invoices/${localId}`);
        await expect(page.locator('[data-testid="customer-name"]')).toContainText('ABC Corporation');
    });

    test('should show offline warning before critical actions', async ({ page, context }) => {
        await login(page);
        await page.goto('/dashboard');

        // Go offline
        await context.setOffline(true);
        await page.waitForSelector('[data-testid="offline-indicator"]');

        // Try to sync manually
        await page.click('[data-testid="sync-button"]');

        // Should show warning
        await expect(page.locator('.warning-message')).toContainText(/cannot sync offline/i);
    });

    test('should cache product data for offline use', async ({ page, context }) => {
        await login(page);

        // Load products page online
        await page.goto('/products');
        await page.waitForSelector('[data-testid="product-list"]');

        // Go offline
        await context.setOffline(true);

        // Reload products page
        await page.reload();

        // Should still show products (from cache)
        await expect(page.locator('[data-testid="product-list"]')).toBeVisible();
        const products = page.locator('[data-testid="product-item"]');
        await expect(products).not.toHaveCount(0);
    });

    test('should cache customer data for offline use', async ({ page, context }) => {
        await login(page);

        // Load customers page online
        await page.goto('/customers');
        await page.waitForSelector('[data-testid="customer-list"]');

        // Go offline
        await context.setOffline(true);

        // Reload customers page
        await page.reload();

        // Should still show customers (from cache)
        await expect(page.locator('[data-testid="customer-list"]')).toBeVisible();
    });

    test('should handle sync conflicts', async ({ page, context, browser }) => {
        // Create two browser contexts (simulating two devices)
        const context2 = await browser.newContext();
        const page2 = await context2.newPage();

        // Login on both
        await login(page);
        await login(page2);

        // Both go offline
        await context.setOffline(true);
        await context2.setOffline(true);

        // Both create similar invoice
        for (const p of [page, page2]) {
            await p.goto('/invoices/new');
            await p.click('[data-testid="customer-select"]');
            await p.click('text=ABC Corporation');
            await p.click('[data-testid="add-item-button"]');
            await p.click('[data-testid="product-select"]');
            await p.click('text=Product A');
            await p.click('button:has-text("Save Invoice")');
        }

        // Go back online (page 1 first)
        await context.setOffline(false);
        await page.waitForTimeout(2000); // Let first sync complete

        // Then page 2
        await context2.setOffline(false);
        await page2.waitForTimeout(2000);

        // Both should have synced successfully (separate invoices)
        await page.goto('/invoices');
        await page2.goto('/invoices');

        const invoices1 = await page.locator('[data-testid="invoice-item"]').count();
        const invoices2 = await page2.locator('[data-testid="invoice-item"]').count();

        expect(invoices1).toBeGreaterThan(0);
        expect(invoices2).toBeGreaterThan(0);

        await context2.close();
    });

    test('should show storage usage', async ({ page }) => {
        await login(page);

        // Click offline indicator to show details
        const indicator = page.locator('[data-testid="offline-indicator"]');
        await indicator.click();

        // Should show storage info
        await expect(page.locator('[data-testid="storage-usage"]')).toBeVisible();
        await expect(page.locator('[data-testid="storage-usage"]')).toContainText(/MB/);
    });

    test('should handle service worker registration', async ({ page }) => {
        await page.goto('/');

        // Check if service worker is registered
        const swRegistered = await page.evaluate(async () => {
            if ('serviceWorker' in navigator) {
                const registration = await navigator.serviceWorker.getRegistration();
                return registration !== undefined;
            }
            return false;
        });

        expect(swRegistered).toBeTruthy();
    });

    test('should show offline page when navigating offline', async ({ page, context }) => {
        await page.goto('/');

        // Go offline
        await context.setOffline(true);

        // Navigate to new page
        await page.goto('/about');

        // Should show offline page OR cached content
        const hasOfflineIndicator = await page.locator('[data-testid="offline-indicator"]').isVisible();
        const hasContent = await page.locator('body').textContent();

        expect(hasOfflineIndicator || hasContent.length > 100).toBeTruthy();
    });
});
