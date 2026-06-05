import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'

// Defensive helpers for currency and percentage formatting
const fmtINR = (v: any) => v == null || isNaN(v) ? '—' : '₹' + Number(v).toLocaleString('en-IN')
const fmtPct = (v: any) => v == null || isNaN(v) ? '—' : `${v > 0 ? '+' : ''}${v}%`

const outletsData = [
  { name: 'Mumbai', sales: 45800, orders: 284, customers: 520, growth: 12.5 },
  { name: 'Delhi', sales: 32100, orders: 198, customers: 380, growth: -5.2 },
  { name: 'Bangalore', sales: 28900, orders: 175, customers: 340, growth: 8.1 },
  { name: 'Hyderabad', sales: 18500, orders: 112, customers: 220, growth: 3.5 },
  { name: 'Pune', sales: 15300, orders: 95, customers: 185, growth: 15.8 },
]

const Outlets: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Outlets</h1>
        <p className="text-gray-600 mt-1">Performance comparison across all retail locations</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Outlet Performance</CardTitle>
          <CardDescription>Sales and growth metrics by location</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={outletsData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="sales" fill="#2563eb" name="Sales (₹)" />
              <Bar dataKey="orders" fill="#10b981" name="Orders" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Outlet Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 font-semibold">Outlet</th>
                    <th className="text-right py-3 font-semibold">Sales</th>
                    <th className="text-right py-3 font-semibold">Orders</th>
                    <th className="text-right py-3 font-semibold">Growth</th>
                  </tr>
                </thead>
                <tbody>
                  {outletsData.map((outlet) => (
                    <tr key={outlet.name} className="border-b hover:bg-gray-50">
                      <td className="py-3 font-medium">{outlet.name}</td>
                      <td className="text-right">{fmtINR(outlet.sales)}</td>
                      <td className="text-right">{outlet.orders}</td>
                      <td className={`text-right font-semibold ${outlet.growth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {fmtPct(outlet.growth)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top Outlet</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Location</span>
                  <span className="font-semibold">Mumbai</span>
                </div>
                <div className="flex justify-between border-t pt-3">
                  <span className="text-gray-600">Total Sales</span>
                  <span className="font-semibold">{fmtINR(outletsData[0].sales)}</span>
                </div>
                <div className="flex justify-between border-t pt-3">
                  <span className="text-gray-600">Customers</span>
                  <span className="font-semibold">{outletsData[0].customers}</span>
                </div>
                <div className="flex justify-between border-t pt-3">
                  <span className="text-gray-600">Growth Rate</span>
                  <span className="font-semibold text-green-600">{fmtPct(outletsData[0].growth)}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Outlet Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {outletsData.map((outlet) => (
                  <div key={outlet.name} className="flex items-center justify-between">
                    <span className="text-sm">{outlet.name}</span>
                    <div className="flex items-center">
                      <div className="w-24 bg-gray-200 h-2 rounded mr-2"></div>
                      <span className="text-xs text-gray-600">
                        {Math.round((outlet.sales / outletsData[0].sales) * 100)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default Outlets
