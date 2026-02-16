import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle, AlertCircle, X, Info } from 'lucide-react';

const ToastContext = createContext();

export const useToast = () => useContext(ToastContext);

export const ToastProvider = ({ children }) => {
    const [toasts, setToasts] = useState([]);

    const addToast = useCallback((message, type = 'success', duration = 3000) => {
        const id = Date.now();
        setToasts(prev => [...prev, { id, message, type }]);
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, duration);
    }, []);

    const removeToast = (id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    };

    return (
        <ToastContext.Provider value={{ addToast }}>
            {children}
            <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">

                {toasts.map(toast => (
                    <div
                        key={toast.id}
                        className={`
                                min-w-[300px] p-4 rounded-lg shadow-lg border backdrop-blur-md flex items-center gap-3
                                ${toast.type === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-500' :
                                toast.type === 'error' ? 'bg-red-500/10 border-red-500/20 text-red-500' :
                                    'bg-blue-500/10 border-blue-500/20 text-blue-500'}
                            `}
                    >
                        {toast.type === 'success' && <CheckCircle size={20} />}
                        {toast.type === 'error' && <AlertCircle size={20} />}
                        {toast.type === 'info' && <Info size={20} />}

                        <span className="text-sm font-medium flex-1">{toast.message}</span>

                        <button onClick={() => removeToast(toast.id)} className="opacity-60 hover:opacity-100">
                            <X size={16} />
                        </button>
                    </div>
                ))}

            </div>
        </ToastContext.Provider>
    );
};
