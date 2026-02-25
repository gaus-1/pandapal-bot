/**
 * React Error Boundary — ловит ошибки рендеринга и показывает fallback UI.
 * Оборачивает приложение, чтобы один упавший компонент не сломал всё.
 */

import { Component, type ErrorInfo, type ReactNode } from 'react';
import { logger } from '../utils/logger';

interface ErrorBoundaryProps {
  children: ReactNode;
  /** Опциональный fallback UI */
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    logger.error('ErrorBoundary caught error:', error, errorInfo.componentStack);
  }

  private handleReset = (): void => {
    this.setState({ hasError: false, error: null });
  };

  private handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (!this.state.hasError) {
      return this.props.children;
    }

    if (this.props.fallback) {
      return this.props.fallback;
    }

    const isDev = typeof import.meta !== 'undefined' && import.meta.env?.DEV;
    return (
      <div className="flex items-center justify-center min-h-screen min-h-dvh bg-gray-50 dark:bg-slate-800 p-fib-4">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-fib-4">🐼</div>
          <h2 className="font-display text-xl font-bold text-gray-900 dark:text-slate-100 mb-fib-2">
            Что-то пошло не так
          </h2>
          <p className="font-sans text-gray-600 dark:text-slate-400 mb-fib-5 text-sm">
            Произошла непредвиденная ошибка. Попробуй обновить страницу.
          </p>
          {isDev && this.state.error && (
            <pre className="text-left text-xs bg-red-50 dark:bg-slate-900 p-fib-3 rounded mb-fib-4 overflow-auto max-h-32">
              {this.state.error.message}
            </pre>
          )}
          <div className="flex gap-fib-3 justify-center">
            <button
              onClick={this.handleReset}
              className="px-fib-4 py-fib-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors text-sm font-medium"
            >
              Попробовать снова
            </button>
            <button
              onClick={this.handleReload}
              className="px-fib-4 py-fib-2 bg-gray-200 dark:bg-slate-700 hover:bg-gray-300 dark:hover:bg-slate-600 text-gray-900 dark:text-slate-100 rounded-lg transition-colors text-sm font-medium"
            >
              Обновить страницу
            </button>
          </div>
        </div>
      </div>
    );
  }
}
