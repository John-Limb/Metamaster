import React from 'react'
import type { ReactNode } from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode | ((error: Error, retry: () => void) => ReactNode)
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorCount: number
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null, errorCount: 0 }
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
    this.setState((state) => ({
      errorCount: state.errorCount + 1,
    }))
  }

  resetError = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        if (React.isValidElement(this.props.fallback)) {
          return this.props.fallback
        }
        if (typeof this.props.fallback === 'function') {
          return this.props.fallback(this.state.error, this.resetError)
        }
      }

      return (
        <div className="flex items-center justify-center min-h-screen bg-red-50 dark:bg-red-900/10 p-4">
          <div className="bg-white dark:bg-secondary-800 p-8 rounded-lg shadow-lg max-w-md w-full">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex-shrink-0">
                <svg
                  className="h-8 w-8 text-danger-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4v.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-body">
                Something went wrong
              </h1>
            </div>
            <p className="text-dim mb-4 text-sm">
              {this.state.error.message}
            </p>
            {import.meta.env.DEV && (
              <details className="mb-4 text-xs text-hint bg-subtle p-3 rounded">
                <summary className="cursor-pointer font-semibold mb-2">Error Details</summary>
                <pre className="mt-2 overflow-auto max-h-40">{this.state.error.stack}</pre>
              </details>
            )}
            <div className="flex gap-2">
              <button
                onClick={this.resetError}
                className="flex-1 bg-primary-600 text-white py-2 rounded-lg hover:bg-primary-700 transition font-medium focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.reload()}
                className="flex-1 bg-secondary-200 dark:bg-secondary-700 text-gray-800 dark:text-white py-2 rounded-lg hover:bg-secondary-300 dark:hover:bg-secondary-600 transition font-medium focus:outline-none focus:ring-2 focus:ring-secondary-500 focus:ring-offset-2"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
