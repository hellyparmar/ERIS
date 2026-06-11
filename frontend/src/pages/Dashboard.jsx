import React, { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart, Line, PieChart, Pie, Cell,
  CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'
import { Eye, Plus, FileText, AlertCircle, TrendingUp, ShoppingBag, Activity, Bell } from 'lucide-react'
import SEO from '../components/SEO'
import api, { authAPI } from '../services/api'
import Badge from '../components/ui/Badge'
import '../styles/dashboard.css'

const fmtINR = (val) => {
  if (!val) return '₹0'
  const num = parseInt(val, 10)
  if (isNaN(num)) return '₹0'
  return '₹' + num.toLocaleString('en-IN')
}

const fmtNum = (val) => {
  if (!val) return '0'
  const num = parseInt(val, 10)
  if (isNaN(num)) return '0'
  return num.toLocaleString('en-IN')
}

const CHART_STROKES = ['#f59e0b', '#22d55e', '#3b82f6', '#ef4444', '#a855f7']
const tooltipStyle = { background: '#1a1a1a', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 12, fontSize: 13, color: '#e8e8e8' }

const GradientSkeleton = () => (
  <div style={{ marginTop: 16 }}>
    <div className="skeleton" style={{ height: 200, borderRadius: 8 }} />
  </div>
)

const TableSkeleton = () => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginTop: 16 }}>
    {[1, 2, 3, 4, 5].map((i) => (
      <div key={i} className="skeleton" style={{ height: 44, borderRadius: 8 }} />
    ))}
  </div>
)

