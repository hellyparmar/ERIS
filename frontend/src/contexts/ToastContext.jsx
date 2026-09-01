import React, { createContext, useContext, useState, useCallback } from 'react';
import { X, CheckCircle, AlertTriangle, Info, AlertOctagon } from 'lucide-react';

const icons = {
    success: <CheckCircle size={18} />,
    error: <AlertOctagon size={18} />,
    warning: <AlertTriangle size={18} />,
    info: <Info size={18} />,
};

const ToastContext = createContext(null);

export { ToastContext };

export const useToast = () => {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within ToastProvider');
    }
    return context;
};

const ToastContainer = ({ toasts, removeToast }) => {
    if (!toasts || toasts.length === 0) return null;
    return (
        <div className="toast-container">
            {toasts.map((t) => (
                <div key={t.id} className={`toast toast-${t.type || 'info'}`} style={{ animation: 'slideInRight 0.3s ease' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        {icons[t.type] || icons.info}
                        {t.message}
                    </span>
                    <button onClick={() => removeToast(t.id)} className="toast-close">
                        <X size={14} />
                    </button>
                </div>
            ))}
        </div>
    );
};

export const ToastProvider = ({ children }) => {
    const [toasts, setToasts] = useState([]);

    const showToast = useCallback((message, type = 'info', duration = 4000) => {
        const id = Date.now();
        const newToast = { id, message, type };

        setToasts((prevToasts) => {
            const updatedToasts = [...prevToasts, newToast];
            if (updatedToasts.length > 4) {
                return updatedToasts.slice(-4);
            }
            return updatedToasts;
        });

        if (duration > 0) {
            setTimeout(() => {
                setToasts((prev) => prev.filter(t => t.id !== id));
            }, duration);
        }
    }, []);

    const removeToast = useCallback((id) => {
        setToasts((prevToasts) => prevToasts.filter((toast) => toast.id !== id));
    }, []);

    React.useEffect(() => {
        const handleGlobalToast = (event) => {
            const { message, type = 'info', duration = 4000 } = event.detail || {};
            if (message) {
                showToast(message, type, duration);
            }
        };

        window.addEventListener('global-toast', handleGlobalToast);
        return () => window.removeEventListener('global-toast', handleGlobalToast);
    }, [showToast]);

    return (
        <ToastContext.Provider value={{ showToast, addToast: showToast, removeToast, toasts }}>
            {children}
            <ToastContainer toasts={toasts} removeToast={removeToast} />
        </ToastContext.Provider>
    );
};
