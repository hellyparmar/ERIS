import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { HelmetProvider } from 'react-helmet-async';
import { queryClient } from './lib/queryClient.js';
import { ToastProvider } from './contexts/ToastContext';
import { ErrorBoundary } from 'react-error-boundary';
import ErrorFallback from './components/ui/ErrorFallback';
import { ThemeProvider } from './hooks/useTheme';
import { LanguageProvider } from './hooks/useLanguage';
import MainLayout from './components/layout/MainLayout';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Login from './pages/Login';
import SEO from './components/SEO';
import { MotionConfig } from 'framer-motion';

const Dashboard = lazy(() => import('./pages/Dashboard.jsx'));
const Analytics = lazy(() => import('./pages/Analytics.jsx'));
const Inventory = lazy(() => import('./pages/Inventory.jsx'));
const Customers = lazy(() => import('./pages/Customers.jsx'));
const Forecasts = lazy(() => import('./pages/Forecasts.jsx'));
const Alerts = lazy(() => import('./pages/Alerts.jsx'));
const DayClose = lazy(() => import('./pages/DayClose.jsx'));
const AIAssistant = lazy(() => import('./pages/AIAssistant.jsx'));
const Integrations = lazy(() => import('./pages/Integrations.jsx'));
const TaxCompliance = lazy(() => import('./pages/TaxCompliance.jsx'));
const Invoices = lazy(() => import('./pages/Invoices.jsx'));
const CustomerInsights = lazy(() => import('./pages/CustomerInsights.jsx'));
const Settings = lazy(() => import('./pages/Settings.jsx'));
const Employees = lazy(() => import('./pages/Employees.jsx'));
const Suppliers = lazy(() => import('./pages/Suppliers.jsx'));
const Sales = lazy(() => import('./pages/Sales.jsx'));
const GSTInvoice = lazy(() => import('./pages/GSTInvoice.jsx'));

const Outlets = lazy(() => import('./pages/Outlets.jsx'));
const CausalAnalysis = lazy(() => import('./pages/CausalAnalysis.jsx'));
const CommunicationHub = lazy(() => import('./pages/CommunicationHub.jsx'));
const NotFound = lazy(() => import('./pages/NotFound.jsx'));

const LoadingSpinner = () => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', color: 'var(--text-primary)' }}>
    <div style={{ textAlign: 'center' }}>
      <div style={{ animation: 'spin 1s linear infinite', width: 48, height: 48, border: '2px solid var(--border-md)', borderTopColor: 'var(--accent)', borderRadius: '50%', margin: '0 auto 16px' }}></div>
      <p>Loading...</p>
    </div>
  </div>
);

const ALL_ROLES = ['super_admin', 'superadmin', 'area_manager', 'outlet_manager', 'manager'];
const SUPER_AND_AREA = ['super_admin', 'superadmin', 'area_manager'];
const SUPER_ONLY = ['super_admin', 'superadmin'];

function AppLayout() {
  return (
    <MainLayout>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<ProtectedRoute roles={ALL_ROLES}><Dashboard /></ProtectedRoute>} />
            <Route path="/analytics" element={<ProtectedRoute roles={SUPER_AND_AREA}><Analytics /></ProtectedRoute>} />
            <Route path="/inventory" element={<ProtectedRoute roles={ALL_ROLES}><Inventory /></ProtectedRoute>} />
            <Route path="/customers" element={<ProtectedRoute roles={ALL_ROLES}><Customers /></ProtectedRoute>} />
            <Route path="/forecasts" element={<ProtectedRoute roles={ALL_ROLES}><Forecasts /></ProtectedRoute>} />
            <Route path="/alerts" element={<ProtectedRoute roles={ALL_ROLES}><Alerts /></ProtectedRoute>} />
            <Route path="/day-close" element={<ProtectedRoute roles={ALL_ROLES}><DayClose /></ProtectedRoute>} />
            <Route path="/ai-assistant" element={<ProtectedRoute roles={ALL_ROLES}><AIAssistant /></ProtectedRoute>} />
            <Route path="/tax-compliance" element={<ProtectedRoute roles={SUPER_ONLY}><TaxCompliance /></ProtectedRoute>} />
            <Route path="/integrations" element={<ProtectedRoute roles={SUPER_ONLY}><Integrations /></ProtectedRoute>} />
            <Route path="/invoices" element={<ProtectedRoute roles={ALL_ROLES}><Invoices /></ProtectedRoute>} />
            <Route path="/customer-insights" element={<ProtectedRoute roles={SUPER_AND_AREA}><CustomerInsights /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute roles={ALL_ROLES}><Settings /></ProtectedRoute>} />
            <Route path="/employees" element={<ProtectedRoute roles={SUPER_ONLY}><Employees /></ProtectedRoute>} />
            <Route path="/suppliers" element={<ProtectedRoute roles={SUPER_ONLY}><Suppliers /></ProtectedRoute>} />
            <Route path="/sales" element={<ProtectedRoute roles={ALL_ROLES}><Sales /></ProtectedRoute>} />
            <Route path="/gst-invoice" element={<ProtectedRoute roles={ALL_ROLES}><GSTInvoice /></ProtectedRoute>} />

            <Route path="/outlets" element={<ProtectedRoute roles={SUPER_AND_AREA}><Outlets /></ProtectedRoute>} />
            <Route path="/causal-analysis" element={<ProtectedRoute roles={SUPER_AND_AREA}><CausalAnalysis /></ProtectedRoute>} />
            <Route path="/communication" element={<ProtectedRoute roles={ALL_ROLES}><CommunicationHub /></ProtectedRoute>} />
            <Route path="*" element={<NotFound />} />
          </Routes>
      </Suspense>
    </MainLayout>
  );
}

function RootRoute() {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <LoadingSpinner />;
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <Navigate to="/login" replace />;
}

function App() {
  return (
    <HelmetProvider>
      <BrowserRouter>
        <AuthProvider>
          <QueryClientProvider client={queryClient}>
            <ThemeProvider>
            <LanguageProvider>
            <ErrorBoundary FallbackComponent={ErrorFallback}>
              <ToastProvider>
                <SEO />
                <MotionConfig reducedMotion="user">
                  <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/*" element={
                      <ProtectedRoute>
                        <AppLayout />
                      </ProtectedRoute>
                    } />
                  </Routes>
                </MotionConfig>
              </ToastProvider>
            </ErrorBoundary>
            </LanguageProvider>
            </ThemeProvider>
          </QueryClientProvider>
        </AuthProvider>
      </BrowserRouter>
    </HelmetProvider>
  );
}

export default App;
