import React, { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { Eye, Plus, FileText, AlertCircle } from 'lucide-react'

import api, { authAPI } from '../services/api'
import StatCard from '../components/ui/StatCard'
import Badge from '../components/ui/Badge'
import '../styles/dashboard.css'

const fmtINR = (val) => {
  if (!val) return '₹0'
  const num = parseInt(val, 10)
  if (isNaN(num)) return '₹0'
  if (num < 100000) {
    return '₹' + num.toLocaleString('en-IN')
  }
  const result = num.toLocaleString('en-IN')
  return '₹' + result
}

const fmtNum = (val) => {
  if (!val) return '0'
  const num = parseInt(val, 10)
  if (isNaN(num)) return '0'
  return num.toLocaleString('en-IN')
}

const CHART_COLORS = ['#FEF9C3', '#FCE7F3', '#DCFCE7', '#DBEAFE', '#EDE9FE']

const GradientSkeleton = () => (
  <div className="skeleton-item">
    <div className="skeleton-line" style={{ width: '60%', marginBottom: '12px' }} />
    <div className="skeleton-line" style={{ width: '100%', height: '200px' }} />
  </div>
)

const TableSkeleton = () => (
  <>
    {[1, 2, 3, 4, 5].map((i) => (
      <div key={i} className="skeleton-item skeleton-row">
        <div className="skeleton-line" style={{ width: '15%' }} />
        <div className="skeleton-line" style={{ width: '25%' }} />
        <div className="skeleton-line" style={{ width: '20%' }} />
        <div className="skeleton-line" style={{ width: '25%' }} />
      </div>
    ))}
  </>
)

export default function Dashboard() {
  const navigate = useNavigate()
  const user = authAPI.getUser() || {}

  const today = useMemo(() => {
    const date = new Date()
    return date.toLocaleDateString('en-GB', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    })
  }, [])

  // Fetch dashboard summary
  const { data: summary, isLoading: summaryLoading, isError: summaryError, refetch: refetchSummary } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => api.get('/api/v1/dashboard/summary').then((res) => res.data),
    staleTime: 30000,
  })

  // Fetch revenue trend (last 30 days)
  const { data: revenueTrendData, isLoading: trendLoading, isError: trendError } = useQuery({
    queryKey: ['dashboard-revenue-trend'],
    queryFn: () => api.get('/api/v1/dashboard/revenue-trend?days=30').then((res) => res.data),
    staleTime: 30000,
  })

  // Fetch category sales
  const { data: categorySalesData, isLoading: categoryLoading, isError: categoryError } = useQuery({
    queryKey: ['dashboard-category-sales'],
    queryFn: () => api.get('/api/v1/dashboard/sales-by-category').then((res) => res.data),
    staleTime: 30000,
  })

  // Fetch top products
  const { data: topProductsData, isLoading: productsLoading, isError: productsError } = useQuery({
    queryKey: ['dashboard-top-products'],
    queryFn: () => api.get('/api/v1/dashboard/top-products?limit=5').then((res) => res.data),
    staleTime: 30000,
  })

  // Fetch outlet performance (if super admin)
  const isSuperAdmin = user?.role === 'super_admin'
  const { data: outletData, isLoading: outletLoading, isError: outletError } = useQuery({
    queryKey: ['dashboard-outlet-performance'],
    queryFn: () => api.get('/api/v1/dashboard/outlet-performance').then((res) => res.data),
    enabled: isSuperAdmin,
    staleTime: 30000,
  })

  // Extract values from summary
  const safeData = summary || {}
  const revenueToday = safeData.total_revenue_today || 0
  const revenueTodayChange = safeData.revenue_change_percent || 0
  const revenueThisMonth = safeData.total_revenue_this_month || 0
  const transactionsToday = safeData.total_transactions_today || 0
  const alertsCount = safeData.low_stock_alerts_count || 0
  const summaryText = safeData.summary_text || `${alertsCount} active alerts`

  return (
    <div className="dashboard">
      {/* GREETING SECTION */}
      <div className="dashboard-greeting-section">
        <div>
          <h1 className="greeting-title">Good morning, {user?.name || 'User'}</h1>
          <p className="greeting-subtitle">{today}</p>
          <p className="greeting-summary">{summaryText}</p>
        </div>
      </div>

      {/* STAT CARDS ROW */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 lg:gap-5 md:gap-3">
        {summaryLoading ? (
          <>
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="skeleton-item stat-card-height" />
            ))}
          </>
        ) : summaryError ? (
          <div className="dashboard-error lg:col-span-4 md:col-span-2">
            <AlertCircle size={20} />
            <span>Failed to load metrics</span>
            <button onClick={() => refetchSummary()}>Retry</button>
          </div>
        ) : (
          <>
            <StatCard
              title="Today's Revenue"
              value={fmtINR(revenueToday)}
              change={`${Math.abs(revenueTodayChange).toFixed(1)}%`}
              changeType={revenueTodayChange >= 0 ? 'up' : 'down'}
              colorVariant="yellow"
              trend="vs yesterday"
            />
            <StatCard
              title="This Month's Revenue"
              value={fmtINR(revenueThisMonth)}
              colorVariant="green"
            />
            <StatCard
              title="Today's Transactions"
              value={fmtNum(transactionsToday)}
              colorVariant="blue"
            />
            <StatCard
              title="Active Alerts"
              value={fmtNum(alertsCount)}
              colorVariant="pink"
            />
          </>
        )}
      </div>

      {/* TWO COLUMN SECTION */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-5">
        {/* LEFT COLUMN */}
        <div className="flex flex-col gap-6 md:gap-5">
          {/* Revenue Trend Chart */}
          <div className="dashboard-card">
            <h3 className="card-title">Revenue Trend</h3>
            <p className="card-subtitle">Last 30 days</p>
            {trendLoading ? (
              <GradientSkeleton />
            ) : trendError ? (
              <div className="card-error">Unable to load revenue data</div>
            ) : (
              <div className="chart-wrapper">
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={revenueTrendData || []}>
                    <CartesianGrid strokeDasharray="0" stroke="#F3F4F6" vertical={false} />
                    <XAxis
                      dataKey="date"
                      stroke="#9CA3AF"
                      style={{ fontSize: '12px' }}
                      tickFormatter={(date) => {
                        if (!date) return ''
                        const d = new Date(date)
                        return `${d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`
                      }}
                    />
                    <YAxis
                      stroke="#9CA3AF"
                      style={{ fontSize: '12px' }}
                      tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#FFFFFF',
                        border: '1px solid #E5E7EB',
                        borderRadius: '8px',
                      }}
                      formatter={(val) => fmtINR(val)}
                      labelFormatter={(date) => new Date(date).toLocaleDateString()}
                    />
                    <Line
                      type="monotone"
                      dataKey="revenue"
                      stroke="#1A1A1A"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Top Products List */}
          <div className="dashboard-card">
            <h3 className="card-title">Top Products This Week</h3>
            <p className="card-subtitle">Ranked by revenue</p>
            {productsLoading ? (
              <TableSkeleton />
            ) : productsError ? (
              <div className="card-error">Unable to load products</div>
            ) : (
              <div className="products-list">
                {(topProductsData || []).slice(0, 5).map((product, idx) => {
                    const maxRevenue = (topProductsData || [])[0]?.revenue || 1
                    const progressPercent = (product.revenue / maxRevenue) * 100
                    const mobileHiddenClass = idx > 2 ? 'hidden md:flex' : 'flex'
                    return (
                      <div key={idx} className={`${mobileHiddenClass} product-item`}>
                        <div className="product-rank">{idx + 1}</div>
                        <div className="product-info">
                          <div className="product-name">{product.name}</div>
                          <div className="product-category">
                            <Badge label={product.category || 'Other'} variant="neutral" />
                          </div>
                        </div>
                        <div className="product-revenue">{fmtINR(product.revenue)}</div>
                        <div className="product-progress">
                          <div className="progress-bar">
                            <div
                              className="progress-fill"
                              style={{ width: `${progressPercent}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    )
                  })}
              </div>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN */}
        <div className="flex flex-col gap-6 md:gap-5">
          {/* Sales by Category Pie Chart */}
          <div className="dashboard-card">
            <h3 className="card-title">Sales by Category</h3>
            <p className="card-subtitle">Category breakdown</p>
            {categoryLoading ? (
              <GradientSkeleton />
            ) : categoryError ? (
              <div className="card-error">Unable to load category data</div>
            ) : (
              <div className="chart-wrapper">
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie
                      data={categorySalesData || []}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {(categorySalesData || []).map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(val) => fmtINR(val)} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="chart-legend">
                  {(categorySalesData || []).map((cat, idx) => (
                    <div key={idx} className="legend-item">
                      <div
                        className="legend-color"
                        style={{ backgroundColor: CHART_COLORS[idx % CHART_COLORS.length] }}
                      ></div>
                      <span className="legend-label">{cat.name}</span>
                      <span className="legend-percent">{cat.percent}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="dashboard-card">
            <h3 className="card-title">Quick Actions</h3>
            <p className="card-subtitle">Common tasks</p>
            <div className="quick-actions">
              <button
                className="action-button"
                onClick={() => navigate('/inventory')}
              >
                <Eye size={18} />
                View Inventory
              </button>
              <button className="action-button" onClick={() => navigate('/sales')}>
                <Plus size={18} />
                Add Sale
              </button>
              <button className="action-button" onClick={() => navigate('/reports')}>
                <FileText size={18} />
                Generate Report
              </button>
              <button className="action-button" onClick={() => navigate('/alerts')}>
                <AlertCircle size={18} />
                View Alerts
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* OUTLET PERFORMANCE (Super Admin Only) */}
      {isSuperAdmin && (
        <div className="dashboard-card full-width">
          <h3 className="card-title">Outlet Performance</h3>
          <p className="card-subtitle">Revenue, transactions, and alerts across all outlets</p>
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
                    <th>Avg Basket Size</th>
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
                      <td>
                        <Badge
                          label={outlet.alerts.toString()}
                          variant={outlet.alerts > 0 ? 'danger' : 'success'}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
