// The API seeds demo data in the background on first start; wait until it is done.
export default async function globalSetup(config) {
  const base = config.projects[0].use.baseURL
  const deadline = Date.now() + 240_000
  while (Date.now() < deadline) {
    try {
      const r = await fetch(`${base}/api/health`)
      const h = await r.json()
      if (h.seeding?.running) throw new Error('seeding')
      // ready once the demo accounts exist (the API lists them for the sign-in page)
      const accounts = await (await fetch(`${base}/api/auth/demo-accounts`)).json()
      if (Array.isArray(accounts) && accounts.some((a) => a.email === 'admin@eris.demo')) return
    } catch { /* server still starting */ }
    await new Promise((res) => setTimeout(res, 2000))
  }
  throw new Error('Demo data was not ready within 4 minutes')
}
