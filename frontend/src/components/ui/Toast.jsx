import React, { useState, useCallback } from 'react';
import { X, CheckCircle, AlertTriangle, Info, AlertOctagon } from 'lucide-react';

const icons = {
    success: <CheckCircle size={18} />,
    error: <AlertOctagon size={18} />,
    warning: <AlertTriangle size={18} />,
    info: <Info size={18} />,
};

export function Toast({ toasts, removeToast }) {
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
}

export function useToast() {
    const [localToasts, setLocalToasts] = useState([]);

    const addToast = useCallback((message, type = 'info', duration = 4000) => {
        const id = Date.now() + Math.random();
        setLocalToasts(prev => [...prev, { id, message, type }]);
        if (typeof window !== 'undefined' && window.dispatchEvent) {
            window.dispatchEvent(new CustomEvent('global-toast', { detail: { message, type, duration } }));
        }
        if (duration > 0) {
            setTimeout(() => {
                setLocalToasts(prev => prev.filter(t => t.id !== id));
            }, duration);
        }
        return id;
    }, []);

    const removeToast = useCallback((id) => {
        setLocalToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    return { toasts: localToasts, addToast, removeToast, showToast: addToast };
}

export default Toast;
