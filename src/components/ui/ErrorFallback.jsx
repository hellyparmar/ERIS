/**
 * Error Fallback Component
 * Displays user-friendly error UI when component crashes
 */

import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import Card from './Card';

const ErrorFallback = ({ error, resetErrorBoundary }) => {
    const isDevelopment = import.meta.env.DEV;

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
            <Card className="max-w-2xl w-full">
                <div className="text-center">
                    {/* Error Icon */}
                    <div className="flex justify-center mb-6">
                        <div className="w-20 h-20 bg-red-100 dark:bg-red-900/20 rounded-full flex items-center justify-center">
                            <AlertTriangle className="w-12 h-12 text-red-600 dark:text-red-400" />
                        </div>
                    </div>

                    {/* Title */}
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
                        Oops! Something went wrong
                    </h1>

                    {/* Description */}
                    <p className="text-gray-600 dark:text-gray-400 mb-8 max-w-md mx-auto">
                        We encountered an unexpected error. Don't worry, our team has been notified and we're working on a fix.
                    </p>

                    {/* Error Details (Development Only) */}
                    {isDevelopment && error && (
                        <details className="mb-8 text-left">
                            <summary className="cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Technical Details (Development Mode)
                            </summary>
                            <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg overflow-auto">
                                <pre className="text-xs text-red-600 dark:text-red-400">
                                    {error.toString()}
                                    {error.stack && `\n\n${error.stack}`}
                                </pre>
                            </div>
                        </details>
                    )}

                    {/* Action Buttons */}
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <button
                            onClick={resetErrorBoundary}
                            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
                        >
                            <RefreshCw className="w-5 h-5" />
                            Try Again
                        </button>

                        <button
                            onClick={() => window.location.href = '/'}
                            className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white font-medium rounded-lg transition-colors"
                        >
                            <Home className="w-5 h-5" />
                            Back to Dashboard
                        </button>
                    </div>

                    {/* Support Info */}
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-8">
                        Need help? Contact support at{' '}
                        <a href="mailto:support@rdios.com" className="text-blue-600 dark:text-blue-400 hover:underline">
                            support@rdios.com
                        </a>
                    </p>
                </div>
            </Card>
        </div>
    );
};

export default ErrorFallback;
