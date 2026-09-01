import { chromium } from 'playwright';

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('http://localhost:5173/login');
  await page.waitForLoadState('networkidle');

  const getComputedStyle = async (selector) => {
    return await page.evaluate((sel) => {
      const el = document.querySelector(sel);
      if (!el) return null;
      const styles = window.getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      return {
        textAlign: styles.textAlign,
        width: styles.width,
        rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }
      };
    }, selector);
  };

  console.log('h1:', await getComputedStyle('h1'));
  console.log('p:', await getComputedStyle('p'));
  console.log('input (email):', await getComputedStyle('input[type="email"]'));
  console.log('button (Sign in):', await getComputedStyle('button[type="submit"]'));
  console.log('.right-panel container:', await getComputedStyle('div[style*="maxWidth: 380px"]'));

  await browser.close();
})();
