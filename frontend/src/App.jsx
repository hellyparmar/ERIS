import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient.js';
import { ToastProvider } from './contexts/ToastContext';
import ErrorBoundary from './components/ErrorBoundary';
import MainLayout from './components/layout/MainLayout';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Login from './pages/Login';

// Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard.jsx'));
const Analytics = lazy(() => import('./pages/Analytics.jsx'));
const Inventory = lazy(() => import('./pages/Inventory.jsx'));
const Customers = lazy(() => import('./pages/Customers.jsx'));
const Forecasts = lazy(() => import('./pages/Forecasts.jsx'));
const Alerts = lazy(() => import('./pages/Alerts.jsx'));
const Integrations = lazy(() => import('./pages/Integrations.jsx'));
const Team = lazy(() => import('./pages/Team.jsx'));
const Enterprise = lazy(() => import('./pages/Enterprise.jsx'));
const AIAssistant = lazy(() => import('./pages/AIAssistant.jsx'));
const TaxCompliance = lazy(() => import('./pages/TaxCompliance.jsx'));
const Invoices = lazy(() => import('./pages/Invoices.jsx'));
const CustomerInsights = lazy(() => import('./pages/CustomerInsights.jsx'));
const MultiStore = lazy(() => import('./pages/MultiStore.jsx'));
const Compliance = lazy(() => import('./pages/Compliance.jsx'));
const Settings = lazy(() => import('./pages/Settings.jsx'));
const DevOps = lazy(() => import('./pages/DevOps.jsx'));
const POS = lazy(() => import('./pages/POS.jsx'));
const Employees = lazy(() => import('./pages/Employees.jsx'));
const Returns = lazy(() => import('./pages/Returns.jsx'));
const Suppliers = lazy(() => import('./pages/Suppliers.jsx'));
const Promotions = lazy(() => import('./pages/Promotions.jsx'));
const Monitoring = lazy(() => import('./pages/Monitoring.jsx'));
const Khata = lazy(() => import('./pages/Khata.jsx'));
const DayClose = lazy(() => import('./pages/DayClose.jsx'));
const GSTInvoice = lazy(() => import('./pages/GSTInvoice.jsx'));
const GSTRates = lazy(() => import('./pages/GSTRates.jsx'));
const NotFound = lazy(() => import('./pages/NotFound.jsx'));

// Loading Fallback
const LoadingSpinner = () => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', color: 'var(--text-primary)' }}>
    <div style={{ textAlign: 'center' }}>
      <div style={{ animation: 'spin 1s linear infinite', width: 48, height: 48, border: '2px solid var(--border-md)', borderTopColor: 'var(--accent)', borderRadius: '50%', margin: '0 auto 16px' }}></div>
      <p>Loading Dashboard...</p>
    </div>
  </div>
);

// Layout wrapper component
function AppLayout() {
  return (
    <MainLayout>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/customers" element={<Customers />} />
            <Route path="/forecasts" element={<Forecasts />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/integrations" element={<Integrations />} />
            <Route path="/team" element={<Team />} />
            <Route path="/enterprise" element={<Enterprise />} />
            <Route path="/ai-assistant" element={<AIAssistant />} />
            <Route path="/tax-compliance" element={<TaxCompliance />} />
            <Route path="/invoices" element={<Invoices />} />
            <Route path="/customer-insights" element={<CustomerInsights />} />
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
            <Route path="/khata" element={<Khata />} />
            <Route path="/day-close" element={<DayClose />} />
            <Route path="/gst-invoice" element={<GSTInvoice />} />
            <Route path="/gst-rates" element={<GSTRates />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
      </Suspense>
    </MainLayout>
  );
}

// Root route handler - redirect based on auth status
function RootRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />;
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <QueryClientProvider client={queryClient}>
          <ErrorBoundary>
            <ToastProvider>
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route path="/" element={<RootRoute />} />
                <Route
                  path="/*"
                  element={
                    <ProtectedRoute>
                      <AppLayout />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </ToastProvider>
          </ErrorBoundary>
        </QueryClientProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
