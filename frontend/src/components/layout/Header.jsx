import { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Bell, Search } from 'lucide-react';

const pageTitleMap = {
  '/': 'Dashboard', '/dashboard': 'Dashboard', '/pos': 'POS Terminal',
  '/sales': 'Sales', '/inventory': 'Inventory',
  '/invoices': 'Invoices', '/analytics': 'Analytics',
  '/forecasts': 'Forecasts', '/ai-assistant': 'AI Assistant',
  '/customer-insights': 'Customer Insights', '/alerts': 'Alerts',
  '/employees': 'Employees', '/suppliers': 'Suppliers',
  '/customers': 'Customers', '/multi-store': 'Multi-Store',
  '/team': 'Team', '/contacts': 'Contacts',
  '/tax-compliance': 'Tax Compliance', '/gst-invoice': 'GST Invoice',
  '/gst-rates': 'GST Rates', '/integrations': 'Integrations',
  '/settings': 'Settings', '/day-close': 'Day Close',
  '/outlets': 'Outlets',
};

export default function Header({ onMenuClick }) {
  const location = useLocation();
  const [hasNotifications] = useState(true);

  const pageName = pageTitleMap[location.pathname] || 'Dashboard';

  return (
    <header style={{
      height: 48,
      display: 'flex',
      alignItems: 'center',
      padding: '0 var(--sp-6)',
      background: 'var(--color-paper)',
      borderBottom: '1px solid var(--color-amber-line)',
      gap: 'var(--sp-6)',
    }}>
      <div style={{
        fontFamily: 'var(--font-serif)',
        fontSize: 18,
        fontWeight: 700,
        color: 'var(--color-ink)',
        lineHeight: 1,
      }}>
        {pageName}
      </div>

      <div style={{ flex: 1 }} />

      <div style={{ position: 'relative', maxWidth: 320, width: '100%' }}>
        <Search size={14} style={{
          position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)',
          color: 'var(--color-ink-faint)', pointerEvents: 'none',
        }} />
        <input
          type="text"
          placeholder="Search products, invoices..."
          style={{
            width: '100%', height: 34, padding: '0 12px 0 34px',
            border: '1px solid var(--color-line)', borderRadius: 'var(--r-md)',
            background: 'var(--color-paper)', color: 'var(--color-ink)',
            fontSize: 13, outline: 'none', fontFamily: 'var(--font-serif)',
            fontStyle: 'italic',
          }}
          onFocus={e => { e.target.style.borderColor = 'var(--color-amber)'; }}
          onBlur={e => { e.target.style.borderColor = 'var(--color-line)'; }}
        />
      </div>

      <div style={{ position: 'relative' }}>
        <button
          title="Notifications"
          style={{
            width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center',
            border: 'none', background: 'transparent', borderRadius: 'var(--r-md)',
            color: 'var(--color-ink-muted)', cursor: 'pointer', position: 'relative',
          }}
        >
          <Bell size={16} />
          {hasNotifications && <span style={{
            position: 'absolute', top: 6, right: 6,
            width: 8, height: 8, borderRadius: '50%',
            background: 'var(--color-amber)',
            boxShadow: '0 0 6px var(--color-amber-glow)',
          }} />}
        </button>
      </div>
    </header>
  );
}
