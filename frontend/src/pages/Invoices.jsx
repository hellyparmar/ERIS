import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import {
  Search,
  Plus,
  Eye,
  Trash2,
  X,
  Printer,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import LoadingSkeleton from '../components/ui/LoadingSkeleton';

const API_BASE = 'http://localhost:8000/api/v1';

// Summary Stat Card
const StatCard = ({ label, value, color }) => {
  const colors = {
    green: 'bg-green-50 text-green-800 border-green-200',
    amber: 'bg-amber-50 text-amber-800 border-amber-200',
    red: 'bg-red-50 text-red-800 border-red-200',
  };

  return (
    <div className={`border rounded-lg p-4 ${colors[color] || colors.green}`}>
      <p className="text-sm font-medium">{label}</p>
      <p className="text-2xl font-bold mt-2">₹{value.toLocaleString('en-IN')}</p>
    </div>
  );
};

// View Invoice Modal
const ViewInvoiceModal = ({ invoice, contacts, onClose }) => {
  if (!invoice) return null;

  const supplier = contacts?.find(c => c.id === invoice.supplier_id);
  const items = invoice.items || [];
  const subtotal = items.reduce((sum, item) => sum + (item.unit_price * item.quantity), 0);
  const tax = invoice.tax_amount || subtotal * 0.18;
  const total = invoice.total || subtotal + tax;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-96 overflow-auto">
        <div className="flex justify-between items-center p-6 border-b sticky top-0 bg-white">
          <h2 className="text-lg font-bold">Invoice {invoice.invoice_number}</h2>
          <button
            onClick={onClose}
            className="hover:bg-gray-100 p-1 rounded"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Header */}
          <div className="flex justify-between border-b pb-4">
            <div>
              <h1 className="text-2xl font-bold">ERIS</h1>
              <p className="text-sm text-gray-500">Enterprise Retail Intelligence System</p>
            </div>
            <div className="text-right">
              <p className="font-mono font-bold">{invoice.invoice_number}</p>
              <p className="text-sm text-gray-500">
                {new Date(invoice.issue_date).toLocaleDateString()}
              </p>
            </div>
          </div>

          {/* Supplier Details */}
          <div>
            <p className="text-sm font-bold text-gray-500 uppercase">From:</p>
            <p className="font-bold text-lg">{supplier?.company_name || 'N/A'}</p>
            {supplier?.contact_person && <p className="text-sm">{supplier.contact_person}</p>}
            {supplier?.phone && <p className="text-sm text-blue-600">{supplier.phone}</p>}
            {supplier?.email && <p className="text-sm text-blue-600">{supplier.email}</p>}
          </div>

          {/* Items Table */}
          <div>
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left px-4 py-2 font-bold">Description</th>
                  <th className="text-right px-4 py-2 font-bold">Qty</th>
                  <th className="text-right px-4 py-2 font-bold">Unit Price</th>
                  <th className="text-right px-4 py-2 font-bold">Amount</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item, idx) => (
                  <tr key={idx} className="border-b">
                    <td className="px-4 py-2">{item.description}</td>
                    <td className="text-right px-4 py-2">{item.quantity}</td>
                    <td className="text-right px-4 py-2">₹{(item.unit_price || 0).toLocaleString('en-IN')}</td>
                    <td className="text-right px-4 py-2">
                      ₹{(item.quantity * item.unit_price).toLocaleString('en-IN')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Summary */}
          <div className="border-t pt-4 space-y-2">
            <div className="flex justify-end gap-32">
              <span className="text-sm">Subtotal:</span>
              <span className="font-mono">₹{subtotal.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-end gap-32">
              <span className="text-sm">Tax (18% GST):</span>
              <span className="font-mono">₹{tax.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-end gap-32 border-t pt-2 font-bold text-lg">
              <span>Total:</span>
              <span className="font-mono">₹{total.toLocaleString('en-IN')}</span>
            </div>
          </div>

          {/* Status */}
          <div className="flex justify-between items-center border-t pt-4">
            <div>
              <p className="text-sm text-gray-500">Status</p>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                invoice.status === 'paid' ? 'bg-green-100 text-green-800' :
                invoice.status === 'pending' ? 'bg-amber-100 text-amber-800' :
                'bg-red-100 text-red-800'
              }`}>
                {invoice.status?.charAt(0).toUpperCase() + invoice.status?.slice(1)}
              </span>
            </div>
            <button
              onClick={() => window.print()}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <Printer size={16} />
              Print
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Create Invoice Modal
const CreateInvoiceModal = ({ contacts, onClose, onSuccess }) => {
  const getDefaultDueDate = () => {
    const date = new Date();
    date.setDate(date.getDate() + 30);
    return date.toISOString().split('T')[0];
  };

  const [formData, setFormData] = useState({
    supplier_id: '',
    outlet_id: '',
    issue_date: new Date().toISOString().split('T')[0],
    due_date: getDefaultDueDate(),
    items: [{ description: '', quantity: 1, unit_price: 0 }],
    tax_rate: 18,
    notes: '',
  });

  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: async (data) => {
      const items = data.items.filter(i => i.description && i.quantity && i.unit_price);
      const subtotal = items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
      const tax_amount = subtotal * (data.tax_rate / 100);
      const total = subtotal + tax_amount;

      const payload = {
        supplier_id: parseInt(data.supplier_id),
        outlet_id: data.outlet_id ? parseInt(data.outlet_id) : 1,
        invoice_number: `INV-${Date.now()}`,
        issue_date: data.issue_date,
        due_date: data.due_date,
        items,
        tax_rate: data.tax_rate,
        tax_amount,
        total,
        status: 'pending',
        notes: data.notes,
      };

      return axios.post(`${API_BASE}/invoices`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      onSuccess?.();
      onClose();
    },
  });

  const handleAddItem = () => {
    setFormData(prev => ({
      ...prev,
      items: [...prev.items, { description: '', quantity: 1, unit_price: 0 }],
    }));
  };

  const handleRemoveItem = (idx) => {
    setFormData(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== idx),
    }));
  };

  const handleItemChange = (idx, field, value) => {
    const newItems = [...formData.items];
    newItems[idx] = { ...newItems[idx], [field]: value };
    setFormData(prev => ({ ...prev, items: newItems }));
  };

  const subtotal = formData.items.reduce(
    (sum, item) => sum + (parseFloat(item.unit_price || 0) * parseFloat(item.quantity || 0)),
    0
  );
  const tax = subtotal * (formData.tax_rate / 100);
  const total = subtotal + tax;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-3xl w-full max-h-screen overflow-auto">
        <div className="flex justify-between items-center p-6 border-b sticky top-0 bg-white">
          <h2 className="text-lg font-bold">Create Invoice</h2>
          <button
            onClick={onClose}
            className="hover:bg-gray-100 p-1 rounded"
          >
            <X size={20} />
          </button>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate(formData);
          }}
          className="p-6 space-y-4"
        >
          {/* Supplier & Dates */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Supplier *</label>
              <select
                value={formData.supplier_id}
                onChange={(e) => setFormData(prev => ({ ...prev, supplier_id: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                required
              >
                <option value="">Select Supplier</option>
                {contacts?.map(c => (
                  <option key={c.id} value={c.id}>
                    {c.company_name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Outlet</label>
              <input
                type="text"
                value={formData.outlet_id || '1'}
                onChange={(e) => setFormData(prev => ({ ...prev, outlet_id: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                placeholder="Outlet ID"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Issue Date</label>
              <input
                type="date"
                value={formData.issue_date}
                onChange={(e) => setFormData(prev => ({ ...prev, issue_date: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Due Date</label>
              <input
                type="date"
                value={formData.due_date}
                onChange={(e) => setFormData(prev => ({ ...prev, due_date: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
          </div>

          {/* Items */}
          <div className="border-t pt-4">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-bold text-gray-900">Items</h3>
              <button
                type="button"
                onClick={handleAddItem}
                className="flex items-center gap-1 px-3 py-1 bg-blue-50 text-blue-600 rounded text-sm hover:bg-blue-100"
              >
                <Plus size={14} />
                Add Item
              </button>
            </div>

            <div className="space-y-2">
              {formData.items.map((item, idx) => (
                <div key={idx} className="flex gap-2 items-end">
                  <div className="flex-1">
                    <input
                      type="text"
                      value={item.description}
                      onChange={(e) => handleItemChange(idx, 'description', e.target.value)}
                      placeholder="Description"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      required={item.quantity > 0 || item.unit_price > 0}
                    />
                  </div>
                  <div className="w-24">
                    <input
                      type="number"
                      value={item.quantity}
                      onChange={(e) => handleItemChange(idx, 'quantity', parseFloat(e.target.value) || 0)}
                      placeholder="Qty"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      min="0"
                      step="0.01"
                    />
                  </div>
                  <div className="w-32">
                    <input
                      type="number"
                      value={item.unit_price}
                      onChange={(e) => handleItemChange(idx, 'unit_price', parseFloat(e.target.value) || 0)}
                      placeholder="Unit Price"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      min="0"
                      step="0.01"
                    />
                  </div>
                  <div className="w-32 text-right">
                    <span className="text-sm font-medium">
                      ₹{(item.quantity * item.unit_price).toLocaleString('en-IN')}
                    </span>
                  </div>
                  {formData.items.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveItem(idx)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded"
                    >
                      <X size={16} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Tax & Total */}
          <div className="border-t pt-4 space-y-2 bg-gray-50 p-3 rounded">
            <div className="flex justify-between text-sm">
              <span>Subtotal:</span>
              <span className="font-mono">₹{subtotal.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <div className="flex items-center gap-2">
                <span>Tax Rate (%):</span>
                <input
                  type="number"
                  value={formData.tax_rate}
                  onChange={(e) => setFormData(prev => ({ ...prev, tax_rate: parseFloat(e.target.value) || 0 }))}
                  className="w-16 px-2 py-1 border border-gray-300 rounded text-sm"
                  min="0"
                  max="100"
                  step="0.1"
                />
              </div>
              <span className="font-mono">₹{tax.toLocaleString('en-IN')}</span>
            </div>
            <div className="flex justify-between text-sm font-bold border-t pt-2">
              <span>Total:</span>
              <span className="font-mono">₹{total.toLocaleString('en-IN')}</span>
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
              placeholder="Additional notes..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              rows="3"
            />
          </div>

          {/* Buttons */}
          <div className="flex gap-2 border-t pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {mutation.isPending ? 'Creating...' : 'Create Invoice'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Main Invoices Page
export default function Invoices() {
  const [statusFilter, setStatusFilter] = useState('All');
  const [supplierSearch, setSupplierSearch] = useState('');
  const [dateFromFilter, setDateFromFilter] = useState('');
  const [dateToFilter, setDateToFilter] = useState('');
  const [viewingInvoice, setViewingInvoice] = useState(null);
  const [creatingInvoice, setCreatingInvoice] = useState(false);
  const queryClient = useQueryClient();

  const { data: invoices = [], isLoading } = useQuery({
    queryKey: ['invoices'],
    queryFn: async () => {
      const res = await axios.get(`${API_BASE}/invoices`);
      return res.data;
    },
  });

  const { data: contacts = [] } = useQuery({
    queryKey: ['contacts'],
    queryFn: async () => {
      const res = await axios.get(`${API_BASE}/contacts`);
      return res.data;
    },
  });

  const deleteInvoiceMutation = useMutation({
    mutationFn: (id) => axios.delete(`${API_BASE}/invoices/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
  });

  const markPaidMutation = useMutation({
    mutationFn: (id) =>
      axios.patch(`${API_BASE}/invoices/${id}`, { status: 'paid' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
  });

  // Filter invoices
  const filtered = useMemo(() => {
    return invoices
      .filter(inv => {
        const matchStatus = statusFilter === 'All' || inv.status === statusFilter.toLowerCase();
        const supplier = contacts.find(c => c.id === inv.supplier_id);
        const matchSupplier = !supplierSearch ||
          supplier?.company_name?.toLowerCase().includes(supplierSearch.toLowerCase());

        const issueDate = new Date(inv.issue_date);
        const matchFromDate = !dateFromFilter || issueDate >= new Date(dateFromFilter);
        const matchToDate = !dateToFilter || issueDate <= new Date(dateToFilter);

        return matchStatus && matchSupplier && matchFromDate && matchToDate;
      })
      .sort((a, b) => new Date(b.issue_date) - new Date(a.issue_date));
  }, [invoices, contacts, statusFilter, supplierSearch, dateFromFilter, dateToFilter]);

  // Calculate stats
  const stats = useMemo(() => {
    const paid = invoices
      .filter(inv => inv.status === 'paid')
      .reduce((sum, inv) => sum + (inv.total || 0), 0);

    const pending = invoices
      .filter(inv => inv.status === 'pending')
      .reduce((sum, inv) => sum + (inv.total || 0), 0);

    const overdue = invoices
      .filter(inv => inv.status === 'overdue')
      .reduce((sum, inv) => sum + (inv.total || 0), 0);

    return { paid, pending, overdue };
  }, [invoices]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
        <div className="w-full max-w-5xl space-y-3">
          <LoadingSkeleton variant="table-row" count={8} className="w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Invoices</h1>
        <p className="text-gray-500">Manage invoices and track payments</p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard
          label="Total Paid"
          value={stats.paid}
          color="green"
        />
        <StatCard
          label="Total Pending"
          value={stats.pending}
          color="amber"
        />
        <StatCard
          label="Total Overdue"
          value={stats.overdue}
          color="red"
        />
      </div>

      {/* Filter Bar */}
      <div className="flex gap-4 flex-wrap">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg bg-white"
        >
          <option value="All">All Status</option>
          <option value="Paid">Paid</option>
          <option value="Pending">Pending</option>
          <option value="Overdue">Overdue</option>
        </select>

        <div className="flex-1 min-w-64 flex items-center gap-2 bg-white border border-gray-300 rounded-lg px-3 py-2">
          <Search size={18} className="text-gray-400" />
          <input
            type="text"
            placeholder="Search by supplier..."
            value={supplierSearch}
            onChange={(e) => setSupplierSearch(e.target.value)}
            className="flex-1 outline-none"
          />
        </div>

        <input
          type="date"
          value={dateFromFilter}
          onChange={(e) => setDateFromFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg"
          title="From Date"
        />

        <input
          type="date"
          value={dateToFilter}
          onChange={(e) => setDateToFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg"
          title="To Date"
        />

        <button
          onClick={() => setCreatingInvoice(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus size={18} />
          Create Invoice
        </button>
      </div>

      {/* Invoices Table */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto md:overflow-x-visible">
          <table className="w-full min-w-max">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-700">Invoice #</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-700">Supplier</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-700">Issue Date</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-700">Due Date</th>
              <th className="px-6 py-3 text-right text-xs font-bold text-gray-700">Amount</th>
              <th className="px-6 py-3 text-right text-xs font-bold text-gray-700">Tax</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-700">Status</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-gray-700">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(invoice => {
              const supplier = contacts.find(c => c.id === invoice.supplier_id);
              const dueDate = new Date(invoice.due_date);
              const today = new Date();
              const isOverdue = invoice.status === 'pending' && dueDate < today;

              return (
                <tr key={invoice.id} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <span className="font-mono font-bold text-gray-900">
                      {invoice.invoice_number}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-gray-900">
                    {supplier?.company_name || '—'}
                  </td>
                  <td className="px-6 py-4 text-gray-900">
                    {new Date(invoice.issue_date).toLocaleDateString()}
                  </td>
                  <td className={`px-6 py-4 ${isOverdue ? 'text-red-600 font-bold' : 'text-gray-900'}`}>
                    {new Date(invoice.due_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right text-gray-900 font-mono">
                    ₹{(invoice.total || 0).toLocaleString('en-IN')}
                  </td>
                  <td className="px-6 py-4 text-right text-gray-900 font-mono">
                    ₹{(invoice.tax_amount || 0).toLocaleString('en-IN')}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      invoice.status === 'paid' ? 'bg-green-100 text-green-800' :
                      invoice.status === 'pending' ? 'bg-amber-100 text-amber-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {invoice.status?.charAt(0).toUpperCase() + invoice.status?.slice(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button
                        onClick={() => setViewingInvoice(invoice)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                        title="View"
                      >
                        <Eye size={16} />
                      </button>
                      {invoice.status !== 'paid' && (
                        <button
                          onClick={() => {
                            if (confirm('Mark this invoice as paid?')) {
                              markPaidMutation.mutate(invoice.id);
                            }
                          }}
                          className="p-2 text-green-600 hover:bg-green-50 rounded text-xs font-bold"
                          title="Mark Paid"
                        >
                          ✓
                        </button>
                      )}
                      <button
                        onClick={() => {
                          if (confirm('Delete this invoice?')) {
                            deleteInvoiceMutation.mutate(invoice.id);
                          }
                        }}
                        className="p-2 text-red-600 hover:bg-red-50 rounded"
                        title="Delete"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No invoices found
          </div>
        )}
      </div>

      {/* Modals */}
      {viewingInvoice && (
        <ViewInvoiceModal
          invoice={viewingInvoice}
          contacts={contacts}
          onClose={() => setViewingInvoice(null)}
        />
      )}

      {creatingInvoice && (
        <CreateInvoiceModal
          contacts={contacts}
          onClose={() => setCreatingInvoice(false)}
          onSuccess={() => setCreatingInvoice(false)}
        />
      )}
    </div>
  );
}
