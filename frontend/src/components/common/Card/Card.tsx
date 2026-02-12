import React from 'react'

export interface CardProps {
  variant?: 'default' | 'elevated' | 'outlined' | 'bordered'
  padding?: 'none' | 'sm' | 'md' | 'lg'
  children: React.ReactNode
  className?: string
  onClick?: () => void
  loading?: boolean
  hoverable?: boolean
  role?: string
  style?: React.CSSProperties
}

interface CardHeaderProps {
  children: React.ReactNode
  className?: string
}

interface CardContentProps {
  children: React.ReactNode
  className?: string
}

interface CardFooterProps {
  children: React.ReactNode
  className?: string
}

const paddingClasses = {
  none: '',
  sm: 'p-3',
  md: 'p-5',
  lg: 'p-6',
}

const variantClasses = {
  default: 'bg-white dark:bg-secondary-800 border border-secondary-200 dark:border-secondary-700',
  elevated: 'bg-white dark:bg-secondary-800',
  outlined: 'bg-transparent border border-secondary-200 dark:border-secondary-700',
  bordered: 'bg-transparent border border-secondary-200 dark:border-secondary-700',
}

const variantShadowClasses = {
  default: 'shadow-subtle',
  elevated: 'shadow-medium',
  outlined: 'shadow-none',
  bordered: 'shadow-none',
}

const hoverClasses = {
  default: `
    hover:shadow-medium hover:-translate-y-0.5
    transition-all duration-150 ease-in-out
  `,
  elevated: `
    hover:shadow-large hover:-translate-y-1
    transition-all duration-150 ease-in-out
  `,
  outlined: `
    hover:shadow-medium hover:-translate-y-0.5
    hover:border-primary-300 dark:hover:border-primary-700
    transition-all duration-150 ease-in-out
  `,
  bordered: `
    hover:shadow-medium hover:-translate-y-0.5
    hover:border-primary-300 dark:hover:border-primary-700
    transition-all duration-150 ease-in-out
  `,
}

export const Card: React.FC<CardProps> & {
  Header: React.FC<CardHeaderProps>
  Content: React.FC<CardContentProps>
  Footer: React.FC<CardFooterProps>
} = ({
  variant = 'default',
  padding = 'md',
  children,
  className = '',
  onClick,
  loading = false,
  hoverable = false,
  role,
  style,
}) => {
  const Component = onClick || hoverable ? 'button' : 'div'

  // Normalize bordered to outlined for class lookups
  const normalizedVariant = (variant === 'bordered' ? 'outlined' : variant) as 'default' | 'elevated' | 'outlined'

  const cardClasses = `
    ${onClick ? 'w-full text-left cursor-pointer' : ''}
    ${variantClasses[normalizedVariant]}
    ${paddingClasses[padding]}
    ${variantShadowClasses[normalizedVariant]}
    ${hoverable || onClick ? hoverClasses[normalizedVariant] : ''}
    rounded-lg
    ${className}
  `.trim()

  if (loading) {
    return (
      <div className={`${cardClasses} relative overflow-hidden`}>
        <div className="animate-shimmer absolute inset-0" />
      </div>
    )
  }

  return (
    <Component
      className={cardClasses}
      onClick={onClick}
      disabled={onClick ? true : undefined}
      tabIndex={onClick || hoverable ? 0 : undefined}
      role={role || (onClick || hoverable ? 'button' : undefined)}
      aria-label={onClick ? undefined : undefined}
      style={style}
    >
      {children}
    </Component>
  )
}

Card.Header = ({ children, className = '' }) => (
  <div
    className={`border-b border-secondary-200 dark:border-secondary-700 pb-4 mb-4 ${className}`}
    role="heading"
    aria-level={3}
  >
    {children}
  </div>
)

Card.Content = ({ children, className = '' }) => (
  <div className={className}>{children}</div>
)

Card.Footer = ({ children, className = '' }) => (
  <div className={`border-t border-secondary-200 dark:border-secondary-700 pt-4 mt-4 ${className}`}>
    {children}
  </div>
)

export default Card
