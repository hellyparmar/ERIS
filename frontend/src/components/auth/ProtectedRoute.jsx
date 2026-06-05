import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const AccessDenied = () => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    backgroundColor: 'var(--bg-primary)',
    color: 'var(--text-primary)',
  }}>
    <div style={{
      textAlign: 'center',
      padding: '40px',
    }}>
      <h1 style={{ fontSize: '48px', fontWeight: 'bold', marginBottom: '16px' }}>403</h1>
      <h2 style={{ fontSize: '24px', marginBottom: '8px' }}>Access Denied</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>
        You do not have permission to access this page.
      </p>
      <a 
        href="/dashboard"
        style={{
          display: 'inline-block',
          padding: '8px 24px',
          backgroundColor: 'var(--primary)',
          color: 'white',
          textDecoration: 'none',
          borderRadius: '4px',
          fontWeight: '500',
        }}
      >
        Go to Dashboard
      </a>
    </div>
  </div>
);

function ProtectedRoute({ children, roles }) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        color: 'var(--text-primary)',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            animation: 'spin 1s linear infinite',
            width: 48,
            height: 48,
            border: '2px solid var(--border-md)',
            borderTopColor: 'var(--accent)',
            borderRadius: '50%',
            margin: '0 auto 16px',
          }}></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role-based access if roles are specified
  if (roles && user && !roles.includes(user.role)) {
    return <AccessDenied />;
  }

  // Render the protected component
  return children;
}

export default ProtectedRoute;
