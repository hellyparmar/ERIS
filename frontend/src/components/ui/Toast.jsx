import React from 'react';
import { Check, X, AlertTriangle, AlertCircle } from 'lucide-react';
import { useToast } from '../../contexts/ToastContext';
export { useToast };

const iconMap = {
  success: Check,
  error: X,
  warning: AlertTriangle,
  info: AlertCircle,
};

const colorMap = {
  success: '#10b981',
  error: '#ef4444',
  warning: '#f59e0b',
  info: '#3b82f6',
};

const Toast = ({ toast, onRemove }) => {
  const Icon = iconMap[toast.type] || iconMap.info;
  const color = colorMap[toast.type] || colorMap.info;

  return (
    <div
      style={{
        animation: 'slideIn 0.3s ease-out',
        marginBottom: '12px',
        borderLeft: `4px solid ${color}`,
        backgroundColor: '#ffffff',
        borderRadius: '6px',
        padding: '16px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
        minWidth: '320px',
        maxWidth: '400px',
      }}
    >
      <Icon
        size={20}
        style={{
          color,
          flexShrink: 0,
          marginTop: '2px',
        }}
      />
      <div style={{ flex: 1, fontSize: '14px', color: '#374151', lineHeight: '1.5' }}>
        {toast.message}
      </div>
      <button
        onClick={() => onRemove(toast.id)}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '0',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#9ca3af',
          flexShrink: 0,
          transition: 'color 0.2s',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.color = '#6b7280')}
        onMouseLeave={(e) => (e.currentTarget.style.color = '#9ca3af')}
      >
        <X size={18} />
      </button>
    </div>
  );
};

export const ToastContainer = () => {
  const { toasts, removeToast } = useToast();

  return (
    <div
      style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: 9999,
        pointerEvents: 'none',
      }}
    >
      <style>{`
        @keyframes slideIn {
          from {
            transform: translateX(400px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }

        @keyframes slideOut {
          from {
            transform: translateX(0);
            opacity: 1;
          }
          to {
            transform: translateX(400px);
            opacity: 0;
          }
        }
      `}</style>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column-reverse',
          gap: '0',
          pointerEvents: 'auto',
        }}
      >
        {toasts.map((toast) => (
          <Toast key={toast.id} toast={toast} onRemove={removeToast} />
        ))}
      </div>
    </div>
  );
};

export default ToastContainer;

