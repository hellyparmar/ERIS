import { useState } from 'react';
import { Bell, LogOut, Menu } from 'lucide-react';
import './header.css';

export default function Header({ pageTitle = 'Dashboard', onMenuClick = () => {} }) {
  const [showUserMenu, setShowUserMenu] = useState(false);

  const user = (() => {
    try {
      return JSON.parse(localStorage.getItem('user') || '{}');
    } catch {
      return { name: 'User', role: 'Admin', outlet: 'Main' };
    }
  })();

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  };

  return (
    <header className="header">
      <div className="header-content">
        {/* Mobile Hamburger Icon (visible only on <768px) */}
        <button onClick={onMenuClick} className="md:hidden p-2 hover:bg-gray-100 rounded-lg" title="Toggle sidebar">
          <Menu size={24} />
        </button>

        {/* Page Title - Visible on tablet+, hidden on mobile */}
        <h1 className="header-title hidden md:block">{pageTitle}</h1>

        <div className="header-actions">
          <button className="notification-btn" title="View notifications">
            <Bell size={20} />
          </button>

          <div className="user-menu-wrapper">
            <button
              className="user-button hidden sm:flex"
              onClick={() => setShowUserMenu(!showUserMenu)}
            >
              <div className="user-avatar">{user.name?.[0]?.toUpperCase() || 'U'}</div>
              <div className="user-info">
                <div className="user-name">{user.name || 'User'}</div>
                <div className="user-role">{user.role || 'Admin'}</div>
              </div>
            </button>

            {/* Mobile-only Avatar Button - visible on <768px */}
            <button
              className="sm:hidden w-10 h-10 rounded-full bg-gradient-to-br from-yellow-400 to-yellow-600 flex items-center justify-center text-white font-bold text-sm"
              onClick={() => setShowUserMenu(!showUserMenu)}
            >
              {user.name?.[0]?.toUpperCase() || 'U'}
            </button>

            {showUserMenu && (
              <div className="user-dropdown">
                <div className="dropdown-item">
                  <span className="dropdown-label">Outlet</span>
                  <span className="dropdown-value">{user.outlet || 'Main'}</span>
                </div>
                <div className="dropdown-item">
                  <span className="dropdown-label">Role</span>
                  <span className="dropdown-value">{user.role || 'Admin'}</span>
                </div>
                <div className="dropdown-divider"></div>
                <button className="dropdown-logout" onClick={handleLogout}>
                  <LogOut size={16} />
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