export default function Dashboard() {
  const navigate = useNavigate()
  const user = authAPI.getUser() || {}

  const today = useMemo(() => {
    const date = new Date()
    return date.toLocaleDateString('en-GB', {
      weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
    })
  }, [])

  const { data: summary, isLoading: summaryLoading, isError: summaryError, refetch: refetchSummary } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => api.get('/api/v1/dashboard/summary').then((r) => r.data),
  })

  const { data: revenueTrendData, isLoading: trendLoading, isError: trendError } = useQuery({
    queryKey: ['dashboard-revenue-trend'],
    queryFn: () => api.get('/api/v1/dashboard/revenue-trend?days=30').then((r) => r.data),
  })

  const { data: categorySalesData, isLoading: categoryLoading, isError: categoryError } = useQuery({
    queryKey: ['dashboard-category-sales'],
    queryFn: () => api.get('/api/v1/dashboard/sales-by-category').then((r) => r.data),
  })

  const { data: topProductsData, isLoading: productsLoading, isError: productsError } = useQuery({
    queryKey: ['dashboard-top-products'],
    queryFn: () => api.get('/api/v1/dashboard/top-products?limit=5').then((r) => r.data),
  })

  const isSuperAdmin = user?.role === 'super_admin'
  const { data: outletData, isLoading: outletLoading, isError: outletError } = useQuery({
    queryKey: ['dashboard-outlet-performance'],
    queryFn: () => api.get('/api/v1/dashboard/outlet-performance').then((r) => r.data),
    enabled: isSuperAdmin,
  })

  const safeData = summary || {}
  const revenueToday = safeData.total_revenue_today || 0
  const revenueTodayChange = safeData.revenue_change_percent || 0
  const revenueThisMonth = safeData.total_revenue_this_month || 0
  const transactionsToday = safeData.total_transactions_today || 0
  const alertsCount = safeData.low_stock_alerts_count || 0

  return (
    <>
      <SEO title="Dashboard" description="Real-time retail analytics dashboard — sales, revenue, inventory, and AI-powered insights." />
      <div className="dashboard">

        <div className="dash-header">
          <div>
            <p className="page-subtitle">{today}</p>
          </div>
        </div>

        {/* ── HERO CARD (chart as background) ── */}
        {trendLoading ? (
          <GradientSkeleton />
        ) : trendError ? null : (
          <div className="hero-card">
            <div className="hero-chart">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={revenueTrendData || []}>
                  <defs>
                    <linearGradient id="heroRevenue" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                  <XAxis dataKey="date" hide />
                  <YAxis hide />
                  <Tooltip contentStyle={tooltipStyle} formatter={(v) => [fmtINR(v), 'Revenue']} labelFormatter={(d) => new Date(d).toLocaleDateString()} />
                  <Line type="monotone" dataKey="revenue" stroke="#f59e0b" strokeWidth={2} fill="url(#heroRevenue)" dot={false} activeDot={{ r: 5, strokeWidth: 0, fill: '#f59e0b' }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="hero-overlay">
              <div className="hero-label">Today's Revenue</div>
              <div className="hero-value">{fmtINR(revenueToday)}</div>
              <div className={`hero-delta ${revenueTodayChange >= 0 ? 'up' : 'down'}`}>
                {revenueTodayChange >= 0 ? '↑' : '↓'} {Math.abs(revenueTodayChange).toFixed(1)}% vs yesterday
              </div>
            </div>
          </div>
        )}

        {/* ── KPI BENTO ── */}
        {summaryLoading ? (
          <div className="bento-grid">
            {[1,2,3,4].map((i) => (
              <div key={i} className="skeleton" style={{ height: 120, borderRadius: 12 }} />
            ))}
          </div>
        ) : summaryError ? (
          <div className="dash-error">
            <AlertCircle size={18} />
            <span>Failed to load metrics</span>
            <button onClick={() => refetchSummary()}>Retry</button>
          </div>
        ) : (
          <div className="bento-grid">
            <div className="card span-2" style={{ borderLeft: '4px solid #f59e0b' }}>
              <div className="card-label">Monthly Revenue</div>
              <div className="card-value" style={{ marginTop: 4 }}>{fmtINR(revenueThisMonth)}</div>
              <TrendingUp size={18} style={{ color: '#f59e0b', position: 'absolute', top: 20, right: 20 }} />
            </div>
            <div className="card">
              <div className="card-label">Transactions Today</div>
              <div className="card-value" style={{ marginTop: 4 }}>{fmtNum(transactionsToday)}</div>
              <ShoppingBag size={18} style={{ color: '#3b82f6', position: 'absolute', top: 20, right: 20 }} />
            </div>
            <div className="card">
              <div className="card-label">Active Alerts</div>
              <div className="card-value" style={{ marginTop: 4, color: alertsCount > 0 ? '#ef4444' : undefined }}>{fmtNum(alertsCount)}</div>
              <Bell size={18} style={{ color: alertsCount > 0 ? '#ef4444' : '#525252', position: 'absolute', top: 20, right: 20 }} />
            </div>
          </div>
        )}

        {/* ── CHARTS BENTO ── */}
        <div className="bento-two">
          {/* Sales by Category */}
          <div className="card">
            <div className="dash-card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <div>
                <h3 className="section-title">Sales by Category</h3>
                <p className="page-subtitle" style={{ fontSize: 12 }}>Category breakdown</p>
              </div>
            </div>
            {categoryLoading ? (
              <GradientSkeleton />
            ) : categoryError ? (
              <div className="card-error">Unable to load category data</div>
            ) : (
              <div className="chart-area">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={categorySalesData || []} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3} dataKey="value">
                      {(categorySalesData || []).map((_, index) => (
                        <Cell key={`cell-${index}`} fill={CHART_STROKES[index % CHART_STROKES.length]} stroke="none" />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} formatter={(v) => [fmtINR(v), 'Revenue']} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="chart-legend">
                  {(categorySalesData || []).map((cat, idx) => (
                    <div key={idx} className="legend-item">
                      <div className="legend-dot" style={{ background: CHART_STROKES[idx % CHART_STROKES.length] }} />
                      <span className="legend-label">{cat.name}</span>
                      <span className="legend-pct">{cat.percent}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Quick Actions */}
            <div className="card">
              <div className="dash-card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <div>
                  <h3 className="section-title">Quick Actions</h3>
                  <p className="page-subtitle" style={{ fontSize: 12 }}>Common tasks</p>
                </div>
              </div>
              <div className="quick-actions">
                <button className="action-btn" onClick={() => navigate('/inventory')}><Eye size={16} /> View Inventory</button>
                <button className="action-btn" onClick={() => navigate('/sales')}><Plus size={16} /> Add Sale</button>
                <button className="action-btn" onClick={() => navigate('/reports')}><FileText size={16} /> Generate Report</button>
                <button className="action-btn" onClick={() => navigate('/alerts')}><AlertCircle size={16} /> View Alerts</button>
              </div>
            </div>

            {/* Revenue Trend mini */}
            <div className="card">
              <div className="dash-card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <div>
                  <h3 className="section-title">Revenue Trend</h3>
                  <p className="page-subtitle" style={{ fontSize: 12 }}>Last 30 days</p>
                </div>
              </div>
              {trendLoading ? (
                <GradientSkeleton />
              ) : trendError ? (
                <div className="card-error">Unable to load revenue data</div>
              ) : (
                <div className="chart-area">
                  <ResponsiveContainer width="100%" height={180}>
                    <LineChart data={revenueTrendData || []}>
                      <defs>
                        <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.25} />
                          <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                      <XAxis dataKey="date" stroke="#525252" style={{ fontSize: '12px' }} tick={{ fill: '#525252' }} tickFormatter={(d) => { if (!d) return ''; return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) }} />
                      <YAxis stroke="#525252" style={{ fontSize: '12px' }} tick={{ fill: '#525252' }} tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                      <Tooltip contentStyle={tooltipStyle} formatter={(v) => [fmtINR(v), 'Revenue']} labelFormatter={(d) => new Date(d).toLocaleDateString()} />
                      <Line type="monotone" dataKey="revenue" stroke="#f59e0b" strokeWidth={2} fill="url(#colorRevenue)" dot={false} activeDot={{ r: 5, strokeWidth: 0, fill: '#f59e0b' }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── TOP PRODUCTS ── */}
        <div className="bento-grid">
          <div className="card span-2">
            <div className="dash-card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <div>
                <h3 className="section-title">Top Products This Week</h3>
                <p className="page-subtitle" style={{ fontSize: 12 }}>Ranked by revenue</p>
              </div>
            </div>
            {productsLoading ? (
              <TableSkeleton />
            ) : productsError ? (
              <div className="card-error">Unable to load products</div>
            ) : (
              <div className="products-list">
                {(topProductsData || []).slice(0, 5).map((product, idx) => {
                  const maxRevenue = (topProductsData || [])[0]?.revenue || 1
                  const pct = (product.revenue / maxRevenue) * 100
                  return (
                    <div key={idx} className="product-item">
                      <div className="product-rank">{idx + 1}</div>
                      <div className="product-info">
                        <div className="product-name">{product.name}</div>
                        <Badge label={product.category || 'Other'} variant="neutral" />
                      </div>
                      <div className="product-right">
                        <div className="product-revenue">{fmtINR(product.revenue)}</div>
                        <div className="progress-bar"><div className="progress-fill" style={{ width: `${pct}%` }} /></div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* ── OUTLET PERFORMANCE ── */}
        {isSuperAdmin && (
          <div className="card">
            <div className="dash-card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <div>
                <h3 className="section-title">Outlet Performance</h3>
                <p className="page-subtitle" style={{ fontSize: 12 }}>Revenue, transactions, and alerts across all outlets</p>
              </div>
            </div>
            {outletLoading ? (
              <TableSkeleton />
            ) : outletError ? (
              <div className="card-error">Unable to load outlet data</div>
            ) : (
              <div className="outlet-table-wrapper">
                <table className="outlet-table">
                  <thead>
                    <tr>
                      <th>Outlet Name</th>
                      <th>City</th>
                      <th>Revenue (Month)</th>
                      <th>Transactions</th>
                      <th>Avg Basket</th>
                      <th>Alerts</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(outletData || []).map((outlet) => (
                      <tr key={outlet.id || outlet.name}>
                        <td className="outlet-name">{outlet.name}</td>
                        <td>{outlet.city}</td>
                        <td>{fmtINR(outlet.revenue_month)}</td>
                        <td>{fmtNum(outlet.transactions)}</td>
                        <td>{fmtINR(outlet.avg_basket_size)}</td>
                        <td><Badge label={outlet.alerts.toString()} variant={outlet.alerts > 0 ? 'danger' : 'success'} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  )
}
