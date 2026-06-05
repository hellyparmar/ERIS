import React from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, TrendingDown, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Alert, AlertDescription } from '../components/ui/Alert'
import { formatCurrency, formatNumber } from '../utils/utils'

// Defensive helpers for NaN/undefined values
const safe = (v: any, fallback = '—') => (v == null || isNaN(v) || v === '') ? fallback : v
const fmtINR = (v: any) => v == null || isNaN(v) ? '—' : '₹' + Number(v).toLocaleString('en-IN')
const fmtPct = (v: any) => v == null || isNaN(v) ? '—' : `${v > 0 ? '+' : ''}${v}%`

// Sample data
const revenueData = [
  { date: 'Mar 1', revenue: 4200, target: 3000 },
  { date: 'Mar 5', revenue: 5600, target: 3000 },
  { date: 'Mar 10', revenue: 4800, target: 3000 },
  { date: 'Mar 15', revenue: 6200, target: 3000 },
  { date: 'Mar 20', revenue: 7100, target: 3000 },
  { date: 'Mar 25', revenue: 6800, target: 3000 },
  { date: 'Mar 28', revenue: 8200, target: 3000 },
]

const topProductsData = [
  { name: 'Coffee', sales: 4200 },
  { name: 'Tea', sales: 3800 },
  { name: 'Snacks', sales: 3200 },
  { name: 'Beverages', sales: 2800 },
  { name: 'Desserts', sales: 2100 },
]

const recentSales = [
  { id: '1', outlet: 'Mumbai', amount: 2500, items: 8, time: '2 hours ago' },
  { id: '2', outlet: 'Delhi', amount: 1800, items: 5, time: '4 hours ago' },
  { id: '3', outlet: 'Bangalore', amount: 3200, items: 12, time: '6 hours ago' },
  { id: '4', outlet: 'Hyderabad', amount: 1500, items: 4, time: '8 hours ago' },
]

interface KPICardProps {
  title: string
  value: string | number
  change: number
  icon: React.ReactNode
}

const KPICard: React.FC<KPICardProps> = ({ title, value, change, icon }) => (
  <Card>
    <CardContent className="p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <h3 className="text-2xl font-bold mt-2">{value}</h3>
          <div className="flex items-center mt-2">
            {change >= 0 ? (
              <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-600 mr-1" />
            )}
            <span className={change >= 0 ? 'text-green-600' : 'text-red-600'}>
              {Math.abs(change)}%
            </span>
          </div>
        </div>
        <div className="text-gray-400">{icon}</div>
      </div>
    </CardContent>
  </Card>
)

const Dashboard: React.FC = () => {
  // Memoized metrics with fallback for zero/null API values
  const metrics = React.useMemo(() => {
    const totalSales: number = 45800
    const orders: number = 284
    const customers: number = 1240
    const alertCount: number = 3

    return {
      totalSales: totalSales === 0 || totalSales == null ? '—' : formatCurrency(totalSales),
      orders: orders === 0 || orders == null ? '—' : formatNumber(orders),
      customers: customers === 0 || customers == null ? '—' : formatNumber(customers),
      alerts: alertCount === 0 || alertCount == null ? '—' : String(alertCount),
    }
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-gray-600 mt-1">Welcome back! Here's your sales overview.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Total Sales" value={metrics.totalSales} change={12.5} icon="₹" />
        <KPICard title="Orders" value={metrics.orders} change={8.2} icon="📦" />
        <KPICard title="Customers" value={metrics.customers} change={5.1} icon="👥" />
        <KPICard title="Alerts" value={metrics.alerts} change={-15.3} icon="⚠️" />
      </div>

      {/* Revenue Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Revenue Trend</CardTitle>
          <CardDescription>Sales performance over the last 30 days</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip formatter={(value) => formatCurrency(Number(value))} />
              <Legend />
              <Line type="monotone" dataKey="revenue" stroke="#2563eb" strokeWidth={2} name="Actual" />
              <Line type="monotone" dataKey="target" stroke="#cbd5e1" strokeWidth={2} strokeDasharray="5 5" name="Target" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Products */}
        <Card>
          <CardHeader>
            <CardTitle>Top Products</CardTitle>
            <CardDescription>Best performing products this month</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={topProductsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => formatNumber(Number(value))} />
                <Bar dataKey="sales" fill="#2563eb" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Low Stock Alerts */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Alerts</CardTitle>
              <CardDescription>Active notifications</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Alert variant="warning">
                <AlertCircle className="w-4 h-4 inline mr-2" />
                <AlertDescription>
                  <strong>Low Stock:</strong> Coffee inventory below threshold (15 units)
                </AlertDescription>
              </Alert>
              <Alert variant="error">
                <AlertCircle className="w-4 h-4 inline mr-2" />
                <AlertDescription>
                  <strong>High Demand:</strong> Tea sales spike detected (+45% vs average)
                </AlertDescription>
              </Alert>
              <Alert variant="warning">
                <AlertCircle className="w-4 h-4 inline mr-2" />
                <AlertDescription>
                  <strong>Outlet Issue:</strong> Delhi outlet system offline for 2 hours
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Stats</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Avg Order Value</span>
                  <span className="font-semibold">{fmtINR(432)}</span>
                </div>
                <div className="flex justify-between border-t pt-3">
                  <span className="text-gray-600">Conversion Rate</span>
                  <span className="font-semibold">{fmtPct(3.2)}</span>
                </div>
                <div className="flex justify-between border-t pt-3">
                  <span className="text-gray-600">Avg Items/Sale</span>
                  <span className="font-semibold">{safe(5.2)}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Recent Sales Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Sales</CardTitle>
          <CardDescription>Latest transactions from all outlets</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 font-semibold">Outlet</th>
                  <th className="text-right py-3 font-semibold">Amount</th>
                  <th className="text-center py-3 font-semibold">Items</th>
                  <th className="text-right py-3 font-semibold">Time</th>
                </tr>
              </thead>
              <tbody>
                {recentSales.map((sale) => (
                  <tr key={sale.id} className="border-b hover:bg-gray-50">
                    <td className="py-3">{sale.outlet}</td>
                    <td className="text-right font-semibold">{formatCurrency(sale.amount)}</td>
                    <td className="text-center">{sale.items}</td>
                    <td className="text-right text-gray-600">{sale.time}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Dashboard
