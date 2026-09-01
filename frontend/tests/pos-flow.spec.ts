import { test, expect } from '@playwright/test';

test.describe('POS Page Flow E2E Test', () => {
  test('POS user authentication and checkout flow works end-to-end', async ({ page }) => {
    // 1. Navigate to the POS page (via proxy port 80)
    await page.goto('http://127.0.0.1/pos');

    // 2. PIN login screen should be visible. We check for POS Login header.
    await expect(page.locator('text=POS Login')).toBeVisible();

    // 3. Enter PIN '9999' for manager using the keypad buttons or keyboard
    // Since the page has keyboard support, let's simulate typing '9999' then 'Enter'
    await page.keyboard.type('9999');
    await page.keyboard.press('Enter');

    // 4. Wait for redirection or authenticated view to load
    // The Cashier Info Bar will contain 'Manager' or the avatar or logout button
    await page.waitForSelector('text=Logout', { timeout: 10000 });
    
    // Check that cashier bar is visible
    await expect(page.locator('text=Online')).toBeVisible();

    // 5. Search for a product. Let's type 'Cable' or another product that exists in database.
    // Let's first type 'a' to get any matching products.
    const searchInput = page.locator('input[placeholder="Search product by name or SKU..."]');
    await searchInput.fill('a');
    
    // Wait for the dropdown recommendations
    await page.waitForSelector('button:has-text("SKU:")', { timeout: 5000 });

    // Let's get the first matching product name
    const productItem = page.locator('button:has-text("SKU:")').first();
    const productName = await productItem.locator('p').first().textContent();
    console.log(`Adding product to cart: ${productName}`);
    
    // Click the product to add to cart
    await productItem.click();

    // 6. Verify product is in the cart
    await expect(page.locator(`text=Cart Items (1)`)).toBeVisible();
    await expect(page.locator(`p:has-text("${productName}")`)).toBeVisible();

    // 7. Test quantity stepper: increment quantity
    const plusButton = page.locator('.stepper-btn').nth(1); // Second stepper button is plus
    await plusButton.click();
    
    // Verify quantity is now 2
    await expect(page.locator('.stepper-btn + span')).toHaveText('2');

    // 8. Verify GST calculation is visible and total is updated
    await expect(page.locator('text=GST (18%)')).toBeVisible();
    await expect(page.locator('text=Subtotal')).toBeVisible();

    // 9. Choose a payment method (e.g. UPI)
    const upiButton = page.locator('button:has-text("UPI")');
    await upiButton.click();

    // 10. Complete sale
    const completeSaleButton = page.locator('button:has-text("Complete Sale")');
    await expect(completeSaleButton).toBeEnabled();
    await completeSaleButton.click();

    // 11. Success indicator (Receipt Preview) should show up, and cart should clear
    await expect(page.locator('text=Receipt Preview')).toBeVisible();
    
    // Verify cart is cleared
    await expect(page.locator('text=Cart is empty.')).toBeVisible();

    // Take a screenshot of the completed flow
    await page.screenshot({ path: 'screenshots/pos-flow-success.png' });
  });
});
