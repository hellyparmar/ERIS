import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

/**
 * ErrorBoundary Component
 * Catches JavaScript errors anywhere in the child component tree
 * Prevents "White Screen of Death" crashes
 */
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            hasError: false,
            error: null,
            errorInfo: null
        };
    }

    static getDerivedStateFromError(error) {
        // Update state so the next render will show the fallback UI
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        // Log error details for debugging
        console.error('ErrorBoundary caught an error:', error, errorInfo);

        this.setState({
            error,
            errorInfo
        });

        // You can also log the error to an error reporting service
        // logErrorToService(error, errorInfo);
    }

    handleReset = () => {
        this.setState({
            hasError: false,
            error: null,
            errorInfo: null
        });
    };

    render() {
        if (this.state.hasError) {
            // Fallback UI
            return (
                <div className="min-h-screen flex items-center justify-center bg-background p-6">
                    <div className="max-w-2xl w-full bg-card border-2 border-destructive rounded-xl p-8 shadow-2xl">
                        <div className="flex items-center gap-4 mb-6">
                            <div className="p-4 bg-destructive/10 rounded-full">
                                <AlertTriangle className="w-8 h-8 text-destructive" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-foreground">
                                    Oops! Something went wrong
                                </h1>
                                <p className="text-muted-foreground mt-1">
                                    An unexpected error occurred in the application
                                </p>
                            </div>
                        </div>

                        {process.env.NODE_ENV === 'development' && this.state.error && (
                            <div className="mb-6 p-4 bg-muted rounded-lg border border-border">
                                <h3 className="font-semibold text-foreground mb-2">Error Details:</h3>
                                <pre className="text-xs text-muted-foreground overflow-auto max-h-40 whitespace-pre-wrap">
                                    {this.state.error.toString()}
                                    {this.state.errorInfo && this.state.errorInfo.componentStack}
                                </pre>
                            </div>
                        )}

                        <div className="flex gap-4">
                            <button
                                onClick={this.handleReset}
                                className="flex items-center gap-2 px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors"
                            >
                                <RefreshCw className="w-4 h-4" />
                                Try Again
                            </button>
                            <button
                                onClick={() => window.location.href = '/'}
                                className="px-6 py-3 bg-secondary text-secondary-foreground rounded-lg font-medium hover:bg-secondary/80 transition-colors"
                            >
                                Go to Dashboard
                            </button>
                        </div>

                        <div className="mt-6 pt-6 border-t border-border">
                            <p className="text-sm text-muted-foreground">
                                If this problem persists, please contact support or try refreshing the page.
                            </p>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
