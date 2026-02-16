import { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function SystemHeartbeat() {
    const [online, setOnline] = useState(true);

    useEffect(() => {
        const check = async () => {
            try {
                await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(5000) });
                setOnline(true);
            } catch {
                setOnline(false);
            }
        };

        check();
        const id = setInterval(check, 15000);
        return () => clearInterval(id);
    }, []);

    return (
        <div className="flex items-center gap-1.5 text-xs">
            <div className={`w-2 h-2 rounded-full ${online ? 'bg-green-500' : 'bg-red-500 animate-pulse'
                }`} />
            <span className={online ? 'text-green-600' : 'text-red-600 font-medium'}>
                {online ? 'Online' : 'Offline — saving locally'}
            </span>
        </div>
    );
}
