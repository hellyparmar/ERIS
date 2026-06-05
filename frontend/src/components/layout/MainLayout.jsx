/**
 * Enterprise Retail Intelligence System v3.0
 * LAYOUT - MAIN LAYOUT
 * 
 * Primary layout structure with Sidebar and Header
 * V3.0 Standard: Presentation vs Container pattern
 */

import { useState } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';

const MainLayout = ({ children, currentView = 'dashboard' }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-[var(--bg-primary)]">
      <Sidebar
        currentView={currentView}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <div className="flex-1 flex flex-col overflow-hidden md:ml-16 lg:ml-60">
        <Header
          onMenuClick={() => setSidebarOpen((v) => !v)}
          sidebarOpen={sidebarOpen}
          onKeyDown={(e) => {
            if (e.key === 'Escape' && sidebarOpen) setSidebarOpen(false);
          }}
        />
        <main style={{
          flex: 1,
          overflow: 'auto',
          background: 'var(--bg-primary)',
          padding: '28px 32px',
        }}>
          <div className="page-inner max-w-screen-xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default MainLayout;

