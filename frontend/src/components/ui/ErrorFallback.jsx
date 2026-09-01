import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

const ErrorFallback = ({ error, resetErrorBoundary }) => {
    const isDevelopment = import.meta.env.DEV;

    return (
        <div className="page-wrap" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '80vh' }}>
            <div className="panel" style={{ maxWidth: 600, width: '100%', textAlign: 'center' }}>
                <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 24 }}>
                    <div style={{ width: 80, height: 80, borderRadius: '50%', background: 'var(--danger-dim, rgba(231,76,60,0.15))', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <AlertTriangle size={32} style={{ color: 'var(--red, #e74c3c)' }} />
                    </div>
                </div>

                <h2 style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
                    Oops! Something went wrong
                </h2>
                <p style={{ color: 'var(--text-muted)', marginBottom: 32, lineHeight: 1.6 }}>
                    We encountered an unexpected error. Don't worry, our team has been notified and we're working on a fix.
                </p>

                {isDevelopment && error && (
                    <details style={{ marginBottom: 24, textAlign: 'left' }}>
                        <summary style={{ cursor: 'pointer', fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8 }}>
                            Technical Details (Development Mode)
                        </summary>
                        <div style={{ background: 'var(--surface-alt)', padding: 16, borderRadius: 'var(--r-lg)', overflow: 'auto', maxHeight: 200 }}>
                            <pre style={{ fontSize: 11, color: 'var(--red)', margin: 0, whiteSpace: 'pre-wrap' }}>
                                {error.toString()}
                                {error.stack && `\n\n${error.stack}`}
                            </pre>
                        </div>
                    </details>
                )}

                <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                    <button onClick={resetErrorBoundary} className="btn btn-primary">
                        <RefreshCw size={16} /> Try Again
                    </button>
                    <button onClick={() => window.location.href = '/'} className="btn btn-ghost">
                        <Home size={16} /> Back to Dashboard
                    </button>
                </div>

                <p style={{ fontSize: 12, color: 'var(--text-faint)', marginTop: 32 }}>
                    Need help? Contact support at{' '}
                    <a href="mailto:support@eris.retail" style={{ color: 'var(--accent)' }}>support@eris.retail</a>
                </p>
            </div>
        </div>
    );
};

export default ErrorFallback;
