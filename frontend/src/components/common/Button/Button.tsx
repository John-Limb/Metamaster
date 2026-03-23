import React from 'react'

export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success'
  size?: 'sm' | 'md' | 'lg'
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  loading?: boolean
  disabled?: boolean
  children: React.ReactNode
  onClick?: (e: React.MouseEvent<HTMLButtonElement>) => void
  className?: string
  fullWidth?: boolean
  type?: 'button' | 'submit' | 'reset'
}

const variantClasses = {
  primary: `
    bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800
    focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-secondary-900
    shadow-sm hover:shadow-md active:shadow-sm
  `,
  secondary: `
    bg-subtle text-body hover:bg-subtle/80 active:bg-subtle/60
    focus:ring-2 focus:ring-secondary-500 focus:ring-offset-2 dark:focus:ring-offset-secondary-900
    shadow-sm hover:shadow-md active:shadow-sm
  `,
  outline: `
    border-2 border-primary-600 text-primary-600 hover:bg-primary-50 active:bg-primary-100
    dark:hover:bg-primary-900/20 dark:active:bg-primary-900/30
    focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-secondary-900
  `,
  ghost: `
    text-dim hover:bg-subtle active:bg-subtle/60
    focus:ring-2 focus:ring-secondary-500 focus:ring-offset-2 dark:focus:ring-offset-secondary-900
  `,
  danger: `
    bg-danger-500 text-white hover:bg-danger-600 active:bg-danger-700
    focus:ring-2 focus:ring-danger-500 focus:ring-offset-2 dark:focus:ring-offset-secondary-900
    shadow-sm hover:shadow-md active:shadow-sm
  `,
  success: `
    bg-success-500 text-white hover:bg-success-600 active:bg-success-700
    focus:ring-2 focus:ring-success-500 focus:ring-offset-2 dark:focus:ring-offset-secondary-900
    shadow-sm hover:shadow-md active:shadow-sm
  `,
}

const sizeClasses = {
  sm: 'px-3 py-1.5 text-sm min-h-[32px]',
  md: 'px-4 py-2 text-sm min-h-[40px]',
  lg: 'px-6 py-3 text-base min-h-[48px]',
}

const iconSizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-4 h-4',
  lg: 'w-5 h-5',
}

const LoadingSpinner: React.FC<{ size: 'sm' | 'md' | 'lg' }> = ({ size }) => (
  <svg
    className={`animate-spin ${iconSizeClasses[size]} mr-2`}
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    role="status"
    aria-label="Loading"
  >
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="4"
    />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    />
  </svg>
)

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  leftIcon,
  rightIcon,
  loading = false,
  disabled = false,
  children,
  onClick,
  className = '',
  fullWidth = false,
  type = 'button',
}: ButtonProps) => {
  const isDisabled = disabled || loading

  const handleClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (!isDisabled && onClick) {
      onClick(e)
    }
  }

  return (
    <button
      type={type}
      className={`
        inline-flex items-center justify-center font-medium rounded-lg
        transition-all duration-150 ease-in-out
        focus:outline-none focus:ring-2 focus:ring-offset-2
        disabled:opacity-50 disabled:cursor-not-allowed
        hover:scale-[0.98] active:scale-[0.97]
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${fullWidth ? 'w-full' : ''}
        ${className}
      `}
      onClick={handleClick}
      disabled={isDisabled}
      aria-busy={loading}
    >
      {loading ? (
        <>
          <LoadingSpinner size={size} />
          <span className="sr-only">Loading...</span>
        </>
      ) : leftIcon ? (
        <span className={`${iconSizeClasses[size]} mr-2 flex-shrink-0`}>{leftIcon}</span>
      ) : null}
      <span className="flex-1">{children}</span>
      {!loading && rightIcon && (
        <span className={`${iconSizeClasses[size]} ml-2 flex-shrink-0`}>{rightIcon}</span>
      )}
    </button>
  )
}

export default Button
