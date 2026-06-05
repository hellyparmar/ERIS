import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Button } from '../components/ui/Button'
import { Select } from '../components/ui/Select'

// Defensive helpers for currency formatting
const fmtINR = (v: any) => v == null || isNaN(v) ? '—' : '₹' + Number(v).toLocaleString('en-IN')

const Sales: React.FC = () => {
  const [filterOutlet, setFilterOutlet] = React.useState('all')

  const outlets = [
    { value: 'all', label: 'All Outlets' },
    { value: 'mumbai', label: 'Mumbai' },
    { value: 'delhi', label: 'Delhi' },
    { value: 'bangalore', label: 'Bangalore' },
  ]

  const sales = [
    { id: '1', date: '2026-03-28 10:30', outlet: 'Mumbai', customer: 'Walk-in', amount: 2500, items: 8, paymentMethod: 'Cash' },
    { id: '2', date: '2026-03-28 09:15', outlet: 'Delhi', customer: 'Reg-001', amount: 1800, items: 5, paymentMethod: 'Card' },
    { id: '3', date: '2026-03-28 08:45', outlet: 'Bangalore', customer: 'Walk-in', amount: 3200, items: 12, paymentMethod: 'UPI' },
    { id: '4', date: '2026-03-27 18:20', outlet: 'Mumbai', customer: 'Reg-002', amount: 1500, items: 4, paymentMethod: 'Cash' },
    { id: '5', date: '2026-03-27 15:40', outlet: 'Delhi', customer: 'Walk-in', amount: 2100, items: 7, paymentMethod: 'Card' },
  ]

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Sales</h1>
          <p className="text-gray-600 mt-1">View and manage all sales transactions</p>
        </div>
        <Button>New Sale</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Input placeholder="Search transaction ID..." />
        <Select label="Outlet" value={filterOutlet} onChange={(e) => setFilterOutlet(e.target.value)} options={outlets} />
        <Input type="date" label="Date Range" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Sales Transactions</CardTitle>
          <CardDescription>{sales.length} transactions found</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 font-semibold">Date & Time</th>
                  <th className="text-left py-3 font-semibold">Outlet</th>
                  <th className="text-left py-3 font-semibold">Customer</th>
                  <th className="text-right py-3 font-semibold">Items</th>
                  <th className="text-right py-3 font-semibold">Amount</th>
                  <th className="text-left py-3 font-semibold">Payment</th>
                  <th className="text-center py-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sales.map((sale) => (
                  <tr key={sale.id} className="border-b hover:bg-gray-50">
                    <td className="py-3">{sale.date}</td>
                    <td className="py-3">{sale.outlet}</td>
                    <td className="py-3">{sale.customer}</td>
                    <td className="text-right">{sale.items}</td>
                    <td className="text-right font-semibold">{fmtINR(sale.amount)}</td>
                    <td className="py-3">
                      <span className="px-2 py-1 bg-gray-100 rounded text-xs font-medium">{sale.paymentMethod}</span>
                    </td>
                    <td className="text-center">
                      <Button variant="ghost" size="sm">View</Button>
                    </td>
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

export default Sales
