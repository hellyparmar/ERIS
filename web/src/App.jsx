import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { Empty, Spinner } from './components/ui'
import { useApp } from './lib/app'
import Login from './pages/Login'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Assistant = lazy(() => import('./pages/Assistant'))
const Sales = lazy(() => import('./pages/Sales'))
const Inventory = lazy(() => import('./pages/Inventory'))
const Products = lazy(() => import('./pages/Products'))
const Suppliers = lazy(() => import('./pages/Suppliers'))
const Customers = lazy(() => import('./pages/Customers'))
const Forecasts = lazy(() => import('./pages/Forecasts'))
const Analytics = lazy(() => import('./pages/Analytics'))
const Outlets = lazy(() => import('./pages/Outlets'))
const DataImport = lazy(() => import('./pages/DataImport'))
const Settings = lazy(() => import('./pages/Settings'))
const ModelComparison = lazy(() => import('./pages/ModelComparison'))
const Insights = lazy(() => import('./pages/Insights'))
const Reports = lazy(() => import('./pages/Reports'))
const Invoices = lazy(() => import('./pages/Invoices'))
const AuditLog = lazy(() => import('./pages/AuditLog'))
const Help = lazy(() => import('./pages/Help'))

/** Pages a role cannot use show a clear message instead of failing API calls (the API enforces it too). */
function Guard({ allow, children }) {
  const { user } = useApp()
  if (allow.includes(user.role)) return children
  return (
    <Empty title="You don't have access to this page">
      This page is for {allow.join(' / ')} accounts. Ask an admin if you need access. <a href="/">Back to the dashboard</a>
    </Empty>
  )
}

const MANAGERS = ['admin', 'manager']

export default function App() {
  const { token, user, loadingUser } = useApp()
  if (!token) return <Login />
  if (loadingUser || !user) return <Spinner label="Loading ERIS…" />
  return (
    <Suspense fallback={<Spinner />}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="assistant" element={<Assistant />} />
          <Route path="sales" element={<Sales />} />
          <Route path="inventory" element={<Inventory />} />
          <Route path="products" element={<Products />} />
          <Route path="suppliers" element={<Suppliers />} />
          <Route path="customers" element={<Customers />} />
          <Route path="forecasts" element={<Forecasts />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="outlets" element={<Outlets />} />
          <Route path="import" element={<Guard allow={MANAGERS}><DataImport /></Guard>} />
          <Route path="settings" element={<Settings />} />
          <Route path="models" element={<ModelComparison />} />
          <Route path="insights" element={<Insights />} />
          <Route path="reports" element={<Reports />} />
          <Route path="invoices" element={<Invoices />} />
          <Route path="help" element={<Help />} />
          <Route path="audit" element={<Guard allow={['admin']}><AuditLog /></Guard>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Suspense>
  )
}
