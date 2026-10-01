import { useQuery } from '@tanstack/react-query';
import { useLocation, useNavigate } from 'react-router-dom';
import { Bell } from 'lucide-react';
import api from '../../lib/api';

const pageTitleMap = {
  '/': 'Dashboard', '/dashboard': 'Dashboard',
  '/sales': 'Sales', '/inventory': 'Inventory',
  '/invoices': 'Invoices', '/analytics': 'Analytics',
  '/forecasts': 'Forecasts', '/ai-assistant': 'AI Assistant',
  '/alerts': 'Alerts',
  '/suppliers': 'Suppliers',
  '/customers': 'Customers',
  '/gst-invoice': 'GST Invoice',
  '/settings': 'Settings',
  '/outlets': 'Outlets',
};

export default function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  const { data: activeAlerts = 0 } = useQuery({
    queryKey: ['headerActiveAlerts'],
    queryFn: async () => {
      const response = await api.get('/api/v1/alerts/list', { params: { unread_only: true, per_page: 1 } });
      return response.data.pagination?.total || 0;
    },
    refetchInterval: 60_000,
  });

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

      <div style={{ position: 'relative' }}>
        <button
          title="Notifications"
          onClick={() => navigate('/alerts')}
          style={{
            width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center',
            border: 'none', background: 'transparent', borderRadius: 'var(--r-md)',
            color: 'var(--color-ink-muted)', cursor: 'pointer', position: 'relative',
          }}
        >
          <Bell size={16} />
          {activeAlerts > 0 && <span style={{
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
