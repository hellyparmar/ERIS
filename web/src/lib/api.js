// Thin fetch wrapper: adds the access token, renews it from the HTTP-only refresh cookie when it expires, parses
// JSON and turns API errors into readable messages.
//
// The access token lives in memory only, so it is gone when the tab closes. The refresh token never reaches page
// scripts: the server keeps it in an HTTP-only cookie, and a page reload restores the session through that cookie.
// Where the API lives. Empty (default): the same server that serves this app, or the Vite dev proxy.
// Set VITE_API_URL at build time when the web app is hosted separately (e.g. Vercel + API on Render).
export const API_BASE = (import.meta.env.VITE_API_URL || '').trim().replace(/\/+$/, '')
const apiUrl = (path) => new URL(path.startsWith('/api') ? path : `/api${path}`, API_BASE || window.location.origin)
// Sent with every request. A page on another site cannot add it without a CORS preflight the API refuses, which
// is what protects the refresh cookie from forged requests.
const CLIENT_HEADER = 'X-ERIS-Client'

// Versions before this one kept tokens in localStorage. Remove them so no old token lingers.
try { ['eris-token', 'eris-refresh'].forEach((k) => localStorage.removeItem(k)) } catch { /* private mode */ }

let accessToken = null
export const getToken = () => accessToken
export const setSession = (access) => { accessToken = access || null }
export const clearSession = () => setSession(null)

// One renewal at a time: parallel requests that hit an expired token all wait for the same renewal.
let refreshing = null
async function renewSession() {
  if (!refreshing) {
    refreshing = fetch(apiUrl('/auth/refresh'), {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', [CLIENT_HEADER]: 'web' },
      body: '{}',
    }).then(async (res) => {
      if (!res.ok) return false
      const data = await res.json()
      setSession(data.access_token)
      return true
    }).catch(() => false).finally(() => { setTimeout(() => { refreshing = null }, 0) })
  }
  return refreshing
}

/** On start-up: is there a session cookie that still gives a valid access token? */
export const restoreSession = () => renewSession()

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.status = status
    this.data = data
  }
}

let onUnauthorized = () => {}
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn }

function errorMessage(data, status) {
  if (!data) return `Request failed (${status})`
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) {
    return data.detail.map((d) => `${(d.loc || []).filter((x) => x !== 'body').join('.')}: ${d.msg}`).join('; ')
  }
  return `Request failed (${status})`
}

export async function api(path, { method = 'GET', body, params, raw = false, form, retried = false } = {}) {
  const url = apiUrl(path)
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, v)
  })
  const headers = { [CLIENT_HEADER]: 'web' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  let payload
  if (form) payload = form
  else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  let res
  try {
    res = await fetch(url, { method, headers, body: payload, credentials: 'include' })
  } catch {
    throw new ApiError('Cannot reach the ERIS server. Is the API running?', 0)
  }
  if (res.status === 401 && token && !path.includes('/auth/login')) {
    if (!retried && await renewSession()) return api(path, { method, body, params, raw, form, retried: true })
    onUnauthorized()
  }
  if (raw) {
    if (!res.ok) throw new ApiError(`Download failed (${res.status})`, res.status)
    return res
  }
  const data = res.status === 204 ? null : await res.json().catch(() => null)
  if (!res.ok && data === null && [404, 405, 502, 503, 504].includes(res.status)) {
    // not an ERIS answer: no API behind this address (e.g. a static host without VITE_API_URL) or it is starting
    throw new ApiError(`The ERIS API is not reachable at ${url.origin} (HTTP ${res.status}). It may still be starting - `
      + 'try again in a minute.', res.status)
  }
  if (!res.ok) throw new ApiError(errorMessage(data, res.status), res.status, data)
  return data
}

export async function download(path, params, filename) {
  const res = await api(path, { params, raw: true })
  const blob = await res.blob()
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  const cd = res.headers.get('Content-Disposition') || ''
  a.download = filename || (cd.match(/filename="([^"]+)"/) || [])[1] || 'export.csv'
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}
