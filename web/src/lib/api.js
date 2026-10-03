// Thin fetch wrapper: adds the JWT, renews it with the refresh token when it expires, parses JSON and turns
// API errors into readable messages.
const TOKEN_KEY = 'eris-token'
// Where the API lives. Empty (default): the same server that serves this app, or the Vite dev proxy.
// Set VITE_API_URL at build time when the web app is hosted separately (e.g. Vercel + API on Render).
export const API_BASE = (import.meta.env.VITE_API_URL || '').trim().replace(/\/+$/, '')
const apiUrl = (path) => new URL(path.startsWith('/api') ? path : `/api${path}`, API_BASE || window.location.origin)
const REFRESH_KEY = 'eris-refresh'

const read = (k) => { try { return localStorage.getItem(k) } catch { return null } }
const write = (k, v) => { try { v ? localStorage.setItem(k, v) : localStorage.removeItem(k) } catch { /* private mode */ } }

export const getToken = () => read(TOKEN_KEY)
export const setToken = (t) => write(TOKEN_KEY, t)
export const setSession = (access, refresh) => { write(TOKEN_KEY, access); write(REFRESH_KEY, refresh) }
export const clearSession = () => setSession(null, null)

// One refresh at a time: parallel requests that hit an expired token all wait for the same renewal.
let refreshing = null
async function renewSession() {
  const refresh = read(REFRESH_KEY)
  if (!refresh) return false
  if (!refreshing) {
    refreshing = fetch(apiUrl('/auth/refresh'), {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: refresh }),
    }).then(async (res) => {
      if (!res.ok) return false
      const data = await res.json()
      setSession(data.access_token, data.refresh_token)
      return true
    }).catch(() => false).finally(() => { setTimeout(() => { refreshing = null }, 0) })
  }
  return refreshing
}

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
  const headers = {}
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
    res = await fetch(url, { method, headers, body: payload })
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
