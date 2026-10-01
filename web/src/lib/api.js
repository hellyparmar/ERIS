// Thin fetch wrapper: adds the JWT, parses JSON and turns API errors into readable messages.
const TOKEN_KEY = 'eris-token'

export const getToken = () => {
  try { return localStorage.getItem(TOKEN_KEY) } catch { return null }
}
export const setToken = (t) => {
  try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY) } catch { /* private mode */ }
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

export async function api(path, { method = 'GET', body, params, raw = false, form } = {}) {
  const url = new URL(path.startsWith('/api') ? path : `/api${path}`, window.location.origin)
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
  if (res.status === 401 && token) onUnauthorized()
  if (raw) {
    if (!res.ok) throw new ApiError(`Download failed (${res.status})`, res.status)
    return res
  }
  const data = res.status === 204 ? null : await res.json().catch(() => null)
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
