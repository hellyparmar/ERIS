import React from 'react';
import { Link } from 'react-router-dom';
import { LayoutDashboard } from 'lucide-react';

const NotFound = () => (
  <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--c-canvas)', padding: '40px 16px' }}>
    <div style={{ textAlign: 'center', padding: '56px 40px', maxWidth: 480 }}>
      <div style={{ width: 40, height: 40, margin: '0 auto 20px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <LayoutDashboard size={40} style={{ color: '#D4C9B8' }} />
      </div>
      <p style={{ fontSize: 9, fontWeight: 700, letterSpacing: '2.5px', textTransform: 'uppercase', color: '#5C4F3D', marginBottom: 12 }}>404 — Page Not Found</p>
      <h1 style={{ fontFamily: 'var(--f-display)', fontSize: 16, fontWeight: 600, color: '#1A1208', marginBottom: 10 }}>We can't find that page.</h1>
      <p style={{ fontSize: 13, color: '#5C4F3D', lineHeight: 1.6, marginBottom: 28 }}>
        The page you are looking for does not exist or may have moved. Check the URL or return to your dashboard.
      </p>
      <Link to="/dashboard" className="action-btn primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, textDecoration: 'none' }}>
        <LayoutDashboard size={13} /> Go to Dashboard
      </Link>
    </div>
  </div>
);

export default NotFound;
