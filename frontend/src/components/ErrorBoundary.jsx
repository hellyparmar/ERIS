import React from 'react';
import { ErrorBoundary as ReactErrorBoundary } from 'react-error-boundary';
import { AlertTriangle, RefreshCw, LayoutDashboard } from 'lucide-react';
import { Link } from 'react-router-dom';

function ErrorFallback({ error, resetErrorBoundary }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-2xl bg-white border border-slate-200 rounded-3xl p-8 shadow-xl">
        <div className="flex items-center gap-4 mb-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-red-100 text-red-600">
            <AlertTriangle className="h-8 w-8" />
          </div>
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-red-600">Error</p>
            <h1 className="mt-2 text-3xl font-semibold text-slate-900">Something went wrong</h1>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Something went wrong. Our team has been notified.
            </p>
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-2">
          <button
            type="button"
            onClick={resetErrorBoundary}
            className="inline-flex items-center justify-center gap-2 rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            <RefreshCw className="h-4 w-4" />
            Try Again
          </button>
          <Link
            to="/dashboard"
            className="inline-flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-50"
          >
            <LayoutDashboard className="h-4 w-4" />
            Go to Dashboard
          </Link>
        </div>

        {import.meta.env.DEV && error ? (
          <div className="mt-8 rounded-2xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">Debug info</p>
            <pre className="mt-2 max-h-40 overflow-auto text-xs text-slate-700">{error.toString()}</pre>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function onErrorHandler(error, info) {
  if (import.meta.env.PROD) {
    console.error('ErrorBoundary caught an error:', error, info);
  }
}

const ErrorBoundary = ({ children }) => (
  <ReactErrorBoundary FallbackComponent={ErrorFallback} onError={onErrorHandler}>
    {children}
  </ReactErrorBoundary>
);

export default ErrorBoundary;
