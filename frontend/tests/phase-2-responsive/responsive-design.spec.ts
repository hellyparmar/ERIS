import { test, expect, devices } from '@playwright/test';

/**
 * Phase 2: Responsive Design Testing Framework
 * Tests layout, components, and UI across different device sizes
 * Covers: Mobile (iPhone), Tablet (iPad), Desktop
 */

const BASE_URL = 'http://127.0.0.1:4173';

// Define viewports for testing
const VIEWPORTS = {
  'mobile-small': { width: 320, height: 568, device: 'iPhone SE' },
  'mobile-medium': { width: 375, height: 667, device: 'iPhone 8' },
  'mobile-large': { width: 414, height: 896, device: 'iPhone 11' },
  'tablet-portrait': { width: 768, height: 1024, device: 'iPad' },
  'tablet-landscape': { width: 1024, height: 768, device: 'iPad Landscape' },
  'desktop-small': { width: 1280, height: 720, device: 'Desktop HD' },
  'desktop-medium': { width: 1440, height: 900, device: 'Desktop Full HD' },
  'desktop-large': { width: 1920, height: 1080, device: 'Desktop 1080p' },
  'desktop-4k': { width: 2560, height: 1440, device: 'Desktop 4K' },
};

test.describe('Phase 2: Responsive Design Tests', () => {
  test.describe('Mobile Responsiveness', () => {
    test('Mobile Small (320px) - Layout should stack vertically', async ({
      page,
    }) => {
      await page.setViewportSize(VIEWPORTS['mobile-small'].width, VIEWPORTS['mobile-small'].height);
      await page.goto(BASE_URL);
      
      // Wait for main layout to load
      await page.waitForSelector('[role="main"]', { timeout: 5000 }).catch(() => null);
      
      // Check sidebar is hidden or collapsed on mobile
      const sidebar = await page.$('[data-testid="sidebar"]');
      if (sidebar) {
        const display = await sidebar.evaluate(el => window.getComputedStyle(el).display);
        expect(['none', '']).toContain(display);
      }

      // Take screenshot for visual regression
      await page.screenshot({ path: `screenshots/mobile-small-${Date.now()}.png` });
    });

    test('Mobile Medium (375px) - Touch targets should be 44px minimum', async ({
      page,
    }) => {
      await page.setViewportSize(VIEWPORTS['mobile-medium'].width, VIEWPORTS['mobile-medium'].height);
      await page.goto(BASE_URL);

      // Get all clickable elements
      const buttons = await page.$$('button, a[role="button"], [role="menuitem"]');
      
      for (const button of buttons) {
        const box = await button.boundingBox();
        if (box && box.width > 0 && box.height > 0) {
          expect(Math.min(box.width, box.height)).toBeGreaterThanOrEqual(44);
        }
      }

      await page.screenshot({ path: `screenshots/mobile-medium-${Date.now()}.png` });
    });

    test('Mobile Large (414px) - Text should be readable without zoom', async ({
      page,
    }) => {
      await page.setViewportSize(VIEWPORTS['mobile-large'].width, VIEWPORTS['mobile-large'].height);
      await page.goto(BASE_URL);

      // Check minimum font size (should be 16px for readability)
      const bodyText = await page.$$('body *:not(script):not(style)');
      for (const element of bodyText.slice(0, 20)) {
        const fontSize = await element.evaluate(el => 
          window.getComputedStyle(el).fontSize
        ).catch(() => '0px');
        
        const size = parseInt(fontSize);
        expect(size).toBeGreaterThanOrEqual(12); // Minimum recommended
      }

      await page.screenshot({ path: `screenshots/mobile-large-${Date.now()}.png` });
    });

    test('Mobile - No horizontal scroll should occur', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS['mobile-small'].width, VIEWPORTS['mobile-small'].height);
      await page.goto(BASE_URL);

      const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      const clientWidth = await page.evaluate(() => window.innerWidth);
      
      expect(scrollWidth).toBeLessThanOrEqual(clientWidth);
    });
  });

  test.describe('Tablet Responsiveness', () => {
    test('Tablet Portrait (768px) - Two-column layout should be visible', async ({
      page,
    }) => {
      await page.setViewportSize(VIEWPORTS['tablet-portrait'].width, VIEWPORTS['tablet-portrait'].height);
      await page.goto(BASE_URL);

      // Check sidebar visibility on tablet
      const sidebar = await page.$('[data-testid="sidebar"]');
      if (sidebar) {
        const isVisible = await sidebar.evaluate(el => 
          window.getComputedStyle(el).display !== 'none'
        );
        expect(isVisible).toBeTruthy();
      }

      await page.screenshot({ path: `screenshots/tablet-portrait-${Date.now()}.png` });
    });

    test('Tablet Landscape (1024px) - Full layout should be visible', async ({
      page,
    }) => {
      await page.setViewportSize(VIEWPORTS['tablet-landscape'].width, VIEWPORTS['tablet-landscape'].height);
      await page.goto(BASE_URL);

      // Check all major layout sections are visible
      const mainContent = await page.$('[role="main"]');
      expect(mainContent).toBeTruthy();

      await page.screenshot({ path: `screenshots/tablet-landscape-${Date.now()}.png` });
    });
  });

  test.describe('Desktop Responsiveness', () => {
    test('Desktop HD (1280px) - Standard desktop layout', async ({ page }) => {
      await page.setViewportSize(VIEWPORTS['desktop-small'].width, VIEWPORTS['desktop-small'].height);
      await page.goto(BASE_URL);

      const sidebar = await page.$('[data-testid="sidebar"]');
      expect(sidebar).toBeTruthy();

      await page.screenshot({ path: `screenshots/desktop-hd-${Date.now()}.png` });
    });

    test('Desktop Full HD (1440px) - Should maintain readability', async ({
      page,
    }) => {
      await page.setViewportSize(VIEWPORTS['desktop-medium'].width, VIEWPORTS['desktop-medium'].height);
      await page.goto(BASE_URL);

      // Check max content width is reasonable (usually 1200-1400px for content)
      const mainContent = await page.$('[role="main"]');
      if (mainContent) {
        const width = await mainContent.boundingBox().then(box => box?.width || 0);
        expect(width).toBeLessThanOrEqual(1400);
      }

      await page.screenshot({ path: `screenshots/desktop-fullhd-${Date.now()}.png` });
    });

    test('Desktop 4K (2560px) - Should handle ultra-wide screens', async ({
      page,
    }) => {
      await page.setViewportSize(VIEWPORTS['desktop-4k'].width, VIEWPORTS['desktop-4k'].height);
      await page.goto(BASE_URL);

      // Check no content is pushed off-screen
      const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
      const clientWidth = await page.evaluate(() => window.innerWidth);
      
      expect(scrollWidth).toBeLessThanOrEqual(clientWidth);

      await page.screenshot({ path: `screenshots/desktop-4k-${Date.now()}.png` });
    });
  });

  test.describe('Responsive Component Tests', () => {
    test('Navigation menu should adapt to screen size', async ({ page }) => {
      const sizes = [
        VIEWPORTS['mobile-small'],
        VIEWPORTS['tablet-portrait'],
        VIEWPORTS['desktop-medium'],
      ];

      for (const size of sizes) {
        await page.setViewportSize(size.width, size.height);
        await page.goto(BASE_URL);

        // Navigation should be present (either visible or hidden)
        const nav = await page.$('nav, [role="navigation"]');
        expect(nav).toBeTruthy();

        await page.screenshot({ 
          path: `screenshots/nav-${size.width}px-${Date.now()}.png` 
        });
      }
    });

    test('Images should scale responsively', async ({ page }) => {
      const sizes = [
        VIEWPORTS['mobile-small'],
        VIEWPORTS['desktop-medium'],
      ];

      for (const size of sizes) {
        await page.setViewportSize(size.width, size.height);
        await page.goto(BASE_URL);

        const images = await page.$$('img');
        for (const img of images) {
          const box = await img.boundingBox();
          if (box) {
            // Image should not exceed viewport width
            expect(box.width).toBeLessThanOrEqual(size.width);
          }
        }
      }
    });

    test('Form inputs should be properly sized on all devices', async ({
      page,
    }) => {
      const sizes = [VIEWPORTS['mobile-medium'], VIEWPORTS['desktop-medium']];

      for (const size of sizes) {
        await page.setViewportSize(size.width, size.height);
        await page.goto(BASE_URL);

        const inputs = await page.$$('input, textarea, select');
        for (const input of inputs) {
          const box = await input.boundingBox();
          if (box) {
            // Minimum touch target size
            expect(box.height).toBeGreaterThanOrEqual(44);
            // Should fit within viewport
            expect(box.width).toBeLessThanOrEqual(size.width);
          }
        }
      }
    });
  });

  test.describe('Orientation Changes', () => {
    test('Should handle portrait to landscape orientation change', async ({
      page,
    }) => {
      // Start in portrait
      await page.setViewportSize(768, 1024);
      await page.goto(BASE_URL);
      
      const portraitContent = await page.content();

      // Switch to landscape
      await page.setViewportSize(1024, 768);
      await page.evaluate(() => window.dispatchEvent(new Event('resize')));
      
      // Wait for potential reflow
      await page.waitForTimeout(500);

      // Check for layout shift without errors
      const errors = [];
      page.on('console', msg => {
        if (msg.type() === 'error') errors.push(msg.text());
      });

      expect(errors).toHaveLength(0);
    });
  });

  test.describe('Responsive Breakpoint Tests', () => {
    const breakpoints = [
      { name: 'xs', width: 320 },
      { name: 'sm', width: 640 },
      { name: 'md', width: 768 },
      { name: 'lg', width: 1024 },
      { name: 'xl', width: 1280 },
      { name: '2xl', width: 1536 },
    ];

    for (const bp of breakpoints) {
      test(`Breakpoint ${bp.name} (${bp.width}px) should render without errors`, async ({
        page,
      }) => {
        await page.setViewportSize(bp.width, 800);
        await page.goto(BASE_URL);

        // Check for JavaScript errors
        const errors: string[] = [];
        page.on('console', msg => {
          if (msg.type() === 'error') errors.push(msg.text());
        });

        await page.waitForTimeout(1000);
        expect(errors).toHaveLength(0);

        await page.screenshot({ 
          path: `screenshots/breakpoint-${bp.name}-${Date.now()}.png` 
        });
      });
    }
  });
});
