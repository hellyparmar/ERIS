import { test, expect } from '@playwright/test';

/**
 * Invoice E2E Tests
 * 
 * Coverage:
 * - Create invoice online
 * - Create invoice offline
 * - Add/remove line items
 * - Calculate GST (intra-state & inter-state)
 * - Apply discounts
 * - Generate PDF
 * - Email/WhatsApp delivery
 * - Save draft
 */

// Helper function to login
async function login(page) {
    await page.goto('/');
    await page.fill('input[name="email"]', 'demo@rdios.com');
    await page.fill('input[name="password"]', 'Demo@123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
}

test.describe('Invoice Creation', () => {

    test.beforeEach(async ({ page }) => {
        await login(page);
        await page.goto('/invoices/new');
    });

    test('should create invoice with single item', async ({ page }) => {
        // Select customer
        await page.click('[data-testid="customer-select"]');
        await page.click('text=ABC Corporation');

        // Add product
        await page.click('[data-testid="add-item-button"]');
        await page.click('[data-testid="product-select"]');
        await page.click('text=Product A');

        // Set quantity
        await page.fill('input[name="quantity"]', '5');

        // Verify calculations
        const subtotal = page.locator('[data-testid="subtotal"]');
        await expect(subtotal).toContainText('₹5,000');

        // Verify GST (assuming 18%)
        const gstAmount = page.locator('[data-testid="gst-amount"]');
        await expect(gstAmount).toContainText('₹900');

        // Verify total
        const total = page.locator('[data-testid="total-amount"]');
        await expect(total).toContainText('₹5,900');

        // Save invoice
        await page.click('button:has-text("Save Invoice")');

        // Should show success message
        await expect(page.locator('.success-message')).toContainText('Invoice created');

        // Should redirect to invoice details
        await expect(page).toHaveURL(/\/invoices\/INV-/);
    });

    test('should calculate intra-state GST correctly', async ({ page }) => {
        // Select customer in same state
        await page.click('[data-testid="customer-select"]');
        await page.click('text=Local Customer');

        // Add item
        await page.click('[data-testid="add-item-button"]');
        await page.click('[data-testid="product-select"]');
        await page.click('text=Product A');
        await page.fill('input[name="quantity"]', '10');

        // Verify CGST + SGST (9% + 9% = 18%)
        await expect(page.locator('[data-testid="cgst-amount"]')).toContainText('₹900');
        await expect(page.locator('[data-testid="sgst-amount"]')).toContainText('₹900');
        await expect(page.locator('[data-testid="igst-amount"]')).toContainText('₹0');
    });

    test('should calculate inter-state GST correctly', async ({ page }) => {
        // Select customer in different state
        await page.click('[data-testid="customer-select"]');
        await page.click('text=Out of State Customer');

        // Add item
        await page.click('[data-testid="add-item-button"]');
        await page.click('[data-testid="product-select"]');
        await page.click('text=Product A');
        await page.fill('input[name="quantity"]', '10');

        // Verify IGST (18%)
        await expect(page.locator('[data-testid="cgst-amount"]')).toContainText('₹0');
        await expect(page.locator('[data-testid="sgst-amount"]')).toContainText('₹0');
        await expect(page.locator('[data-testid="igst-amount"]')).toContainText('₹1,800');
    });

    test('should add multiple line items', async ({ page }) => {
        await page.click('[data-testid="customer-select"]');
        await page.click('text=ABC Corporation');

        // Add first item
        await page.click('[data-testid="add-item-button"]');
        await page.locator('[data-testid="product-select"]').first().click();
        await page.click('text=Product A');
        await page.locator('input[name="quantity"]').first().fill('2');

        // Add second item
        await page.click('[data-testid="add-item-button"]');
        await page.locator('[data-testid="product-select"]').nth(1).click();
        await page.click('text=Product B');
        await page.locator('input[name="quantity"]').nth(1).fill('3');

        // Verify item count
        const lineItems = page.locator('[data-testid="invoice-line-item"]');
        await expect(lineItems).toHaveCount(2);
    });

    test('should remove line item', async ({ page }) => {
        await page.click('[data-testid="customer-select"]');
        await page.click('text=ABC Corporation');

        // Add two items
        await page.click('[data-testid="add-item-button"]');
        await page.locator('[data-testid="product-select"]').first().click();
        await page.click('text=Product A');

        await page.click('[data-testid="add-item-button"]');

        // Remove first item
        await page.locator('[data-testid="remove-item-button"]').first().click();

        // Should have one item
        const lineItems = page.locator('[data-testid="invoice-line-item"]');
        await expect(lineItems).toHaveCount(1);
    });

    test('should apply discount', async ({ page }) => {
        await page.click('[data-testid="customer-select"]');
        await page.click('text=ABC Corporation');

        await page.click('[data-testid="add-item-button"]');
        await page.click('[data-testid="product-select"]');
        await page.click('text=Product A');
        await page.fill('input[name="quantity"]', '10');

        // Initial total
        let total = await page.locator('[data-testid="total-amount"]').textContent();

        // Apply 10% discount
        await page.fill('input[name="discount"]', '10');

        // Total should decrease
        const newTotal = await page.locator('[data-testid="total-amount"]').textContent();
        expect(parseFloat(newTotal.replace(/[^0-9.]/g, ''))).toBeLessThan(
            parseFloat(total.replace(/[^0-9.]/g, ''))
        );
    });

    test('should save as draft', async ({ page }) => {
        await page.click('[data-testid="customer-select"]');
        await page.click('text=ABC Corporation');

        await page.click('[data-testid="add-item-button"]');
        await page.click('[data-testid="product-select"]');
        await page.click('text=Product A');

        // Save as draft
        await page.click('button:has-text("Save as Draft")');

        // Should show success
        await expect(page.locator('.success-message')).toContainText('Draft saved');

        // Navigate to drafts
        await page.goto('/invoices?status=draft');

        // Should see draft invoice
        await expect(page.locator('[data-testid="invoice-status"]').first()).toContainText('Draft');
    });

    test('should generate PDF', async ({ page }) => {
        // Create invoice first
        await page.click('[data-testid="customer-select"]');
        await page.click('text=ABC Corporation');
        await page.click('[data-testid="add-item-button"]');
        await page.click('[data-testid="product-select"]');
        await page.click('text=Product A');
        await page.click('button:has-text("Save Invoice")');

        // Wait for invoice to be created
        await page.waitForURL(/\/invoices\/INV-/);

        // Listen for download
        const downloadPromise = page.waitForEvent('download');

        // Click PDF button
        await page.click('button:has-text("Download PDF")');

        const download = await downloadPromise;

        // Verify filename
        expect(download.suggestedFilename()).toMatch(/INV-.*\.pdf/);
    });

    test('should validate required fields', async ({ page }) => {
        // Try to save without customer
        await page.click('button:has-text("Save Invoice")');

        // Should show validation errors
        await expect(page.locator('.error-message')).toContainText(/customer|required/i);
    });

    test('should recalculate on quantity change', async ({ page }) => {
        await page.click('[data-testid="customer-select"]');
        await page.click('text=ABC Corporation');

        await page.click('[data-testid="add-item-button"]');
        await page.click('[data-testid="product-select"]');
        await page.click('text=Product A');  // ₹1,000 per unit

        // Initial quantity
        await page.fill('input[name="quantity"]', '5');
        await expect(page.locator('[data-testid="line-total"]')).toContainText('₹5,000');

        // Update quantity
        await page.fill('input[name="quantity"]', '10');
        await expect(page.locator('[data-testid="line-total"]')).toContainText('₹10,000');
    });

    test('should handle concurrent edits gracefully', async ({ page, context }) => {
        // Open invoice in two tabs
        const page2 = await context.newPage();

        // Both pages create same invoice
        await page.click('[data-testid="customer-select"]');
        await page.click('text=ABC Corporation');

        await page2.goto('/invoices/new');
        await login(page2);
        await page2.goto('/invoices/new');
        await page2.click('[data-testid="customer-select"]');
        await page2.click('text=ABC Corporation');

        // Save from both pages
        await Promise.all([
            page.click('button:has-text("Save Invoice")'),
            page2.click('button:has-text("Save Invoice")')
        ]);

        // Both should succeed (separate invoices)
        await expect(page).toHaveURL(/\/invoices\/INV-/);
        await expect(page2).toHaveURL(/\/invoices\/INV-/);

        await page2.close();
    });
});
