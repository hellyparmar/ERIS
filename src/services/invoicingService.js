/**
 * Invoicing Service
 * Handles all invoice-related API calls
 */

export const invoicingService = {
  // Create Invoice
  async createInvoice(invoiceData) {
    try {
      const response = await fetch('/api/v1/invoicing/invoices', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(invoiceData)
      });
      return await response.json();
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Get Invoice Details
  async getInvoice(invoiceId) {
    try {
      const response = await fetch(`/api/v1/invoicing/invoices/${invoiceId}`);
      return await response.json();
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // List Invoices with Filters
  async listInvoices(filters = {}) {
    try {
      const params = new URLSearchParams({
        page: filters.page || 1,
        per_page: filters.perPage || 50,
        ...(filters.status && { status: filters.status }),
        ...(filters.paymentStatus && { payment_status: filters.paymentStatus }),
        ...(filters.customerId && { customer_id: filters.customerId })
      });

      const response = await fetch(`/api/v1/invoicing/invoices?${params}`);
      return await response.json();
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Record Payment
  async recordPayment(invoiceId, paymentData) {
    try {
      const response = await fetch(`/api/v1/invoicing/invoices/${invoiceId}/pay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(paymentData)
      });
      return await response.json();
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Download Invoice PDF
  downloadInvoicePDF(invoiceId) {
    window.open(`/api/v1/invoicing/invoices/${invoiceId}/pdf`, '_blank');
  },

  // Email Invoice
  async emailInvoice(invoiceId, recipientEmail) {
    try {
      const response = await fetch(
        `/api/v1/invoicing/invoices/${invoiceId}/email`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ recipient_email: recipientEmail })
        }
      );
      return await response.json();
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Analytics: GST Summary
  async getGSTSummary(startDate, endDate) {
    try {
      const params = new URLSearchParams({
        ...(startDate && { start_date: startDate }),
        ...(endDate && { end_date: endDate })
      });

      const response = await fetch(`/api/v1/invoicing/analytics/gst-summary?${params}`);
      return await response.json();
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Analytics: Payment Summary
  async getPaymentSummary(days = 90) {
    try {
      const response = await fetch(
        `/api/v1/invoicing/analytics/payment-summary?days=${days}`
      );
      return await response.json();
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Analytics: Revenue by Customer
  async getRevenueByCustomer(limit = 10) {
    try {
      const response = await fetch(
        `/api/v1/invoicing/analytics/revenue-by-customer?limit=${limit}`
      );
      return await response.json();
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Analytics: Overdue Invoices
  async getOverdueInvoices() {
    try {
      const response = await fetch('/api/v1/invoicing/analytics/overdue-invoices');
      return await response.json();
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Generate Invoice Report
  async generateInvoiceReport(startDate, endDate) {
    try {
      const response = await fetch('/api/v1/invoicing/reports/invoice-summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ start_date: startDate, end_date: endDate })
      });
      return await response.json();
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  // Calculate Invoice Total
  calculateInvoiceTotal(lineItems, gstRate = 18, tdsRate = 0) {
    let subtotal = 0;
    lineItems.forEach(item => {
      subtotal += item.quantity * item.unit_price;
    });

    const gstAmount = subtotal * (gstRate / 100);
    const tdsAmount = (subtotal + gstAmount) * (tdsRate / 100);
    const total = subtotal + gstAmount - tdsAmount;

    return {
      subtotal: Math.round(subtotal * 100) / 100,
      gstAmount: Math.round(gstAmount * 100) / 100,
      tdsAmount: Math.round(tdsAmount * 100) / 100,
      total: Math.round(total * 100) / 100
    };
  },

  // Format currency
  formatCurrency(amount) {
    return `₹${amount.toLocaleString('en-IN', { maximumFractionDigits: 2 })}`;
  },

  // Format date
  formatDate(date) {
    return new Date(date).toLocaleDateString('en-IN');
  }
};

export default invoicingService;
