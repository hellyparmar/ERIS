import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, ShoppingCart, TrendingUp, Package, Bell, MoreHorizontal, BarChart3, Bot, FileText, Building2, Settings } from 'lucide-react';

const mainItems = [
  { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { label: 'POS',       path: '/pos',        icon: ShoppingCart },
  { label: 'Sales',     path: '/sales',      icon: TrendingUp },
  { label: 'Inventory', path: '/inventory',  icon: Package },
  { label: 'Alerts',    path: '/alerts',     icon: Bell },
];

const drawerItems = [
  { label: 'Analytics',    path: '/analytics',      icon: BarChart3 },
  { label: 'AI Assistant', path: '/ai-assistant',   icon: Bot },
  { label: 'Invoices',     path: '/invoices',       icon: FileText },
  { label: 'Multi-Store',  path: '/multi-store',    icon: Building2 },
  { label: 'Settings',     path: '/settings',       icon: Settings },
];

export default function BottomNav() {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <>
      <nav style={{
        display: 'none',
        position: 'fixed', bottom: 0, left: 0, right: 0,
        height: 60, background: 'var(--color-navy-deep)',
        borderTop: '1px solid rgba(255,255,255,0.06)',
        zIndex: 1000,
        padding: '4px env(safe-area-inset-bottom)',
      }}
      className="bottom-nav-visible"
      >
        <style>{`
          @media (max-width: 767px) {
            .bottom-nav-visible { display: flex !important; }
          }
          .bnav-link {
            flex: 1; display: flex; flex-direction: column; align-items: center;
            justify-content: center; gap: 2px; text-decoration: none;
            color: var(--color-navy-text); font-size: 9px; font-weight: 500;
            padding: 4px 0; border-radius: var(--r-md); transition: all 0.12s ease;
          }
          .bnav-link:active { background: var(--color-navy-hover); }
          .bnav-link.active { color: var(--color-amber); }
          .bnav-drawer-overlay {
            position: fixed; inset: 0; background: rgba(0,0,0,0.4);
            z-index: 998; display: none;
          }
          .bnav-drawer-overlay.open { display: block; }
          .bnav-drawer {
            position: fixed; bottom: 0; left: 0; right: 0;
            background: var(--color-navy-deep); border-radius: 16px 16px 0 0;
            z-index: 999; padding: 20px 24px calc(20px + env(safe-area-inset-bottom));
            transform: translateY(100%); transition: transform 0.25s ease;
          }
          .bnav-drawer.open { transform: translateY(0); }
          .bnav-drawer-handle {
            width: 32px; height: 4px; border-radius: 2px;
            background: rgba(255,255,255,0.15); margin: 0 auto 16px;
          }
          @media (min-width: 768px) {
            .bottom-nav-visible { display: none !important; }
            .bnav-drawer-overlay { display: none !important; }
            .bnav-drawer { display: none !important; }
          }
        `}</style>

        {mainItems.map(item => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className="bnav-link"
              onClick={() => setDrawerOpen(false)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}

        <button
          onClick={() => setDrawerOpen(true)}
          className="bnav-link"
          style={{ border: 'none', background: 'transparent', cursor: 'pointer' }}
        >
          <MoreHorizontal size={18} />
          <span>More</span>
        </button>
      </nav>

      {/* Drawer overlay */}
      <div
        className={`bnav-drawer-overlay ${drawerOpen ? 'open' : ''}`}
        onClick={() => setDrawerOpen(false)}
      />

      {/* Drawer panel */}
      <div className={`bnav-drawer ${drawerOpen ? 'open' : ''}`}>
        <div className="bnav-drawer-handle" />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
          {drawerItems.map(item => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className="bnav-link"
                onClick={() => setDrawerOpen(false)}
                style={{ padding: '12px 8px', borderRadius: 'var(--r-md)', gap: 4 }}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </div>
      </div>
    </>
  );
}
