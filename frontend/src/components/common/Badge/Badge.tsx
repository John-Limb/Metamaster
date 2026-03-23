import React from 'react'

export interface BadgeProps {
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'indigo' | 'secondary'
  size?: 'sm' | 'md' | 'lg'
  dismissible?: boolean
  onDismiss?: () => void
  children: React.ReactNode
  className?: string
}

const variantClasses = {
  primary: 'bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200',
  success: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  warning: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
  danger: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
  info: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  indigo: 'bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200',
  secondary: 'bg-subtle text-body',
}

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-xs',
  lg: 'px-3 py-1 text-sm',
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'primary',
  size = 'md',
  dismissible = false,
  onDismiss,
  children,
  className = '',
}) => {
  return (
    <span
      className={`
        inline-flex items-center font-medium rounded-full
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${className}
      `}
    >
      {children}
      {dismissible && (
        <button
          type="button"
          className="ml-1 inline-flex items-center justify-center hover:opacity-75 focus:outline-none"
          onClick={onDismiss}
        >
          <svg
            className="w-3.5 h-3.5"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      )}
    </span>
  )
}
