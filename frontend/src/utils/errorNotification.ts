import type { ApiError } from '@/types'
import { errorHandler } from './errorHandler'

export interface ErrorNotification {
  id: string
  title: string
  message: string
  type: 'error' | 'warning' | 'info'
  duration?: number
  action?: {
    label: string
    onClick: () => void
  }
}

type ErrorNotificationListener = (notification: ErrorNotification) => void

class ErrorNotificationManager {
  private listeners: Set<ErrorNotificationListener> = new Set()
  private notificationId = 0

  /**
   * Subscribe to error notifications
   */
  public subscribe(listener: ErrorNotificationListener): () => void {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  /**
   * Notify error
   */
  private notify(notification: ErrorNotification): void {
    this.listeners.forEach((listener) => listener(notification))
  }

  /**
   * Show error notification from API error
   */
  public showError(error: ApiError, context?: string): void {
    const notification: ErrorNotification = {
      id: `error-${++this.notificationId}`,
      title: 'Error',
      message: errorHandler.getUserMessage(error),
      type: 'error',
      duration: 5000,
    }

    if (errorHandler.isRetryable(error)) {
      notification.action = {
        label: 'Retry',
        onClick: () => {
          // Retry logic would be handled by the component
        },
      }
    }

    if (import.meta.env.DEV && context) {
      console.error(`[${context}] ${error.code}: ${error.message}`)
    }

    this.notify(notification)
  }

  /**
   * Show warning notification
   */
  public showWarning(message: string, duration?: number): void {
    const notification: ErrorNotification = {
      id: `warning-${++this.notificationId}`,
      title: 'Warning',
      message,
      type: 'warning',
      duration: duration || 4000,
    }

    this.notify(notification)
  }

  /**
   * Show info notification
   */
  public showInfo(message: string, duration?: number): void {
    const notification: ErrorNotification = {
      id: `info-${++this.notificationId}`,
      title: 'Info',
      message,
      type: 'info',
      duration: duration || 3000,
    }

    this.notify(notification)
  }

  /**
   * Show custom notification
   */
  public show(notification: Omit<ErrorNotification, 'id'>): void {
    this.notify({
      ...notification,
      id: `notification-${++this.notificationId}`,
    })
  }

  /**
   * Show network error notification
   */
  public showNetworkError(): void {
    this.showError({
      code: 'NETWORK_ERROR',
      message: 'Network error occurred. Please check your connection.',
    })
  }

  /**
   * Show timeout error notification
   */
  public showTimeoutError(): void {
    this.showError({
      code: '408',
      message: 'Request timeout. Please try again.',
    })
  }

  /**
   * Show authentication error notification
   */
  public showAuthError(): void {
    this.showError({
      code: '401',
      message: 'Your session has expired. Please log in again.',
    })
  }

  /**
   * Show permission error notification
   */
  public showPermissionError(): void {
    this.showError({
      code: '403',
      message: 'You do not have permission to perform this action.',
    })
  }

  /**
   * Show validation error notification
   */
  public showValidationError(message?: string): void {
    this.showError({
      code: '400',
      message: message || 'Invalid input. Please check your data.',
    })
  }

  /**
   * Show server error notification
   */
  public showServerError(): void {
    this.showError({
      code: '500',
      message: 'Server error. Please try again later.',
    })
  }
}

export const errorNotificationManager = new ErrorNotificationManager()
