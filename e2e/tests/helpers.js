import { expect } from '@playwright/test'

export const USERS = {
  admin: ['admin@eris.demo', 'Admin@123'],
  manager: ['priya.and@eris.demo', 'Manager@123'],
  areaManager: ['arjun.ind@eris.demo', 'Manager@123'],
  staff: ['staff.andheri@eris.demo', 'Staff@123'],
  viewer: ['analyst@eris.demo', 'Viewer@123'],
}

export async function login(page, who = 'admin') {
  const [email, password] = USERS[who]
  await page.goto('/')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page.locator('.kpi-value').first()).toBeVisible({ timeout: 60_000 })
}

/** Fail the test on uncaught page errors or console errors. */
export function watchErrors(page) {
  const errors = []
  page.on('pageerror', (e) => errors.push(e.message))
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
  return errors
}
