import type { ApiError } from '@/types'

export interface ErrorLog {
  timestamp: string
  code: string
  message: string
  details?: Record<string, any>
  stack?: string
}

class ErrorHandler {
  private errorLogs: ErrorLog[] = []
  private maxLogs = 100

  /**
   * Handle API error and log it
   */
  public handleError(error: ApiError, context?: string): void {
    const errorLog: ErrorLog = {
      timestamp: new Date().toISOString(),
      code: error.code,
      message: error.message,
      details: error.details,
    }

    if (context) {
      errorLog.details = {
        ...errorLog.details,
        context,
      }
    }

    this.logError(errorLog)
  }

  /**
   * Log error to internal storage and console
   */
  private logError(errorLog: ErrorLog): void {
    this.errorLogs.push(errorLog)

    // Keep only recent logs
    if (this.errorLogs.length > this.maxLogs) {
      this.errorLogs = this.errorLogs.slice(-this.maxLogs)
    }

    // Log to console in development
    if (import.meta.env.DEV) {
      console.error(`[${errorLog.code}] ${errorLog.message}`, errorLog.details)
    }
  }

  /**
   * Get all logged errors
   */
  public getLogs(): ErrorLog[] {
    return [...this.errorLogs]
  }

  /**
   * Clear error logs
   */
  public clearLogs(): void {
    this.errorLogs = []
  }

  /**
   * Get error message for user display
   */
  public getUserMessage(error: ApiError): string {
    const errorMessages: Record<string, string> = {
      '400': 'Invalid request. Please check your input.',
      '401': 'Unauthorized. Please log in again.',
      '403': 'You do not have permission to perform this action.',
      '404': 'The requested resource was not found.',
      '408': 'Request timeout. Please try again.',
      '429': 'Too many requests. Please wait a moment and try again.',
      '500': 'Server error. Please try again later.',
      '502': 'Bad gateway. Please try again later.',
      '503': 'Service unavailable. Please try again later.',
      '504': 'Gateway timeout. Please try again later.',
      'NETWORK_ERROR': 'Network error. Please check your connection.',
      'ERROR': 'An unexpected error occurred.',
    }

    return errorMessages[error.code] || error.message || 'An error occurred'
  }

  /**
   * Check if error is retryable
   */
  public isRetryable(error: ApiError): boolean {
    const retryableCodes = ['408', '429', '500', '502', '503', '504', 'NETWORK_ERROR']
    return retryableCodes.includes(error.code)
  }

  /**
   * Check if error is authentication related
   */
  public isAuthError(error: ApiError): boolean {
    return error.code === '401' || error.code === '403'
  }

  /**
   * Check if error is validation related
   */
  public isValidationError(error: ApiError): boolean {
    return error.code === '400' || error.code === '422'
  }
}

export const errorHandler = new ErrorHandler()
