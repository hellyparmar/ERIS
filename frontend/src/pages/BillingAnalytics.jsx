import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AlertCircle, TrendingUp, DollarSign, Clock } from 'lucide-react';

export default function BillingAnalytics() {
  const [gstData, setGstData] = useState([]);
  const [paymentData, setPaymentData] = useState(null);
  const [topCustomers, setTopCustomers] = useState([]);
  const [overdueInvoices, setOverdueInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const [gst, payment, customers, overdue] = await Promise.all([
        fetch('/api/v1/invoicing/analytics/gst-summary').then(r => r.json()),
        fetch('/api/v1/invoicing/analytics/payment-summary').then(r => r.json()),
        fetch('/api/v1/invoicing/analytics/revenue-by-customer?limit=10').then(r => r.json()),
        fetch('/api/v1/invoicing/analytics/overdue-invoices').then(r => r.json())
      ]);

      if (gst.success) setGstData(gst.data.gst_summary || []);
      if (payment.success) setPaymentData(payment.data);
      if (customers.success) setTopCustomers(customers.data.top_customers || []);
      if (overdue.success) setOverdueInvoices(overdue.data.overdue_invoices || []);
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-6 text-center">Loading analytics...</div>;
  }

  const COLORS = ['#3b82f6', '#ef4444', '#f59e0b', '#10b981', '#8b5cf6'];

  const paymentStatusData = paymentData ? [
    { name: 'Unpaid', value: paymentData.summary_by_status.unpaid.count, amount: paymentData.summary_by_status.unpaid.value },
    { name: 'Partial', value: paymentData.summary_by_status.partially_paid.count, amount: paymentData.summary_by_status.partially_paid.value },
    { name: 'Paid', value: paymentData.summary_by_status.paid.count, amount: paymentData.summary_by_status.paid.value }
  ] : [];

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Billing Analytics</h1>
        <button
          onClick={fetchAnalytics}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex gap-3">
          <AlertCircle className="text-red-600" size={20} />
          <div>
            <h3 className="font-semibold text-red-900">Error</h3>
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Invoiced</p>
              <p className="text-2xl font-bold text-gray-900">
                ₹{paymentData?.total_invoiced.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <DollarSign className="text-blue-600" size={32} />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Collected</p>
              <p className="text-2xl font-bold text-green-600">
                ₹{paymentData?.total_collected.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <TrendingUp className="text-green-600" size={32} />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Collection Rate</p>
              <p className="text-2xl font-bold text-purple-600">
                {paymentData?.collection_rate.toFixed(1)}%
              </p>
            </div>
            <BarChart width={40} height={40} data={[{ v: paymentData?.collection_rate }]}>
              <Bar dataKey="v" fill="#8b5cf6" radius={4} />
            </BarChart>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Overdue Amount</p>
              <p className="text-2xl font-bold text-red-600">
                ₹{overdueInvoices.reduce((sum, inv) => sum + inv.balance_amount, 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <AlertCircle className="text-red-600" size={32} />
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* GST Collection Trend */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-bold mb-4">GST Collection Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={gstData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value) => `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`} />
              <Legend />
              <Line type="monotone" dataKey="total_gst" stroke="#3b82f6" name="GST Amount" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Payment Status Distribution */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-bold mb-4">Payment Status Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={paymentStatusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {paymentStatusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Customers */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-bold mb-4">Top 10 Customers by Revenue</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700">Rank</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700">Customer</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-700">Invoices</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-700">Revenue</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {topCustomers.map((customer, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-bold text-gray-900">{idx + 1}</td>
                  <td className="px-6 py-4 text-gray-700">{customer.customer_name}</td>
                  <td className="px-6 py-4 text-center text-gray-700">{customer.invoice_count}</td>
                  <td className="px-6 py-4 text-right font-medium text-gray-900">
                    ₹{customer.total_revenue.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Overdue Invoices */}
      {overdueInvoices.length > 0 && (
        <div className="bg-red-50 rounded-lg shadow p-6 border border-red-200">
          <div className="flex items-center gap-2 mb-4">
            <AlertCircle className="text-red-600" size={24} />
            <h2 className="text-lg font-bold text-red-900">
              {overdueInvoices.length} Overdue Invoices
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-red-100 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-red-900">Invoice</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-red-900">Customer</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-red-900">Days Overdue</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-red-900">Balance</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {overdueInvoices.slice(0, 10).map((invoice, idx) => (
                  <tr key={idx} className="hover:bg-red-100">
                    <td className="px-6 py-4 font-medium text-gray-900">{invoice.invoice_number}</td>
                    <td className="px-6 py-4 text-gray-700">{invoice.customer_name}</td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        invoice.days_overdue > 90
                          ? 'bg-red-600 text-white'
                          : invoice.days_overdue > 30
                          ? 'bg-orange-600 text-white'
                          : 'bg-yellow-600 text-white'
                      }`}>
                        {invoice.days_overdue} days
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right font-medium text-red-600">
                      ₹{invoice.balance_amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
