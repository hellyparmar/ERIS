import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: BASE, timeout: 10000 })

// ── Token management ──────────────────────────────────────────────────────────
export const tokenManager = {
  get: () => localStorage.getItem('rdios-token'),
  set: (token: string) => localStorage.setItem('rdios-token', token),
  clear: () => {
    localStorage.removeItem('rdios-token')
    localStorage.removeItem('rdios-user')
  },
}

// ── Request interceptor: attach JWT ──────────────────────────────────────────
const dispatchToast = (message: string, type: 'success' | 'error' | 'warning' | 'info' = 'error', duration = 4000) => {
  if (typeof window !== 'undefined' && window.dispatchEvent) {
    window.dispatchEvent(new CustomEvent('global-toast', { detail: { message, type, duration } }))
  }
}

api.interceptors.request.use((config) => {
  const token = tokenManager.get()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ── Response interceptor: handle 401 ─────────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      dispatchToast('Network error. Check your connection.', 'error')
    } else if (error.response.status === 500) {
      dispatchToast('Server error. Please try again.', 'error')
    } else if (error.response.status === 403) {
      dispatchToast("You don't have permission to do this.", 'warning')
    }

    if (error.response?.status === 401) {
      tokenManager.clear()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ── Auth API ──────────────────────────────────────────────────────────────────
export const authAPI = {
  login: async (email: string, password: string) => {
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);
    const res = await api.post('/api/v1/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    // Store token and user info - extract from res.data.user object
    tokenManager.set(res.data.access_token)
    localStorage.setItem('rdios-user', JSON.stringify({
      id: res.data.user.id,
      email: res.data.user.email,
      username: res.data.user.username,
      role: res.data.user.role,
      organization_id: res.data.user.organization_id,
      is_active: res.data.user.is_active,
      token: res.data.access_token,
    }))
    return res.data
  },

  logout: () => {
    tokenManager.clear()
    window.location.href = '/login'
  },

  me: () => api.get('/api/v1/auth/me').then((r) => r.data),

  register: (data: any) => api.post('/api/v1/auth/register', data).then((r) => r.data),

  isAuthenticated: () => !!tokenManager.get(),

  getUser: () => {
    try {
      return JSON.parse(localStorage.getItem('rdios-user') || '{}')
    } catch {
      return {}
    }
  },
}

// ── Dashboard API ─────────────────────────────────────────────────────────────
export const dashboardAPI = {
  metrics: () => api.get('/api/v1/dashboard/metrics').then((r) => r.data),
  salesChart: (days = 7) => api.get(`/api/v1/dashboard/sales-chart?days=${days}`).then((r) => r.data),
  topOutlets: () => api.get('/api/v1/dashboard/top-outlets').then((r) => r.data),
}

// ── Inventory API ─────────────────────────────────────────────────────────────
export const inventoryAPI = {
  list: (params = {}) => api.get('/api/v1/inventory/', { params }).then((r) => r.data),
  summary: () => api.get('/api/v1/inventory/summary').then((r) => r.data),
  create: (data: any) => api.post('/api/v1/inventory/sku', data).then((r) => r.data),
  update: (id: number, data: any) => api.patch(`/api/v1/inventory/${id}`, data).then((r) => r.data),
  delete: (id: number) => api.delete(`/api/v1/inventory/sku/${id}`).then((r) => r.data),
}

// ── Community Marketplace API ─────────────────────────────────────────────────
export const communityAPI = {
  listings: (params = {}) => api.get('/api/community/listings', { params }).then((r) => r.data),
  createListing: (data: any) => api.post('/api/community/listings', data).then((r) => r.data),
  updateListing: (id: number, data: any) => api.patch(`/api/community/listings/${id}`, data).then((r) => r.data),
  deleteListing: (id: number) => api.delete(`/api/community/listings/${id}`).then((r) => r.data),
  expressInterest: (id: number) => api.post(`/api/community/listings/${id}/interest`).then((r) => r.data),
}

// ── Invoice API ───────────────────────────────────────────────────────────────
export const invoiceAPI = {
  list: (params = {}) => api.get('/api/v1/invoices/', { params }).then((r) => r.data),
  get: (id: number) => api.get(`/api/v1/invoices/${id}`).then((r) => r.data),
  create: (data: any) => api.post('/api/v1/invoices/', data).then((r) => r.data),
  update: (id: number, data: any) => api.patch(`/api/v1/invoices/${id}`, data).then((r) => r.data),
  addPayment: (id: number, data: any) => api.post(`/api/v1/invoices/${id}/payment`, data).then((r) => r.data),
  syncTally: (id: number) => api.post(`/api/v1/invoices/${id}/tally-sync`).then((r) => r.data),
}

// ── Alerts API ────────────────────────────────────────────────────────────────
export const alertsAPI = {
  list: (params = {}) => api.get('/api/v1/alerts/', { params }).then((r) => r.data),
  markRead: (id: number) => api.patch(`/api/v1/alerts/${id}/read`).then((r) => r.data),
  markAllRead: () => api.patch('/api/v1/alerts/mark-all-read').then((r) => r.data),
}

// ── Forecast API ──────────────────────────────────────────────────────────────
export const forecastAPI = {
  sales: (days = 30, outletId: number | null = null) =>
    api.get(`/api/v1/forecasts/sales?days=${days}${outletId ? `&outlet_id=${outletId}` : ''}`).then((r) => r.data),
  inventory: () => api.get('/api/v1/forecasts/inventory').then((r) => r.data),
}

// ── Health API ────────────────────────────────────────────────────────────────
export const healthAPI = {
  check: () => api.get('/health').then((r) => r.data).catch(() => ({ status: 'offline' })),
  ollama: () =>
    fetch('http://localhost:11434/api/tags', { signal: AbortSignal.timeout(3000) })
      .then((r) => r.json())
      .catch(() => null),
}

export const endpoints = {
  me: '/api/v1/auth/me',
  login: '/api/v1/auth/login',
  products: '/api/v1/products',
  product: (id: string | number) => `/api/v1/products/${id}`,
  sales: '/api/v1/sales',
  sale: (id: string | number) => `/api/v1/sales/${id}`,
}

export default api
