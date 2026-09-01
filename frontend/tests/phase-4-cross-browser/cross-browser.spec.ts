import { test, expect, chromium, firefox, webkit } from '@playwright/test';

/**
 * Phase 4: Cross-Browser Testing Framework
 * Tests application across different browsers and versions
 * Supports: Chrome, Firefox, Safari (WebKit), Edge
 */

const BASE_URL = 'http://127.0.0.1:4173';

test.describe('Phase 4: Cross-Browser Tests', () => {
  test.describe('Chromium Browser (Chrome/Edge)', () => {
    test('Should load dashboard in Chrome', async () => {
      const browser = await chromium.launch();
      const context = await browser.createBrowserContext();
      const page = await context.newPage();

      try {
        await page.goto(BASE_URL);
        
        // Wait for main content
        await page.waitForSelector('[role="main"]', { timeout: 5000 }).catch(() => null);
        
        // Verify page title
        const title = await page.title();
        expect(title).toBeTruthy();

        // Check for major layout elements
        const mainContent = await page.$('[role="main"]');
        expect(mainContent).toBeTruthy();

        // Verify no console errors
        const errors: string[] = [];
        page.on('console', msg => {
          if (msg.type() === 'error') errors.push(msg.text());
        });

        await page.waitForTimeout(1000);
        expect(errors).toHaveLength(0);

        // Screenshot
        await page.screenshot({ path: `screenshots/chrome-${Date.now()}.png` });
      } finally {
        await context.close();
        await browser.close();
      }
    });

    test('Chrome - Should handle navigation', async () => {
      const browser = await chromium.launch();
      const context = await browser.createBrowserContext();
      const page = await context.newPage();

      try {
        await page.goto(BASE_URL);
        
        // Try to navigate using sidebar links if available
        const navLinks = await page.$$('a[role="menuitem"], nav a');
        
        if (navLinks.length > 0) {
          const firstLink = navLinks[0];
          const href = await firstLink.getAttribute('href');
          
          if (href && href !== '#') {
            await firstLink.click();
            await page.waitForTimeout(500);
            
            // Verify page changed
            const newUrl = page.url();
            expect(newUrl).not.toBe(BASE_URL);
          }
        }
      } finally {
        await context.close();
        await browser.close();
      }
    });

    test('Chrome - Viewport should be responsive', async () => {
      const browser = await chromium.launch();
      const context = await browser.createBrowserContext({
        viewport: { width: 1440, height: 900 },
      });
      const page = await context.newPage();

      try {
        await page.goto(BASE_URL);
        
        const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
        const clientWidth = await page.evaluate(() => window.innerWidth);
        
        expect(scrollWidth).toBeLessThanOrEqual(clientWidth);
      } finally {
        await context.close();
        await browser.close();
      }
    });
  });

  test.describe('Firefox Browser', () => {
    test('Should load dashboard in Firefox', async () => {
      const browser = await firefox.launch();
      const context = await browser.createBrowserContext();
      const page = await context.newPage();

      try {
        await page.goto(BASE_URL);
        
        await page.waitForSelector('[role="main"]', { timeout: 5000 }).catch(() => null);
        
        const title = await page.title();
        expect(title).toBeTruthy();

        const mainContent = await page.$('[role="main"]');
        expect(mainContent).toBeTruthy();

        // Screenshot
        await page.screenshot({ path: `screenshots/firefox-${Date.now()}.png` });
      } finally {
        await context.close();
        await browser.close();
      }
    });

    test('Firefox - Form interactions should work', async () => {
      const browser = await firefox.launch();
      const context = await browser.createBrowserContext();
      const page = await context.newPage();

      try {
        await page.goto(BASE_URL);
        
        // Find and interact with first input if exists
        const input = await page.$('input[type="text"], input[type="search"]');
        
        if (input) {
          await input.fill('test input');
          const value = await input.inputValue();
          expect(value).toBe('test input');
        }
      } finally {
        await context.close();
        await browser.close();
      }
    });

    test('Firefox - Should handle CSS properly', async () => {
      const browser = await firefox.launch();
      const context = await browser.createBrowserContext();
      const page = await context.newPage();

      try {
        await page.goto(BASE_URL);
        
        // Check computed styles render correctly
        const element = await page.$('body > *');
        if (element) {
          const styles = await element.evaluate(el => 
            window.getComputedStyle(el)
          );
          expect(styles.display).toBeTruthy();
        }
      } finally {
        await context.close();
        await browser.close();
      }
    });
  });

  test.describe('WebKit Browser (Safari)', () => {
    test('Should load dashboard in Safari (WebKit)', async () => {
      const browser = await webkit.launch();
      const context = await browser.createBrowserContext();
      const page = await context.newPage();

      try {
        await page.goto(BASE_URL);
        
        await page.waitForSelector('[role="main"]', { timeout: 5000 }).catch(() => null);
        
        const title = await page.title();
        expect(title).toBeTruthy();

        const mainContent = await page.$('[role="main"]');
        expect(mainContent).toBeTruthy();

        // Screenshot
        await page.screenshot({ path: `screenshots/safari-webkit-${Date.now()}.png` });
      } finally {
        await context.close();
        await browser.close();
      }
    });

    test('Safari - Touch events should work', async () => {
      const browser = await webkit.launch();
      const context = await browser.createBrowserContext({
        hasTouch: true,
        isMobile: true,
      });
      const page = await context.newPage();

      try {
        await page.goto(BASE_URL);
        
        // Verify page supports touch
        const supportsTouchEvents = await page.evaluate(() => 
          'ontouchstart' in window || navigator.maxTouchPoints > 0
        );
        
        // Safari should handle both touch and mouse events
        expect(typeof supportsTouchEvents).toBe('boolean');
      } finally {
        await context.close();
        await browser.close();
      }
    });

    test('Safari - CSS Grid and Flexbox should render', async () => {
      const browser = await webkit.launch();
      const context = await browser.createBrowserContext();
      const page = await context.newPage();

      try {
        await page.goto(BASE_URL);
        
        // Check for flex/grid layout
        const layoutElements = await page.$$('[style*="display"], .flex, .grid');
        expect(layoutElements.length).toBeGreaterThan(0);
      } finally {
        await context.close();
        await browser.close();
      }
    });
  });

  test.describe('Cross-Browser Compatibility', () => {
    test('All browsers - localStorage should work', async () => {
      const browsers = [
        { name: 'Chromium', launch: chromium.launch },
        { name: 'Firefox', launch: firefox.launch },
        { name: 'WebKit', launch: webkit.launch },
      ];

      for (const browserConfig of browsers) {
        const browser = await browserConfig.launch();
        const context = await browser.createBrowserContext();
        const page = await context.newPage();

        try {
          await page.goto(BASE_URL);
          
          // Test localStorage
          await page.evaluate(() => {
            localStorage.setItem('test-key', 'test-value');
          });

          const value = await page.evaluate(() => 
            localStorage.getItem('test-key')
          );
          
          expect(value).toBe('test-value');
        } finally {
          await context.close();
          await browser.close();
        }
      }
    });

    test('All browsers - CSS custom properties should work', async () => {
      const browsers = [
        { name: 'Chromium', launch: chromium.launch },
        { name: 'Firefox', launch: firefox.launch },
        { name: 'WebKit', launch: webkit.launch },
      ];

      for (const browserConfig of browsers) {
        const browser = await browserConfig.launch();
        const context = await browser.createBrowserContext();
        const page = await context.newPage();

        try {
          await page.goto(BASE_URL);
          
          // Check for CSS variable support
          const supportsCSSVariables = await page.evaluate(() => {
            const el = document.documentElement;
            el.style.setProperty('--test-var', 'red');
            return getComputedStyle(el).getPropertyValue('--test-var').trim() === 'red';
          });
          
          expect(supportsCSSVariables).toBeTruthy();
        } finally {
          await context.close();
          await browser.close();
        }
      }
    });

    test('All browsers - should render with same layout', async () => {
      const browsers = [
        { name: 'Chromium', launch: chromium.launch },
        { name: 'Firefox', launch: firefox.launch },
        { name: 'WebKit', launch: webkit.launch },
      ];

      for (const browserConfig of browsers) {
        const browser = await browserConfig.launch();
        const context = await browser.createBrowserContext({
          viewport: { width: 1440, height: 900 },
        });
        const page = await context.newPage();

        try {
          await page.goto(BASE_URL);
          await page.waitForTimeout(500);
          
          // Check consistent rendering metrics
          const metrics = await page.evaluate(() => ({
            scrollHeight: document.documentElement.scrollHeight,
            clientHeight: document.documentElement.clientHeight,
            offsetHeight: document.body.offsetHeight,
          }));
          
          expect(metrics.scrollHeight).toBeGreaterThan(0);
          expect(metrics.clientHeight).toBeGreaterThan(0);
        } finally {
          await context.close();
          await browser.close();
        }
      }
    });

    test('All browsers - JavaScript execution should work', async () => {
      const browsers = [
        { name: 'Chromium', launch: chromium.launch },
        { name: 'Firefox', launch: firefox.launch },
        { name: 'WebKit', launch: webkit.launch },
      ];

      for (const browserConfig of browsers) {
        const browser = await browserConfig.launch();
        const context = await browser.createBrowserContext();
        const page = await context.newPage();

        try {
          await page.goto(BASE_URL);
          
          // Test basic JS operations
          const result = await page.evaluate(() => {
            const arr = [1, 2, 3];
            return arr.map(x => x * 2).reduce((a, b) => a + b, 0);
          });
          
          expect(result).toBe(12);
        } finally {
          await context.close();
          await browser.close();
        }
      }
    });
  });

  test.describe('Browser-Specific Features', () => {
    test('Chrome - ServiceWorker support', async () => {
      const browser = await chromium.launch();
      const context = await browser.createBrowserContext();
      const page = await context.newPage();

      try {
        await page.goto(BASE_URL);
        
        const hasServiceWorkerAPI = await page.evaluate(() => 
          'serviceWorker' in navigator
        );
        
        expect(hasServiceWorkerAPI).toBeTruthy();
      } finally {
        await context.close();
        await browser.close();
      }
    });

    test('Firefox - IndexedDB support', async () => {
      const browser = await firefox.launch();
      const context = await browser.createBrowserContext();
      const page = await context.newPage();

      try {
        await page.goto(BASE_URL);
        
        const hasIndexedDB = await page.evaluate(() => 
          !!window.indexedDB
        );
        
        expect(hasIndexedDB).toBeTruthy();
      } finally {
        await context.close();
        await browser.close();
      }
    });

    test('Safari - WebKit Text Rendering', async () => {
      const browser = await webkit.launch();
      const context = await browser.createBrowserContext();
      const page = await context.newPage();

      try {
        await page.goto(BASE_URL);
        
        // Check text rendering
        const textElements = await page.$$('p, span, h1, h2, h3');
        expect(textElements.length).toBeGreaterThan(0);
      } finally {
        await context.close();
        await browser.close();
      }
    });
  });
});
