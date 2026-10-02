// Regenerates the README screenshots in docs/images from a running ERIS with the demo data.
//   cd api && uvicorn app.main:app --port 8000      (after `cd web && npm run build`)
//   cd e2e && node screenshots.mjs                   (BASE_URL and PW_CHROMIUM_PATH are optional)
import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from '@playwright/test'

const BASE = process.env.BASE_URL || 'http://localhost:8000'
const out = fileURLToPath(new URL('../docs/images/', import.meta.url))
const browser = await chromium.launch(process.env.PW_CHROMIUM_PATH ? { executablePath: process.env.PW_CHROMIUM_PATH } : {})

async function login(page) {
  await page.goto(BASE + '/')
  await page.getByLabel('Email').fill('admin@eris.demo')
  await page.getByLabel('Password').fill('Admin@123')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await page.waitForSelector('.kpi-value', { timeout: 60_000 })
}
async function shot(page, name) {
  await page.mouse.move(0, 0) // no stray chart tooltips
  await page.locator('.toast').waitFor({ state: 'detached', timeout: 15_000 }).catch(() => {})
  await page.screenshot({ path: join(out, `${name}.png`) })
}

// A sales file with the user's own column names and a few typical mistakes (shown on the import screenshot)
const day = new Date(Date.now() - 86_400_000).toISOString().slice(0, 10)
const rows = [
  'Bill No,date,time,Store,sku,Qty,unit_price,discount,payment_method,channel,customer_phone,customer_name',
  `SHOT-1,${day},10:15,MUM-AND,BEV-001,1,,,upi,in_store,9800001021,Sample Customer 1`,
  `SHOT-2,${day},11:15,PUN-KOR,BEV-002,2,,,cash,in_store,,`,
  `SHOT-2,${day},11:16,PUN-KOR,BEV-003,3,,,cash,in_store,,`,
  `SHOT-3,${day},12:15,BLR-IND,BEV-004,1,,,card,in_store,9802001021,Sample Customer 3`,
  `SHOT-E1,${day},12:00,MUM-AND,NO-SUCH-SKU,1,,,cash,in_store,,`,
  `SHOT-E2,${day},12:05,MUM-AND,BEV-001,-2,,,cash,in_store,,`,
  `SHOT-E3,31-31-2025,12:10,MUM-AND,BEV-001,1,,,cash,in_store,,`,
  `SHOT-E4,${day},12:15,XXX-000,BEV-001,1,,,cheque,in_store,,`,
  `SHOT-E5,${day},12:20,MUM-AND,BEV-001,1,,,upi,in_store,12345,`,
]
const csv = join(mkdtempSync(join(tmpdir(), 'eris-')), 'pos_export.csv')
writeFileSync(csv, rows.join('\n') + '\n')

const p = await browser.newPage({ viewport: { width: 1440, height: 900 } })
await login(p)
await p.waitForTimeout(2500)
await shot(p, 'dashboard')

await p.goto(BASE + '/assistant')
await p.getByRole('button', { name: 'Clear chat' }).click().catch(() => {})
await p.getByLabel('Ask a question').fill('Which outlet had the highest revenue last month?')
await p.getByRole('button', { name: 'Ask' }).click()
await p.waitForSelector('.provenance', { timeout: 60_000 })
await p.locator('.provenance summary').last().click()
await p.locator('.msg.bot').last().evaluate((e) => e.scrollIntoView({ block: 'start' }))
await p.waitForTimeout(800)
await shot(p, 'assistant')

await p.goto(BASE + '/forecasts?scope=category&id=1')
await p.waitForSelector('text=Model leaderboard', { timeout: 120_000 })
await p.waitForTimeout(1500)
await shot(p, 'forecasts')

await p.goto(BASE + '/models')
await p.waitForSelector('text=Most accurate single model', { timeout: 60_000 })
await p.waitForTimeout(1500)
await shot(p, 'model-comparison')

await p.goto(BASE + '/insights')
await p.waitForSelector('text=In plain words', { timeout: 60_000 })
await p.waitForTimeout(1500)
await shot(p, 'drivers')
await p.locator('text=Unusual days and suspicious bills').scrollIntoViewIfNeeded()
await p.waitForTimeout(800)
await shot(p, 'anomalies')

// a demo GST invoice for a recent bill (or the one already issued for it)
await p.goto(BASE + '/sales')
await p.locator('main table tbody tr').first().click()
await p.locator('.drawer').getByRole('button', { name: /GST invoice/ }).or(p.locator('.drawer a', { hasText: /^Invoice / })).click()
await p.waitForSelector('text=Tax summary')
await p.waitForTimeout(800)
await shot(p, 'invoice')

await p.goto(BASE + '/import?type=sales')
await p.locator('input[type=file]').setInputFiles(csv)
await p.waitForSelector('text=Match your columns')
await p.getByRole('button', { name: /Check file/ }).click()
await p.waitForSelector('text=Rows to fix')
await p.getByText('Rows to fix').first().evaluate((e) => e.scrollIntoView({ block: 'center' }))
await p.waitForTimeout(800)
await shot(p, 'import')

await p.goto(BASE + '/reports')
await p.waitForSelector('table')
await p.waitForTimeout(800)
await shot(p, 'reports')

await p.goto(BASE + '/analytics')
await p.waitForTimeout(4000)
await shot(p, 'analytics')

await p.goto(BASE + '/inventory?tab=reorder')
await p.waitForSelector('table tbody tr', { timeout: 60_000 })
await p.waitForTimeout(1000)
await shot(p, 'reorder')

const m = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, colorScheme: 'dark' })
await login(m)
await m.waitForTimeout(2500)
await shot(m, 'mobile-dark')

await browser.close()
console.log('Screenshots written to', out)
