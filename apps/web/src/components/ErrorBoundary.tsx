import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an unhandled exception:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-[50vh] flex items-center justify-center p-6">
          <div className="glass-card max-w-md w-full p-8 text-center shadow-glass space-y-4">
            <div className="w-12 h-12 mx-auto text-amber flex items-center justify-center">
              <AlertTriangle className="w-8 h-8" strokeWidth={1.5} />
            </div>
            <h2 className="text-lg font-bold text-ink-900 dark:text-mist">Operational View Degraded</h2>
            <p className="text-xs text-ink-600 dark:text-sky-300">
              The interface encountered a transient error while rendering telemetry. The backend state remains intact.
            </p>
            {this.state.error && (
              <pre className="text-[11px] font-mono text-left bg-sky-50 dark:bg-white/5 p-3 rounded-lg overflow-x-auto text-ink-600 dark:text-sky-300">
                {this.state.error.message}
              </pre>
            )}
            <button
              onClick={() => {
                this.setState({ hasError: false });
                window.location.reload();
              }}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-btn bg-sky-500 text-white font-medium text-xs hover:bg-sky-700 transition-colors shadow-sm"
            >
              <RefreshCw className="w-3.5 h-3.5" strokeWidth={1.5} />
              <span>Retry and reload view</span>
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
