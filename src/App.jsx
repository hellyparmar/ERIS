import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Sidebar from './components/layout/Sidebar';
import Header from './components/layout/Header';
import MobileNav from './components/layout/MobileNav';
import FloatingAIAssistant from './components/layout/FloatingAIAssistant';
import { ToastProvider } from './components/ui/Toast';
import ErrorBoundary from './components/ErrorBoundary';
import SkipLinks from './components/a11y/SkipLinks';
import { Announcer } from './components/a11y/A11yUtils';
import './modern-design.css';
import './index.css';

// Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Inventory = lazy(() => import('./pages/Inventory'));
const Customers = lazy(() => import('./pages/Customers'));  // Phase 3
const Forecasts = lazy(() => import('./pages/Forecasts'));
const Alerts = lazy(() => import('./pages/Alerts'));
const Integrations = lazy(() => import('./pages/Integrations'));
const Team = lazy(() => import('./pages/Team'));
const Enterprise = lazy(() => import('./pages/Enterprise'));
const AIAssistant = lazy(() => import('./pages/AIAssistant'));
const TaxCompliance = lazy(() => import('./pages/TaxCompliance'));
const Invoices = lazy(() => import('./pages/Invoices'));
const Loyalty = lazy(() => import('./pages/Loyalty'));
// New Enterprise Intelligence Modules
const CustomerInsights = lazy(() => import('./pages/CustomerInsights'));
const MultiStore = lazy(() => import('./pages/MultiStore'));
const Compliance = lazy(() => import('./pages/Compliance'));
// Production-Grade Feature Pages
const Settings = lazy(() => import('./pages/Settings'));
const DevOps = lazy(() => import('./pages/DevOps'));
const POS = lazy(() => import('./pages/POS'));
const Employees = lazy(() => import('./pages/Employees'));
const Returns = lazy(() => import('./pages/Returns'));
const Suppliers = lazy(() => import('./pages/Suppliers'));
const Promotions = lazy(() => import('./pages/Promotions'));
const Monitoring = lazy(() => import('./pages/Monitoring'));

// Loading Fallback
const LoadingSpinner = () => (
  <div className="flex h-full items-center justify-center min-h-[50vh]">
    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
  </div>
);

const MainLayout = () => {
  const location = useLocation();
  const mainRef = React.useRef(null);

  React.useEffect(() => {
    // Disable browser's scroll restoration
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }

    // Scroll to top using multiple methods to ensure it works
    const scrollToTop = () => {
      if (mainRef.current) {
        mainRef.current.scrollTop = 0;
      }
      const mainContent = document.getElementById('main-content');
      if (mainContent) {
        mainContent.scrollTop = 0;
      }
    };

    // Execute immediately and after a delay to override any restoration
    scrollToTop();
    setTimeout(scrollToTop, 10);
    setTimeout(scrollToTop, 50);
    setTimeout(scrollToTop, 100);
  }, [location.pathname]);

  return (
    <>
      <SkipLinks />
      <Announcer />
      <div className="flex h-screen bg-background text-foreground overflow-hidden transition-colors duration-300" style={{ height: '100vh' }}>
        <div id="navigation" className="hidden md:block">
          <Sidebar />
        </div>
        <div className="flex-1 flex flex-col overflow-hidden h-full">
          <Header />
          <main
            id="main-content"
            ref={mainRef}
            className="flex-1 overflow-y-auto overflow-x-hidden p-4 md:p-6 mb-16 md:mb-0 w-full min-h-0"
            role="main"
            aria-label="Main content"
          >
            <Suspense fallback={<LoadingSpinner />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/analytics" element={<ErrorBoundary><Analytics /></ErrorBoundary>} />
                <Route path="/invoices" element={<Invoices />} />
                <Route path="/loyalty" element={<Loyalty />} />
                <Route path="/inventory" element={<Inventory />} />
                <Route path="/customers" element={<Customers />} />  {/* Phase 3 */}
                <Route path="/forecasts" element={<Forecasts />} />
                <Route path="/alerts" element={<Alerts />} />
                <Route path="/integrations" element={<Integrations />} />
                <Route path="/tax-compliance" element={<TaxCompliance />} />
                <Route path="/team" element={<Team />} />
                <Route path="/enterprise" element={<Enterprise />} />
                <Route path="/ai-assistant" element={<AIAssistant />} />
                <Route path="/customers" element={<CustomerInsights />} />
                <Route path="/multi-store" element={<MultiStore />} />
                <Route path="/compliance" element={<Compliance />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/devops" element={<DevOps />} />
                <Route path="/pos" element={<POS />} />
                <Route path="/employees" element={<Employees />} />
                <Route path="/returns" element={<Returns />} />
                <Route path="/suppliers" element={<Suppliers />} />
                <Route path="/promotions" element={<Promotions />} />
                <Route path="/monitoring" element={<Monitoring />} />
              </Routes>
            </Suspense>
          </main>
        </div>
        <MobileNav />
        <FloatingAIAssistant />
      </div>
    </>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <Router>
          <MainLayout />
        </Router>
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
