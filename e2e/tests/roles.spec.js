import { expect, test } from '@playwright/test'
import { login } from './helpers'

test('viewer is read-only', async ({ page }) => {
  await login(page, 'viewer')
  await page.goto('/sales')
  await expect(page.locator('table')).toBeVisible()
  await expect(page.getByRole('button', { name: 'New bill' })).toHaveCount(0)
  await page.goto('/customers')
  await expect(page.locator('table')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Add customer' })).toHaveCount(0)
  await expect(page.getByRole('link', { name: 'Data import' })).toHaveCount(0)
  await expect(page.getByRole('link', { name: 'Audit log' })).toHaveCount(0)
})

test('area manager can switch between their two outlets only', async ({ page }) => {
  await login(page, 'areaManager')
  const picker = page.getByLabel('Outlet filter')
  await expect(picker.locator('option')).toHaveText(['All my outlets', 'Indiranagar', 'Whitefield'])
  await picker.selectOption({ label: 'Whitefield' })
  await page.goto('/outlets')
  await expect(page.getByRole('heading', { name: 'Whitefield' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Andheri West' })).toHaveCount(0)
})

test('an expired access token is renewed from the HTTP-only refresh cookie', async ({ page }) => {
  await login(page, 'manager')
  let renewals = 0
  page.on('request', (r) => { if (r.url().includes('/api/auth/refresh')) renewals++ })
  let expired = false
  await page.route('**/api/sales**', (route) => {
    if (!expired) { expired = true; return route.fulfill({ status: 401, contentType: 'application/json', body: '{"detail":"expired"}' }) }
    return route.continue()
  })
  await page.goto('/sales')
  await expect(page.locator('table')).toBeVisible()
  expect(renewals).toBeGreaterThan(0)
})

test('a page reload keeps the session; the tokens are HTTP-only cookies, not in the browser storage', async ({ page }) => {
  await login(page, 'manager')
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible()
  const stored = await page.evaluate(() => Object.keys(localStorage).filter((k) => /token|refresh|auth/i.test(k)))
  expect(stored).toEqual([])
  const cookies = await page.context().cookies()
  for (const name of ['eris_refresh', 'eris_access']) {
    const c = cookies.find((x) => x.name === name)
    expect(c && c.httpOnly).toBe(true)
  }
})

test('phone layout has no horizontal scrolling', async ({ browser }) => {
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } })
  await login(page)
  for (const path of ['/', '/insights', '/reports', '/models', '/invoices', '/import', '/assistant', '/forecasts', '/products', '/inventory', '/sales']) {
    await page.goto(path)
    await page.waitForLoadState('networkidle')
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
    expect(overflow, path).toBeLessThanOrEqual(1)
  }
})

test('a demo account picked from the list signs in, and a suggested question opens the assistant answered', async ({ page }) => {
  await page.goto('/')
  await page.getByLabel('Demo account').selectOption('priya.and@eris.demo')
  await expect(page.getByLabel('Email')).toHaveValue('priya.and@eris.demo')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.locator('.kpi-value').first()).toBeVisible({ timeout: 60_000 })
  await expect(page.getByText('Andheri West').first()).toBeVisible()
  await page.getByRole('link', { name: /Why did revenue change this week/ }).click()
  await expect(page).toHaveURL(/\/assistant/)
  await expect(page.locator('.msg.bot .provenance')).toBeVisible({ timeout: 60_000 })
})

test('a newly opened page starts at its title, not where the last page was scrolled to', async ({ page }) => {
  await login(page)
  await page.getByRole('link', { name: 'Sales', exact: true }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Sales' })).toBeVisible()
  await expect(page.locator('.pager')).toBeVisible()
  await page.evaluate(() => window.scrollTo(0, 1500))
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(200)
  await page.getByRole('link', { name: 'Menu', exact: true }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Menu' })).toBeInViewport()
  expect(await page.evaluate(() => window.scrollY)).toBe(0)
})
