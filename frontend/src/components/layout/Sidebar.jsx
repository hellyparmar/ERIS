import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { LogOut, ChevronDown, Menu, X } from 'lucide-react';
import './sidebar.css';

export default function Sidebar({ open = false, onClose = () => {} }) {
  const navigate = useNavigate();
  const [openSections, setOpenSections] = useState({
    general: true,
    management: true,
    intelligence: true,
  });

  const toggleSection = (section) => {
    setOpenSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const navItems = {
    general: [
      { label: 'Dashboard', path: '/' },
      { label: 'Sales', path: '/sales' },
    ],
    management: [
      { label: 'Inventory', path: '/inventory' },
      { label: 'Outlets', path: '/outlets' },
      { label: 'Employees', path: '/employees' },
      { label: 'Contacts', path: '/contacts' },
      { label: 'Invoices', path: '/invoices' },
    ],
    intelligence: [
      { label: 'Forecasting', path: '/forecasting' },
      { label: 'Alerts', path: '/alerts' },
      { label: 'Reports', path: '/reports' },
      { label: 'AI Assistant', path: '/ai-assistant' },
    ],
  };

  return (
    <>
      {/* Mobile overlay backdrop */}
      {open && (
        <div
          className="fixed inset-0 bg-black/30 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Desktop/Tablet Sidebar + Mobile overlay sidebar when open */}
      {/* Desktop: Full width (240px), Tablet: Collapsed (60px), Mobile: overlay when open */}
      <div className={`sidebar ${open ? 'flex' : 'hidden'} md:flex w-60 md:w-16 lg:w-60 flex-col fixed left-0 top-0 h-screen z-50 md:z-100`}>
        {/* Header - Hidden on tablet/mobile */}
        <div className="sidebar-header md:hidden">
          <div className="sidebar-logo">
            <div className="logo-circle">E</div>
            <div>
              <div className="logo-title">ERIS</div>
              <div className="logo-subtitle">Retail System</div>
            </div>
          </div>
        </div>

        {/* Icon-only header for tablet (md: 768px - 1023px) */}
        <div className="hidden md:flex lg:hidden items-center justify-center h-16 border-b border-opacity-10 border-white">
          <div className="logo-circle w-10 h-10">E</div>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav flex-1 overflow-y-auto">
          {/* General Section */}
          <div className="nav-section">
            <button
              className="nav-section-header md:hidden"
              onClick={() => toggleSection('general')}
            >
              <span>General</span>
              <ChevronDown
                size={16}
                className={`chevron ${openSections.general ? 'open' : ''}`}
              />
            </button>
            {openSections.general && (
              <div className="nav-items">
                {navItems.general.map(item => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `nav-item ${isActive ? 'active' : ''} md:justify-center`
                    }
                    title={item.label}
                  >
                    <span className="md:hidden">{item.label}</span>
                    <span className="hidden md:inline text-sm" title={item.label}>
                      {item.label.charAt(0).toUpperCase()}
                    </span>
                  </NavLink>
                ))}
              </div>
            )}
          </div>

          {/* Management Section */}
          <div className="nav-section">
            <button
              className="nav-section-header md:hidden"
              onClick={() => toggleSection('management')}
            >
              <span>Management</span>
              <ChevronDown
                size={16}
                className={`chevron ${openSections.management ? 'open' : ''}`}
              />
            </button>
            {openSections.management && (
              <div className="nav-items">
                {navItems.management.map(item => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `nav-item ${isActive ? 'active' : ''} md:justify-center`
                    }
                    title={item.label}
                  >
                    <span className="md:hidden">{item.label}</span>
                    <span className="hidden md:inline text-sm" title={item.label}>
                      {item.label.charAt(0).toUpperCase()}
                    </span>
                  </NavLink>
                ))}
              </div>
            )}
          </div>

          {/* Intelligence Section */}
          <div className="nav-section">
            <button
              className="nav-section-header md:hidden"
              onClick={() => toggleSection('intelligence')}
            >
              <span>Intelligence</span>
              <ChevronDown
                size={16}
                className={`chevron ${openSections.intelligence ? 'open' : ''}`}
              />
            </button>
            {openSections.intelligence && (
              <div className="nav-items">
                {navItems.intelligence.map(item => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      `nav-item ${isActive ? 'active' : ''} md:justify-center`
                    }
                    title={item.label}
                  >
                    <span className="md:hidden">{item.label}</span>
                    <span className="hidden md:inline text-sm" title={item.label}>
                      {item.label.charAt(0).toUpperCase()}
                    </span>
                  </NavLink>
                ))}
              </div>
            )}
          </div>
        </nav>

        {/* Footer */}
        <div className="sidebar-footer md:flex-col">
          <NavLink
            to="/settings"
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''} md:justify-center`}
            title="Settings"
          >
            <span className="md:hidden">Settings</span>
            <span className="hidden md:inline text-sm">⚙️</span>
          </NavLink>
          <button
            className="nav-item logout md:justify-center"
            onClick={handleLogout}
            title="Logout"
          >
            <LogOut size={16} />
            <span className="md:hidden">Logout</span>
          </button>
        </div>
      </div>

      {/* Mobile Bottom Navigation (< 768px) */}
      <div className="fixed bottom-0 left-0 right-0 md:hidden z-50 border-t border-opacity-10 border-white bg-sidebar overflow-x-auto">
        <div className="flex min-w-max">
          {[...navItems.general, ...navItems.management, ...navItems.intelligence].map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex-shrink-0 w-16 flex flex-col items-center justify-center py-3 text-xs ${isActive ? 'text-yellow-500 border-t-2 border-yellow-500' : 'text-sidebar-text-inactive'}`
              }
            >
              <span>{item.label.charAt(0).toUpperCase()}</span>
            </NavLink>
          ))}
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `flex-shrink-0 w-16 flex flex-col items-center justify-center py-3 text-xs ${isActive ? 'text-yellow-500 border-t-2 border-yellow-500' : 'text-sidebar-text-inactive'}`
            }
          >
            <span>⚙️</span>
          </NavLink>
        </div>
      </div>
    </>
  );
}
