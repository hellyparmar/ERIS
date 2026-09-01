import React, { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import SEO from '../components/SEO'
import api from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import InstrumentPanel from '../components/patterns/InstrumentPanel'
import HeatCanvas from '../components/patterns/HeatCanvas'
import Spotlight from '../components/patterns/Spotlight'

const fmtINR = (val) => {
  if (!val) return '\u20B90'
  const num = parseInt(val, 10)
  if (isNaN(num)) return '\u20B90'
  return '\u20B9' + num.toLocaleString('en-IN')
}

const fmtNum = (val) => {
  if (!val) return '0'
  const num = parseInt(val, 10)
  if (isNaN(num)) return '0'
  return num.toLocaleString('en-IN')
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { user = {} } = useAuth()

  const today = useMemo(() => new Date().toLocaleDateString('en-GB', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  }), [])

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => api.get('/api/v1/analytics/dashboard/summary').then(r => r.data),
  })

  const { data: revenueTrend, isLoading: trendLoading } = useQuery({
    queryKey: ['dashboard-revenue-trend'],
    queryFn: () => api.get('/api/v1/analytics/dashboard/revenue-trend?days=30').then(r => r.data),
  })

  const { data: topProducts, isLoading: productsLoading } = useQuery({
    queryKey: ['dashboard-top-products'],
    queryFn: () => api.get('/api/v1/analytics/dashboard/top-products?limit=5').then(r => r.data),
  })

  const sd = summary || {}
  const revenueToday = sd.total_revenue_today || 0
  const revenueTodayChange = sd.revenue_change_percent || 0
  const revenueMonth = sd.total_revenue_this_month || 0
  const transactionsToday = sd.total_transactions_today || 0
  const alertsCount = sd.low_stock_alerts_count || 0

  const gauges = [
    {
      label: 'Revenue Today',
      value: fmtINR(revenueToday),
      delta: revenueTodayChange,
      deltaUp: revenueTodayChange >= 0,
    },
    {
      label: 'Monthly Revenue',
      value: fmtINR(revenueMonth),
    },
    {
      label: 'Transactions',
      value: fmtNum(transactionsToday),
    },
    {
      label: 'Active Alerts',
      value: fmtNum(alertsCount),
      danger: alertsCount > 0,
    },
  ]

  const spotlightItems = (topProducts || []).slice(0, 5).map((p, i) => ({
    rank: i + 1,
    label: p.name,
    subtitle: p.category || 'Other',
    value: fmtINR(p.revenue),
    barValue: p.revenue,
    maxBarValue: topProducts?.[0]?.revenue || 1,
  }))

  return (
    <>
      <SEO title="Dashboard" description="Real-time retail analytics" />
      <div>

        <div style={{ marginBottom: 'var(--sp-6)' }}>
          <div style={{
            fontFamily: 'var(--font-serif)', fontSize: 26, fontWeight: 700,
            color: 'var(--color-ink)', lineHeight: 1.15,
          }}>
            Good {new Date().getHours() < 12 ? 'morning' : 'afternoon'}, {user.name || 'User'}
          </div>
          <div style={{ fontSize: 13, color: 'var(--color-ink-muted)', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
            {today}
          </div>
        </div>

        <div style={{ marginBottom: 'var(--sp-6)' }}>
          <InstrumentPanel
            gauges={gauges}
            loading={summaryLoading}
            columns={4}
            title=""
          />
        </div>

        <div style={{ marginBottom: 'var(--sp-6)' }}>
          <HeatCanvas
            title="Revenue Trend"
            subtitle="Last 30 days"
            loading={trendLoading}
            empty={!revenueTrend || revenueTrend.length === 0}
            emptyMessage="No revenue data available for this period"
            minWidth={600}
          >
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={revenueTrend}>
                <defs>
                  <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-amber)" stopOpacity={0.12} />
                    <stop offset="95%" stopColor="var(--color-amber)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-line)" vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke="var(--color-ink-faint)"
                  style={{ fontSize: 12, fontFamily: 'var(--font-mono)' }}
                  tickFormatter={(d) => d ? new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : ''}
                />
                <YAxis
                  stroke="var(--color-ink-faint)"
                  style={{ fontSize: 12, fontFamily: 'var(--font-mono)' }}
                  tickFormatter={(v) => `\u20B9${(v / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  contentStyle={{
                    background: 'var(--color-navy-deep)', border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: 8, fontSize: 13, color: '#f4f2ed',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.4)', fontFamily: 'var(--font-mono)',
                  }}
                  formatter={(v) => [fmtINR(v), 'Revenue']}
                  labelFormatter={(d) => new Date(d).toLocaleDateString()}
                />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="var(--color-amber)"
                  strokeWidth={2}
                  fill="url(#revGrad)"
                  dot={false}
                  animationDuration={800}
                />
              </AreaChart>
            </ResponsiveContainer>
          </HeatCanvas>
        </div>

        <div style={{ marginBottom: 'var(--sp-6)' }}>
          <Spotlight
            title="Top Products This Week"
            subtitle="Ranked by revenue"
            items={spotlightItems}
            loading={productsLoading}
            empty={!topProducts || topProducts.length === 0}
            emptyMessage="No product data available for this period"
          />
        </div>

      </div>
    </>
  )
}
