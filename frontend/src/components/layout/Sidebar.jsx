import { useState, useMemo } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { LogOut, LayoutDashboard, ShoppingCart, Package, FileText, BarChart3, Bell, Bot, Calculator, Building2, Settings, Truck, Receipt, Tag, TrendingUp, Users, ChevronLeft, MessageSquare, Activity } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

const routeRoleMap = {
  '/dashboard': ['super_admin', 'superadmin', 'area_manager', 'outlet_manager', 'manager'],
  '/pos': ['super_admin', 'superadmin', 'area_manager', 'outlet_manager', 'manager'],
  '/sales': ['super_admin', 'superadmin', 'area_manager', 'outlet_manager', 'manager'],
  '/inventory': ['super_admin', 'superadmin', 'area_manager', 'outlet_manager', 'manager'],
  '/invoices': ['super_admin', 'superadmin', 'area_manager', 'outlet_manager', 'manager'],
  '/alerts': ['super_admin', 'superadmin', 'area_manager', 'outlet_manager', 'manager'],
  '/ai-assistant': ['super_admin', 'superadmin', 'area_manager', 'outlet_manager', 'manager'],
  '/customers': ['super_admin', 'superadmin', 'area_manager', 'outlet_manager', 'manager'],
  '/forecasts': ['super_admin', 'superadmin', 'area_manager', 'outlet_manager', 'manager'],
  '/settings': ['super_admin', 'superadmin', 'area_manager', 'outlet_manager', 'manager'],
  '/day-close': ['super_admin', 'superadmin', 'area_manager', 'outlet_manager', 'manager'],
  '/analytics': ['super_admin', 'superadmin', 'area_manager'],
  '/multi-store': ['super_admin', 'superadmin', 'area_manager'],
  '/outlets': ['super_admin', 'superadmin', 'area_manager'],
  '/reports': ['super_admin', 'superadmin', 'area_manager'],
  '/customer-insights': ['super_admin', 'superadmin', 'area_manager'],
  '/team': ['super_admin', 'superadmin'],
  '/integrations': ['super_admin', 'superadmin'],
  '/tax-compliance': ['super_admin', 'superadmin'],
  '/gst-invoice': ['super_admin', 'superadmin'],
  '/gst-rates': ['super_admin', 'superadmin'],
  '/suppliers': ['super_admin', 'superadmin'],
  '/contacts': ['super_admin', 'superadmin'],
  '/employees': ['super_admin', 'superadmin'],
  '/causal-analysis': ['super_admin', 'superadmin', 'area_manager'],
  '/communication': ['super_admin', 'superadmin', 'area_manager', 'outlet_manager', 'manager'],
};

