import fs from 'node:fs'
import { expect, test } from '@playwright/test'
import { login, watchErrors } from './helpers'

test('admin can open every page without errors', async ({ page }) => {
  const errors = watchErrors(page)
  await login(page)
  const pages = [
    ['/assistant', 'AI Assistant'], ['/sales', 'Sales'], ['/inventory', 'Inventory'], ['/products', 'Products'],
    ['/suppliers', 'Suppliers'], ['/customers', 'Customers'], ['/invoices', 'Invoices (demo GST)'],
    ['/forecasts', 'Forecasts'], ['/models', 'Model comparison'], ['/insights', 'Anomalies & drivers'],
    ['/analytics', 'Analytics'], ['/reports', 'Reports & export'], ['/outlets', 'Outlets'], ['/import', 'Data import'],
    ['/audit', 'Audit log'], ['/settings', 'Settings'],
  ]
  for (const [path, title] of pages) {
    await page.goto(path)
    await expect(page.getByRole('heading', { level: 1, name: title })).toBeVisible()
  }
  await page.goto('/forecasts')
  await expect(page.getByText('Model leaderboard')).toBeVisible({ timeout: 90_000 })
  await page.goto('/insights')
  await expect(page.getByText('In plain words')).toBeVisible()
  await expect(page.getByText('Unusual outlet-days')).toBeVisible()
  expect(errors).toEqual([])
})

test('record a sale, issue a demo GST invoice and void the sale', async ({ page }) => {
  await login(page)
  await page.goto('/sales')
  await page.getByRole('button', { name: 'New sale' }).click()
  await page.locator('.modal select').first().selectOption({ label: 'Andheri West' })
  await page.getByLabel('Search products').fill('milk')
  await page.getByRole('button', { name: /Toned Milk 1L/ }).click()
  await page.getByRole('button', { name: /Save bill/ }).click()
  await expect(page.getByText('Total paid')).toBeVisible()
  await page.getByRole('button', { name: /Issue GST invoice/ }).click()
  await expect(page).toHaveURL(/invoices\?id=/)
  await expect(page.getByText('Tax summary')).toBeVisible()
  await expect(page.locator('.drawer').getByText(/DEMO - NOT FOR TAX FILING/)).toBeVisible()
  await expect(page.locator('.drawer').getByText('Intra-state - CGST + SGST')).toBeVisible()
  const pdf = await page.request.get(`/api/invoices/${new URL(page.url()).searchParams.get('id')}/pdf`, {
    headers: { Authorization: `Bearer ${await page.evaluate(() => localStorage.getItem('eris-token'))}` },
  })
  expect(pdf.ok()).toBeTruthy()
  expect((await pdf.body()).subarray(0, 4).toString()).toBe('%PDF')
})

test('import with column mapping: errors block the import, a valid file commits', async ({ page }) => {
  await login(page)
  await page.goto('/import?type=sales')
  const [bad] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Sample with mistakes' }).click()])
  const lines = fs.readFileSync(await bad.path(), 'utf8').split('\n')
  lines[0] = lines[0].replace('invoice_no', 'Bill No').replace('outlet_code', 'Store').replace('quantity', 'Qty')
  const renamed = test.info().outputPath('pos_export.csv')
  fs.writeFileSync(renamed, lines.join('\n'))
  await page.locator('input[type=file]').setInputFiles(renamed)
  await expect(page.getByText('Match your columns')).toBeVisible()
  await page.getByRole('button', { name: /Check file/ }).click()
  await expect(page.getByText('Rows to fix')).toBeVisible()
  await expect(page.getByRole('button', { name: /^Import/ })).toBeDisabled()

  const [good] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Sample file (valid)' }).click()])
  const goodPath = test.info().outputPath('sales_sample.csv')
  await good.saveAs(goodPath)
  await page.locator('input[type=file]').setInputFiles(goodPath)
  await expect(page.getByText('Match your columns')).toBeVisible()
  await page.getByRole('button', { name: /Check file/ }).click()
  await expect(page.getByText(/All rows look good/)).toBeVisible()
  await page.getByRole('button', { name: /^Import \d+ record/ }).click()
  await expect(page.getByRole('main').getByText(/Import complete/)).toBeVisible()
  await expect(page.locator('table').last().getByText('committed').first()).toBeVisible()
})

test('assistant answers the evaluation questions with provenance', async ({ page }) => {
  await login(page)
  await page.goto('/assistant')
  const questions = ['Which outlet had the highest revenue last month?', 'Why was Outlet 3 revenue lower this week?', 'What is WAPE?']
  for (const [i, q] of questions.entries()) {
    await page.getByLabel('Ask a question').fill(q)
    await page.getByRole('button', { name: 'Ask' }).click()
    await expect(page.locator('.provenance')).toHaveCount(i + 1, { timeout: 60_000 })
  }
  await page.locator('.provenance summary').nth(1).click()
  await expect(page.locator('.provenance').nth(1)).toContainText('Indiranagar')
  await expect(page.locator('.provenance').nth(2)).toContainText('docs/knowledge/glossary.md')
})

test('reports download as CSV and Excel', async ({ page }) => {
  await login(page)
  await page.goto('/reports')
  await expect(page.locator('table')).toBeVisible()
  const [csv] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'CSV' }).click()])
  expect(csv.suggestedFilename()).toMatch(/^eris_sales-daily_.*\.csv$/)
  const [xlsx] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Excel' }).click()])
  expect(xlsx.suggestedFilename()).toMatch(/\.xlsx$/)
})

test('purchase order can be delivered in parts, then completed', async ({ page }) => {
  await login(page, 'manager')
  await page.goto('/suppliers')
  await page.getByRole('button', { name: 'New purchase order' }).click()
  const modal = page.locator('.modal')
  await modal.locator('label:has-text("Supplier") select').selectOption({ index: 1 })
  await modal.getByLabel('Search products').fill('milk')
  await page.getByRole('button', { name: /Toned Milk 1L/ }).click()
  await modal.getByRole('button', { name: /Create/ }).last().click()
  const toast = page.locator('.toast', { hasText: /Purchase order .* created/ })
  await expect(toast).toBeVisible()
  const poNumber = (await toast.textContent()).match(/Purchase order (\S+) created/)[1]

  await page.locator('main table tbody tr', { hasText: poNumber }).click()
  const drawer = page.locator('.drawer')
  const qty = drawer.locator('input[type=number]').first()
  const ordered = Number(await qty.inputValue())
  await qty.fill(String(Math.max(1, Math.floor(ordered / 2))))
  await drawer.getByRole('button', { name: 'Record delivery' }).click()
  await expect(page.getByText(/rest of the order is still expected/)).toBeVisible()
  await expect(drawer.getByText('Part-delivered').first()).toBeVisible()
  await drawer.getByRole('button', { name: 'Record delivery' }).click()
  await expect(page.getByText(/order complete/)).toBeVisible()
})
