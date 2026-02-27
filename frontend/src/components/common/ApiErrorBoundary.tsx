import React from 'react'
import type { ReactNode } from 'react'
import { Button } from './Button/Button'
import { Toast, ToastContainer } from './Toast'
import type { ApiError, Toast as ToastType } from '@/types'

interface ApiErrorBoundaryProps {
  children: ReactNode
  onError?: (error: ApiError) => void
  fallback?: (error: ApiError, retry: () => void, reportIssue: () => void) => ReactNode
  showToast?: boolean
}

interface ApiErrorBoundaryState {
  hasError: boolean
  error: ApiError | null
  errorCount: number
  toasts: ToastType[]
}

/**
 * Error boundary specifically for API errors
 * Catches and handles API-related errors with proper notifications and retry functionality
 */
export class ApiErrorBoundary extends React.Component<ApiErrorBoundaryProps, ApiErrorBoundaryState> {
  constructor(props: ApiErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null, errorCount: 0, toasts: [] }
  }

  static getDerivedStateFromError(error: Error): Partial<ApiErrorBoundaryState> {
    const apiError: ApiError = {
      code: 'ERROR',
      message: error.message || 'An unexpected error occurred',
    }
    return { hasError: true, error: apiError }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    const apiError: ApiError = {
      code: 'ERROR',
      message: error.message || 'An unexpected error occurred',
      details: {
        componentStack: errorInfo.componentStack,
      },
    }

    console.error('API Error caught by boundary:', apiError, errorInfo)

    this.setState((state) => ({
      errorCount: state.errorCount + 1,
    }))

    // Show toast notification if enabled
    if (this.props.showToast !== false) {
      this.addToast({
        type: 'error',
        message: apiError.message,
        duration: 5000,
      })
    }

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(apiError)
    }
  }

  addToast = (toast: Omit<ToastType, 'id'>) => {
    const id = crypto.randomUUID()
    this.setState((prev) => ({
      toasts: [...prev.toasts, { ...toast, id }],
    }))
  }

  removeToast = (id: string) => {
    this.setState((prev) => ({
      toasts: prev.toasts.filter((t) => t.id !== id),
    }))
  }

  resetError = () => {
    this.setState({ hasError: false, error: null })
  }

  reportIssue = () => {
    const { error } = this.state
    const subject = encodeURIComponent(`Issue Report: ${error?.code || 'Unknown Error'}`)
    const body = encodeURIComponent(
      `Error: ${error?.message || 'Unknown error'}\n\nDetails:\n${JSON.stringify(error?.details, null, 2)}`
    )
    window.open(`mailto:support@metamaster.app?subject=${subject}&body=${body}`)
  }

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.resetError, this.reportIssue)
      }

      return (
        <>
          <div
            className="flex items-center justify-center min-h-[400px] bg-red-50 dark:bg-red-900/10 p-4"
            role="alert"
            aria-live="assertive"
          >
            <div className="bg-white dark:bg-secondary-800 p-8 rounded-lg shadow-lg max-w-md w-full animate-scale-in">
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
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">API Error</h1>
              </div>

              <div className="mb-4 p-3 bg-danger-50 dark:bg-danger-900/20 rounded-lg">
                <p className="text-sm font-semibold text-danger-700 dark:text-danger-300 mb-1">
                  Error Code: {this.state.error.code}
                </p>
                <p className="text-gray-700 dark:text-gray-300 text-sm">
                  {this.state.error.message}
                </p>
              </div>

              {import.meta.env.DEV && this.state.error.details && (
                <details className="mb-4 text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-secondary-700 p-3 rounded">
                  <summary className="cursor-pointer font-semibold mb-2">Error Details</summary>
                  <pre className="overflow-auto max-h-40">
                    {JSON.stringify(this.state.error.details, null, 2)}
                  </pre>
                </details>
              )}

              <div className="flex flex-col gap-2">
                <Button
                  variant="primary"
                  onClick={this.resetError}
                  className="w-full"
                  aria-label="Retry loading the content"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="mr-2"
                  >
                    <path d="M23 4v6h-6M1 20v-6h6" />
                    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                  </svg>
                  Try Again
                </Button>
                <Button
                  variant="outline"
                  onClick={this.reportIssue}
                  className="w-full"
                  aria-label="Report this issue via email"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="mr-2"
                  >
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                    <polyline points="22,6 12,13 2,6" />
                  </svg>
                  Report Issue
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => (window.location.href = '/')}
                  className="w-full"
                  aria-label="Go to home page"
                >
                  Go to Home
                </Button>
              </div>

              {this.state.errorCount > 2 && (
                <p className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center">
                  Multiple errors detected. Please consider refreshing the page or contacting support if the issue persists.
                </p>
              )}
            </div>
          </div>

          {/* Toast Container for error notifications */}
          <ToastContainer toasts={this.state.toasts} onRemoveToast={this.removeToast} />
        </>
      )
    }

    return this.props.children
  }
}

export default ApiErrorBoundary