export default function Sidebar({ open = false, onClose = () => {}, collapsed = false, onToggle }) {
  const navigate = useNavigate();
  const { user: authUser, logout } = useAuth();

  const user = useMemo(() => {
    try {
      const stored = JSON.parse(localStorage.getItem('rdios-user') || '{}');
      return { ...stored, ...authUser };
    } catch {
      return authUser || { name: 'User', role: 'Admin' };
    }
  }, [authUser]);

  const userRole = user?.role || '';

  const sections = [
    {
      id: 'operations',
      title: 'Operations',
      items: [
        { label: 'Dashboard',  path: '/dashboard',  icon: LayoutDashboard },
        { label: 'POS',        path: '/pos',         icon: ShoppingCart },
        { label: 'Sales',      path: '/sales',       icon: TrendingUp },
        { label: 'Inventory',  path: '/inventory',   icon: Package },
        { label: 'Invoices',   path: '/invoices',    icon: FileText },
      ]
    },
    {
      id: 'intelligence',
      title: 'Intelligence',
      items: [
        { label: 'Analytics',          path: '/analytics',         icon: BarChart3 },
        { label: 'Causal Analysis',    path: '/causal-analysis',   icon: Activity },
        { label: 'Forecasts',          path: '/forecasts',         icon: TrendingUp },
        { label: 'AI Assistant',       path: '/ai-assistant',      icon: Bot },
        { label: 'Communication Hub',  path: '/communication',     icon: MessageSquare },
        { label: 'Alerts',             path: '/alerts',            icon: Bell },
      ]
    },
    {
      id: 'management',
      title: 'Management',
      items: [
        { label: 'Employees',   path: '/employees',   icon: Users },
        { label: 'Suppliers',   path: '/suppliers',   icon: Truck },
        { label: 'Customers',   path: '/customers',   icon: Users },
        { label: 'Multi-Store', path: '/multi-store', icon: Building2 },
        { label: 'Team',        path: '/team',        icon: Users },
        { label: 'Contacts',    path: '/contacts',    icon: Users },
        { label: 'Outlets',     path: '/outlets',     icon: Building2 },
      ]
    },
    {
      id: 'compliance',
      title: 'Compliance',
      items: [
        { label: 'Tax Compliance', path: '/tax-compliance', icon: Calculator },
        { label: 'GST Invoice',    path: '/gst-invoice',    icon: Receipt },
        { label: 'GST Rates',      path: '/gst-rates',      icon: Tag },
        { label: 'Integrations',   path: '/integrations',   icon: Settings },
      ]
    }
  ];

  const filteredSections = sections
    .map(section => ({
      ...section,
      items: section.items.filter(item => {
        const allowedRoles = routeRoleMap[item.path];
        return !allowedRoles || allowedRoles.includes(userRole);
      })
    }))
    .filter(section => section.items.length > 0);

  return (
    <aside style={{
      width: collapsed ? 'var(--sidebar-collapsed)' : 'var(--sidebar-width)',
      height: '100vh', display: 'flex', flexDirection: 'column',
      background: 'var(--color-navy-deep)', borderRight: 'none',
      transition: 'width 0.2s ease',
      overflow: 'hidden',
    }}>
      <div style={{
        padding: collapsed ? 'var(--sp-4)' : 'var(--sp-5) var(--sp-4)',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        display: 'flex', alignItems: 'center', gap: collapsed ? 0 : 12,
        justifyContent: collapsed ? 'center' : 'flex-start',
      }}>
        <div style={{
          width: 32, height: 32, borderRadius: 'var(--r-md)',
          background: 'var(--color-amber-dim)', color: 'var(--color-amber)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: 'var(--font-serif)', fontWeight: 700, fontSize: 16, flexShrink: 0,
        }}>E</div>
        {!collapsed && (
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#f4f2ed', lineHeight: 1.2 }}>ERIS</div>
            <div style={{ fontSize: 9, color: 'var(--color-navy-text)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Retail Intelligence
            </div>
          </div>
        )}
      </div>

      <nav style={{ flex: 1, overflowY: 'auto', padding: collapsed ? 'var(--sp-3)' : 'var(--sp-4)' }}>
        <style>{`
          .sidebar-link-atelier {
            display: flex; align-items: center; gap: var(--sp-3);
            padding: ${collapsed ? '8px 0' : '8px 12px'};
            border-radius: var(--r-md);
            font-size: 13px; font-weight: 500;
            color: var(--color-navy-text); text-decoration: none;
            transition: all 0.12s ease;
            justify-content: ${collapsed ? 'center' : 'flex-start'};
            position: relative;
          }
          .sidebar-link-atelier:hover {
            background: var(--color-navy-hover);
            color: var(--color-navy-active);
          }
          .sidebar-link-atelier.active {
            background: var(--color-amber-dim);
            color: var(--color-amber);
            font-weight: 600;
          }
          .sidebar-link-atelier.active::before {
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 2px;
            height: 18px;
            background: var(--color-amber);
            border-radius: 0 2px 2px 0;
          }
          .sidebar-link-atelier:focus-visible {
            outline: 2px solid var(--color-amber);
            outline-offset: -2px;
          }
        `}</style>
        {filteredSections.map(section => (
          <div key={section.id} style={{ marginBottom: collapsed ? 'var(--sp-4)' : 'var(--sp-6)' }}>
            {!collapsed && (
              <div style={{
                fontSize: 9, fontWeight: 700, textTransform: 'uppercase',
                letterSpacing: '0.1em', color: 'var(--color-navy-muted)',
                padding: '0 var(--sp-3)', marginBottom: 'var(--sp-2)',
              }}>
                {section.title}
              </div>
            )}
            {section.items.map(item => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className="sidebar-link-atelier"
                  onClick={onClose}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon size={16} style={{ flexShrink: 0 }} />
                  {!collapsed && <span>{item.label}</span>}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      <button
        onClick={onToggle}
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: 'var(--sp-2)', margin: '0 var(--sp-2)',
          border: 'none', background: 'transparent',
          color: 'var(--color-navy-text)', cursor: 'pointer',
          borderRadius: 'var(--r-md)',
          transition: 'transform 0.2s ease',
          transform: collapsed ? 'rotate(180deg)' : 'rotate(0deg)',
        }}
      >
        <ChevronLeft size={14} />
      </button>

      <div style={{
        padding: collapsed ? 'var(--sp-3)' : 'var(--sp-4)',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        display: 'flex', alignItems: 'center', gap: collapsed ? 0 : 'var(--sp-3)',
        justifyContent: collapsed ? 'center' : 'flex-start',
      }}>
        <div style={{
          width: 30, height: 30, borderRadius: '50%',
          background: 'var(--color-amber-dim)', color: 'var(--color-amber)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 12, fontWeight: 700, flexShrink: 0,
        }}>
          {user.name?.[0]?.toUpperCase() || 'U'}
        </div>
        {!collapsed && (
          <>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: '#d4d0c8', lineHeight: 1.2 }}>{user.name || 'User'}</div>
              <div style={{ fontSize: 10, color: 'var(--color-navy-text)', marginTop: 1, textTransform: 'capitalize' }}>
                {user.role?.replace('_', ' ') || 'Admin'}
              </div>
            </div>
            <button
              onClick={logout}
              title="Logout"
              style={{
                width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center',
                border: 'none', background: 'transparent', borderRadius: 'var(--r-md)',
                color: 'var(--color-navy-text)', cursor: 'pointer', flexShrink: 0,
              }}
            >
              <LogOut size={13} />
            </button>
          </>
        )}
      </div>
    </aside>
  );
}
