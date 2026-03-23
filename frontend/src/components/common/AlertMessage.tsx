import React from 'react'

export interface AlertMessageProps {
  variant: 'error' | 'success' | 'warning'
  message: string | React.ReactNode
  className?: string
}

export function AlertMessage({ variant, message, className = '' }: AlertMessageProps) {
  const styles = {
    error:   'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400',
    success: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-700 dark:text-green-400',
    warning: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300',
  }[variant]
  return (
    <div
      role={variant === 'success' ? 'status' : 'alert'}
      className={`rounded-lg border px-4 py-3 text-sm ${styles} ${className}`}
    >
      {message}
    </div>
  )
}

export default AlertMessage
