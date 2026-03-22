import React from 'react'

export interface AlertMessageProps {
  variant: 'error' | 'success'
  message: string
  className?: string
}

export function AlertMessage({ variant, message, className = '' }: AlertMessageProps) {
  const styles =
    variant === 'error'
      ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400'
      : 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-700 dark:text-green-400'
  return (
    <div
      role={variant === 'error' ? 'alert' : 'status'}
      className={`rounded-lg border px-4 py-3 text-sm ${styles} ${className}`}
    >
      {message}
    </div>
  )
}

export default AlertMessage
