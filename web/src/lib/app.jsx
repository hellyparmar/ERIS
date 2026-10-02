import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api, clearSession, getToken, setSession, setUnauthorizedHandler } from './api'
import { setCurrencySymbol } from './format'

const AppCtx = createContext(null)
const ToastCtx = createContext(() => {})

function readPref(key, fallback) {
  try { return localStorage.getItem(key) ?? fallback } catch { return fallback }
}
function writePref(key, value) {
  try { value === null || value === undefined ? localStorage.removeItem(key) : localStorage.setItem(key, value) } catch { /* ignore */ }
}

export function AppProvider({ children }) {
  const qc = useQueryClient()
  const [token, setTok] = useState(getToken())
  const [outletId, setOutletIdState] = useState(() => {
    const v = readPref('eris-outlet', '')
    return v ? Number(v) : null
  })
  const [theme, setThemeState] = useState(() => readPref('eris-theme', 'system'))

  const logout = useCallback(() => {
    clearSession()
    setTok(null)
    qc.clear()
  }, [qc])

  useEffect(() => setUnauthorizedHandler(logout), [logout])

  const me = useQuery({ queryKey: ['me', token], queryFn: () => api('/auth/me'), enabled: !!token, retry: false, staleTime: 300_000 })
  const org = useQuery({ queryKey: ['org'], queryFn: () => api('/settings/organization'), enabled: !!token && me.isSuccess, staleTime: 600_000 })
  const outlets = useQuery({ queryKey: ['outlets'], queryFn: () => api('/outlets'), enabled: !!token && me.isSuccess, staleTime: 300_000 })

  useEffect(() => { if (org.data) setCurrencySymbol(org.data.currency_symbol) }, [org.data])

  const login = async (email, password) => {
    const res = await api('/auth/login', { method: 'POST', body: { email, password } })
    setSession(res.access_token, res.refresh_token)
    qc.clear()
    setTok(res.access_token)
    return res.user
  }

  const setOutletId = (id) => {
    setOutletIdState(id || null)
    writePref('eris-outlet', id || null)
  }

  const setTheme = (t) => {
    setThemeState(t)
    if (t === 'system') {
      delete document.documentElement.dataset.theme
      writePref('eris-theme', null)
    } else {
      document.documentElement.dataset.theme = t
      writePref('eris-theme', t)
    }
  }

  const user = me.data
  // Non-admins work within their assigned outlets: one outlet is fixed, several can be switched between
  // (or viewed together when no outlet is chosen).
  const assigned = user?.outlet_ids || []
  const effectiveOutlet = !user || user.role === 'admin' ? outletId
    : assigned.length === 1 ? assigned[0] : (assigned.includes(outletId) ? outletId : null)
  const value = useMemo(() => ({
    token, user, loadingUser: !!token && me.isLoading, login, logout,
    org: org.data, outlets: outlets.data || [], outletId: effectiveOutlet, setOutletId,
    isAdmin: user?.role === 'admin', isManager: user?.role === 'admin' || user?.role === 'manager',
    canWrite: !!user && user.role !== 'viewer', isViewer: user?.role === 'viewer',
    theme, setTheme,
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }), [token, user, me.isLoading, org.data, outlets.data, effectiveOutlet, theme])

  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>
}

export const useApp = () => useContext(AppCtx)

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const push = useCallback((message, kind = 'info') => {
    const id = Math.random().toString(36).slice(2)
    setToasts((t) => [...t, { id, message, kind }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), kind === 'error' ? 6000 : 3500)
  }, [])
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {toasts.map((t) => <div key={t.id} className={`toast ${t.kind}`}>{t.message}</div>)}
      </div>
    </ToastCtx.Provider>
  )
}

export const useToast = () => useContext(ToastCtx)
