import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import BottomNav from './BottomNav';

const hideHeaderPaths = ['/login', '/signup'];

const MainLayout = ({ children }) => {
  const location = useLocation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const showHeader = !hideHeaderPaths.includes(location.pathname);

  const toggleSidebar = () => setSidebarCollapsed(v => !v);

  return (
    <div className="app-shell" style={{
      display: 'flex', minHeight: '100vh',
      background: 'var(--color-canvas)',
    }}>
      <div id="sidebar-desktop" style={{
        display: 'block',
      }}>
        <style>{`
          @media (max-width: 767px) {
            #sidebar-desktop { display: none !important; }
          }
        `}</style>
        <Sidebar collapsed={sidebarCollapsed} onToggle={toggleSidebar} />
      </div>

      <div style={{
        flex: 1, display: 'flex', flexDirection: 'column',
        minWidth: 0, paddingBottom: 60,
      }}
      className="main-content-area"
      >
        <style>{`
          @media (min-width: 768px) {
            .main-content-area { padding-bottom: 0 !important; }
          }
        `}</style>

        {showHeader && <Header />}

        <main style={{
          flex: 1, padding: 'var(--sp-6)',
          maxWidth: 'var(--content-max)',
        }}
        className="main-content-pad"
        >
          <style>{`
            @media (max-width: 767px) {
              .main-content-pad { padding: var(--sp-4) var(--sp-3) !important; }
            }
          `}</style>
          {children}
        </main>

        <footer style={{
          borderTop: '1px solid var(--color-line)',
          padding: 'var(--sp-5) var(--sp-6) var(--sp-4)',
          marginTop: 'auto',
          fontSize: 11, color: 'var(--color-ink-faint)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span>&copy; {new Date().getFullYear()} ERIS</span>
          <span>Open-source portfolio build</span>
        </footer>
      </div>

      <BottomNav />
    </div>
  );
};

export default MainLayout;
