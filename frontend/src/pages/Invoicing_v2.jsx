import React, { useState, useEffect } from 'react';
import { Plus, Download, Send, Mail, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import PaginationControls from '../ui/PaginationControls';

export default function Invoicing() {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(50);
  const [totalInvoices, setTotalInvoices] = useState(0);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [paymentFilter, setPaymentFilter] = useState('');
  const [sendingEmail, setSendingEmail] = useState(false);
  const [emailRecipient, setEmailRecipient] = useState('');

  // Fetch invoices
  useEffect(() => {
    fetchInvoices();
  }, [page, perPage, statusFilter, paymentFilter]);

  // Clear messages after 5 seconds
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(''), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const fetchInvoices = async () => {
    setLoading(true);
    try {
      let url = `/api/v1/invoicing/invoices?page=${page}&per_page=${perPage}`;
      if (statusFilter) url += `&status=${statusFilter}`;
      if (paymentFilter) url += `&payment_status=${paymentFilter}`;

      const response = await fetch(url);
      const result = await response.json();

      if (result.success) {
        setInvoices(result.data.invoices);
        setTotalInvoices(result.data.pagination.total);
      } else {
        setError(result.error || 'Failed to fetch invoices');
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Fetch invoice details
  const viewInvoice = async (invoiceId) => {
    try {
      const response = await fetch(`/api/v1/invoicing/invoices/${invoiceId}`);
      const result = await response.json();

      if (result.success) {
        setSelectedInvoice(result.data);
        setEmailRecipient(result.data.customer_email);
      }
    } catch (err) {
      setError(`Error loading invoice: ${err.message}`);
    }
  };

  const downloadInvoice = (invoiceId) => {
    try {
      window.open(`/api/v1/invoicing/invoices/${invoiceId}/pdf`, '_blank');
      setSuccess('PDF download started');
    } catch (err) {
      setError('Failed to download PDF');
    }
  };

  const sendInvoiceEmail = async (invoiceId) => {
    if (!emailRecipient) {
      setError('Please enter a recipient email');
      return;
    }

    setSendingEmail(true);
    try {
      const response = await fetch(`/api/v1/invoicing/invoices/${invoiceId}/email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recipient_email: emailRecipient })
      });

      const result = await response.json();
      
      if (result.success) {
        setSuccess(`Invoice sent to ${emailRecipient}`);
        setSelectedInvoice(null);
        fetchInvoices();
      } else {
        setError(result.error || 'Failed to send email');
      }
    } catch (err) {
      setError(`Error sending email: ${err.message}`);
    } finally {
      setSendingEmail(false);
    }
  };

  const recordPayment = async (invoiceId) => {
    const amount = prompt('Enter payment amount:');
    if (!amount) return;

    try {
      const response = await fetch(`/api/v1/invoicing/invoices/${invoiceId}/pay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: parseFloat(amount),
          payment_method: 'bank_transfer',
          notes: 'Payment recorded from system'
        })
      });

      const result = await response.json();
      if (result.success) {
        setSuccess('Payment recorded successfully');
        setSelectedInvoice(null);
        fetchInvoices();
      } else {
        setError(result.error || 'Payment failed');
      }
    } catch (err) {
      setError(`Error recording payment: ${err.message}`);
    }
  };

  const getStatusBadge = (status, paymentStatus) => {
    const statusColors = {
      draft: 'bg-gray-100 text-gray-800',
      sent: 'bg-blue-100 text-blue-800',
      paid: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800'
    };

    const paymentColors = {
      unpaid: 'bg-red-100 text-red-800',
      partially_paid: 'bg-yellow-100 text-yellow-800',
      paid: 'bg-green-100 text-green-800'
    };

    return (
      <div className="flex gap-2">
        <span className={`px-2 py-1 rounded text-xs font-medium ${statusColors[status] || 'bg-gray-100'}`}>
          {status}
        </span>
        <span className={`px-2 py-1 rounded text-xs font-medium ${paymentColors[paymentStatus] || 'bg-gray-100'}`}>
          {paymentStatus?.replace('_', ' ')}
        </span>
      </div>
    );
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Invoicing</h1>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus size={20} /> Create Invoice
        </button>
      </div>

      {/* Success Message */}
      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex gap-3">
          <CheckCircle className="text-green-600 flex-shrink-0" size={20} />
          <div>
            <h3 className="font-semibold text-green-900">Success</h3>
            <p className="text-green-700">{success}</p>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex gap-3">
          <AlertCircle className="text-red-600 flex-shrink-0" size={20} />
          <div>
            <h3 className="font-semibold text-red-900">Error</h3>
            <p className="text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4 bg-white p-4 rounded-lg shadow">
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2 border border-gray-300 rounded-lg"
        >
          <option value="">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="sent">Sent</option>
          <option value="paid">Paid</option>
          <option value="cancelled">Cancelled</option>
        </select>

        <select
          value={paymentFilter}
          onChange={(e) => {
            setPaymentFilter(e.target.value);
            setPage(1);
          }}
          className="px-3 py-2 border border-gray-300 rounded-lg"
        >
          <option value="">All Payment Status</option>
          <option value="unpaid">Unpaid</option>
          <option value="partially_paid">Partially Paid</option>
          <option value="paid">Paid</option>
        </select>
      </div>

      {/* Invoices Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700">Invoice #</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700">Customer</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700">Date</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-700">Amount</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-700">Balance</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700">Status</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {loading ? (
                <tr>
                  <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                    Loading invoices...
                  </td>
                </tr>
              ) : invoices.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-4 text-center text-gray-500">
                    No invoices found
                  </td>
                </tr>
              ) : (
                invoices.map((invoice) => (
                  <tr key={invoice.invoice_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium text-gray-900">{invoice.invoice_number}</td>
                    <td className="px-6 py-4 text-gray-700">{invoice.customer_name}</td>
                    <td className="px-6 py-4 text-gray-700">
                      {new Date(invoice.invoice_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right font-medium text-gray-900">
                      ₹{invoice.total_amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4 text-right text-gray-700">
                      ₹{invoice.balance_amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(invoice.status, invoice.payment_status)}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <button
                        onClick={() => viewInvoice(invoice.invoice_id)}
                        className="text-blue-600 hover:text-blue-800 font-medium"
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <PaginationControls
          page={page}
          perPage={perPage}
          total={totalInvoices}
          onPageChange={setPage}
          onPerPageChange={setPerPage}
        />
      </div>

      {/* Invoice Detail Modal */}
      {selectedInvoice && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-gray-50 border-b p-6 flex justify-between items-center">
              <h2 className="text-2xl font-bold">{selectedInvoice.invoice_number}</h2>
              <button
                onClick={() => setSelectedInvoice(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Customer & Date Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Customer</p>
                  <p className="font-semibold">{selectedInvoice.customer_name}</p>
                  <p className="text-sm text-gray-600">{selectedInvoice.customer_email}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Invoice Date</p>
                  <p className="font-semibold">
                    {new Date(selectedInvoice.invoice_date).toLocaleDateString()}
                  </p>
                  <p className="text-sm text-gray-600">
                    Due: {new Date(selectedInvoice.due_date).toLocaleDateString()}
                  </p>
                </div>
              </div>

              {/* Line Items */}
              <div>
                <h3 className="font-semibold mb-3">Line Items</h3>
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b">
                    <tr>
                      <th className="px-3 py-2 text-left">Product</th>
                      <th className="px-3 py-2 text-right">Qty</th>
                      <th className="px-3 py-2 text-right">Price</th>
                      <th className="px-3 py-2 text-right">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {selectedInvoice.line_items.map((item, idx) => (
                      <tr key={idx}>
                        <td className="px-3 py-2">{item.product_name}</td>
                        <td className="px-3 py-2 text-right">{item.quantity}</td>
                        <td className="px-3 py-2 text-right">
                          ₹{item.unit_price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-3 py-2 text-right font-medium">
                          ₹{item.line_total_with_tax.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Totals */}
              <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span>₹{selectedInvoice.subtotal.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between text-blue-600">
                  <span>GST ({selectedInvoice.line_items[0]?.gst_rate || 18}%)</span>
                  <span>₹{selectedInvoice.gst_amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                </div>
                {selectedInvoice.tds_amount > 0 && (
                  <div className="flex justify-between text-orange-600">
                    <span>TDS</span>
                    <span>-₹{selectedInvoice.tds_amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                  </div>
                )}
                <div className="flex justify-between font-bold text-lg border-t pt-2">
                  <span>Total Amount</span>
                  <span>₹{selectedInvoice.total_amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between text-green-600">
                  <span>Amount Paid</span>
                  <span>₹{selectedInvoice.amount_paid.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                </div>
                <div className="flex justify-between text-red-600 font-semibold">
                  <span>Balance Due</span>
                  <span>₹{selectedInvoice.balance_amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</span>
                </div>
              </div>

              {/* Email Section */}
              <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg space-y-3">
                <h3 className="font-semibold text-blue-900">Send Invoice</h3>
                <input
                  type="email"
                  value={emailRecipient}
                  onChange={(e) => setEmailRecipient(e.target.value)}
                  placeholder="Email address"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
                <button
                  onClick={() => sendInvoiceEmail(selectedInvoice.invoice_id)}
                  disabled={sendingEmail}
                  className="w-full flex items-center justify-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {sendingEmail ? <Loader size={18} className="animate-spin" /> : <Mail size={18} />}
                  {sendingEmail ? 'Sending...' : 'Send Invoice Email'}
                </button>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  onClick={() => downloadInvoice(selectedInvoice.invoice_id)}
                  className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
                >
                  <Download size={18} /> Download PDF
                </button>

                {selectedInvoice.payment_status !== 'paid' && (
                  <button
                    onClick={() => recordPayment(selectedInvoice.invoice_id)}
                    className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
                  >
                    <Send size={18} /> Record Payment
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
