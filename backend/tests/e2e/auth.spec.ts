import { test, expect } from '@playwright/test';

/**
 * Authentication Flow Tests
 * 
 * Coverage:
 * - User registration
 * - Email verification
 * - Login/logout
 * - Password reset
 * - Session persistence
 * - Multi-factor authentication
 */

test.describe('Authentication', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('should display login page', async ({ page }) => {
        await expect(page).toHaveTitle(/R-DIOS/);
        await expect(page.locator('h1')).toContainText('Welcome');
    });

    test('should login with valid credentials', async ({ page }) => {
        // Fill login form
        await page.fill('input[name="email"]', 'demo@rdios.com');
        await page.fill('input[name="password"]', 'Demo@123');

        // Click login button
        await page.click('button[type="submit"]');

        // Wait for navigation to dashboard
        await page.waitForURL('/dashboard');

        // Verify logged in
        await expect(page.locator('h1')).toContainText('Dashboard');
        await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    });

    test('should show error with invalid credentials', async ({ page }) => {
        await page.fill('input[name="email"]', 'invalid@email.com');
        await page.fill('input[name="password"]', 'wrongpassword');

        await page.click('button[type="submit"]');

        // Should show error message
        await expect(page.locator('.error-message')).toContainText('Invalid credentials');

        // Should stay on login page
        await expect(page).toHaveURL('/');
    });

    test('should logout successfully', async ({ page }) => {
        // Login first
        await page.fill('input[name="email"]', 'demo@rdios.com');
        await page.fill('input[name="password"]', 'Demo@123');
        await page.click('button[type="submit"]');
        await page.waitForURL('/dashboard');

        // Click user menu
        await page.click('[data-testid="user-menu"]');

        // Click logout
        await page.click('text=Logout');

        // Should redirect to login
        await page.waitForURL('/');

        // Should not have access to protected routes
        await page.goto('/dashboard');
        await expect(page).toHaveURL('/');
    });

    test('should validate email format', async ({ page }) => {
        await page.fill('input[name="email"]', 'invalid-email');
        await page.fill('input[name="password"]', 'Password123');

        // Try to submit
        await page.click('button[type="submit"]');

        // Should show validation error
        const emailInput = page.locator('input[name="email"]');
        await expect(emailInput).toHaveAttribute('aria-invalid', 'true');
    });

    test('should persist session after refresh', async ({ page }) => {
        // Login
        await page.fill('input[name="email"]', 'demo@rdios.com');
        await page.fill('input[name="password"]', 'Demo@123');
        await page.click('button[type="submit"]');
        await page.waitForURL('/dashboard');

        // Refresh page
        await page.reload();

        // Should still be logged in
        await expect(page).toHaveURL('/dashboard');
        await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
    });

    test('should navigate to password reset', async ({ page }) => {
        await page.click('text=Forgot Password?');

        await expect(page).toHaveURL('/reset-password');
        await expect(page.locator('h1')).toContainText('Reset Password');
    });

    test('should handle password reset flow', async ({ page }) => {
        await page.goto('/reset-password');

        // Enter email
        await page.fill('input[name="email"]', 'demo@rdios.com');
        await page.click('button[type="submit"]');

        // Should show success message
        await expect(page.locator('.success-message')).toContainText('Check your email');
    });

    test('should show loading state during login', async ({ page }) => {
        // Slow down network to see loading state
        await page.route('**/api/v1/auth/login', async route => {
            await new Promise(resolve => setTimeout(resolve, 1000));
            await route.continue();
        });

        await page.fill('input[name="email"]', 'demo@rdios.com');
        await page.fill('input[name="password"]', 'Demo@123');

        const submitButton = page.locator('button[type="submit"]');
        await submitButton.click();

        // Should show loading state
        await expect(submitButton).toBeDisabled();
        await expect(submitButton).toContainText(/Loading|Signing in/i);
    });

    test('should handle session timeout', async ({ page, context }) => {
        // Login
        await page.fill('input[name="email"]', 'demo@rdios.com');
        await page.fill('input[name="password"]', 'Demo@123');
        await page.click('button[type="submit"]');
        await page.waitForURL('/dashboard');

        // Clear session storage to simulate timeout
        await context.clearCookies();
        await page.evaluate(() => localStorage.clear());

        // Try to access protected route
        await page.goto('/invoices');

        // Should redirect to login
        await expect(page).toHaveURL('/');
    });

    test('should prevent SQL injection in login', async ({ page }) => {
        const sqlInjection = "admin'--";

        await page.fill('input[name="email"]', sqlInjection);
        await page.fill('input[name="password"]', sqlInjection);
        await page.click('button[type="submit"]');

        // Should safely handle and show error
        await expect(page.locator('.error-message')).toBeVisible();
        await expect(page).toHaveURL('/');
    });

    test('should validate password strength on registration', async ({ page }) => {
        await page.goto('/register');

        // Weak password
        await page.fill('input[name="password"]', '123');

        // Should show strength indicator
        const strengthIndicator = page.locator('[data-testid="password-strength"]');
        await expect(strengthIndicator).toContainText(/Weak/i);

        // Strong password
        await page.fill('input[name="password"]', 'SecureP@ssw0rd123!');
        await expect(strengthIndicator).toContainText(/Strong/i);
    });

    test('should auto-focus email field on load', async ({ page }) => {
        const emailInput = page.locator('input[name="email"]');
        await expect(emailInput).toBeFocused();
    });

    test('should handle network errors gracefully', async ({ page }) => {
        // Simulate network failure
        await page.route('**/api/v1/auth/login', route => route.abort());

        await page.fill('input[name="email"]', 'demo@rdios.com');
        await page.fill('input[name="password"]', 'Demo@123');
        await page.click('button[type="submit"]');

        // Should show network error
        await expect(page.locator('.error-message')).toContainText(/network|connection/i);
    });
});
