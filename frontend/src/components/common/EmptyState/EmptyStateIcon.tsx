/* eslint-disable react-refresh/only-export-components */
import React from 'react'
import { Film, Search, Settings, AlertCircle, Loader2, FileWarning, CheckCircle } from 'lucide-react'

export type EmptyStateVariant = 'noData' | 'noResults' | 'featureDisabled' | 'error' | 'loading' | 'not-found' | 'empty' | 'default' | 'elevated' | 'bordered'

export interface EmptyStateIconProps {
  variant: EmptyStateVariant
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const sizeClasses = {
  sm: 'w-8 h-8',
  md: 'w-12 h-12',
  lg: 'w-16 h-16',
}

const iconSizeMap = {
  sm: 20,
  md: 28,
  lg: 36,
}

const variantColors = {
  noData: 'text-primary-500',
  noResults: 'text-secondary-500',
  featureDisabled: 'text-amber-500',
  error: 'text-red-500',
  loading: 'text-primary-500',
  'not-found': 'text-secondary-500',
  empty: 'text-primary-500',
  default: 'text-secondary-500',
  elevated: 'text-primary-500',
  bordered: 'text-secondary-500',
}

const variantBackgrounds = {
  noData: 'bg-primary-50 dark:bg-primary-900/20',
  noResults: 'bg-secondary-50 dark:bg-secondary-800',
  featureDisabled: 'bg-amber-50 dark:bg-amber-900/20',
  error: 'bg-red-50 dark:bg-red-900/20',
  loading: 'bg-primary-50 dark:bg-primary-900/20',
  'not-found': 'bg-secondary-50 dark:bg-secondary-800',
  empty: 'bg-primary-50 dark:bg-primary-900/20',
  default: 'bg-transparent',
  elevated: 'bg-primary-50 dark:bg-primary-900/20',
  bordered: 'bg-secondary-50 dark:bg-secondary-800',
}

const IconRenderer: React.FC<{ variant: EmptyStateVariant; size: number; className: string }> = ({
  variant,
  size,
  className,
}) => {
  const defaultClass = 'animate-pulse'

  switch (variant) {
    case 'noData':
      return <Film size={size} className={`${className} ${defaultClass}`} />
    case 'noResults':
      return <Search size={size} className={className} />
    case 'featureDisabled':
      return <Settings size={size} className={`${className} ${defaultClass}`} />
    case 'error':
      return <AlertCircle size={size} className={`${className} animate-bounce`} />
    case 'loading':
      return <Loader2 size={size} className={`${className} animate-spin`} />
    default:
      return null
  }
}

export const EmptyStateIcon: React.FC<EmptyStateIconProps> = ({
  variant,
  size = 'md',
  className = '',
}) => {
  const iconSize = iconSizeMap[size]
  const variantColor = variantColors[variant]
  const variantBg = variantBackgrounds[variant]

  return (
    <div
      className={`
        inline-flex items-center justify-center rounded-full
        ${variantBg}
        ${sizeClasses[size]}
        ${className}
      `}
      aria-hidden="true"
    >
      <IconRenderer
        variant={variant}
        size={iconSize}
        className={variantColor}
      />
    </div>
  )
}

// Alternative icon set for more specific use cases
export const EmptyStateIcons = {
  // No data variants
  noMovies: () => <Film size={36} className="text-primary-500 animate-pulse" />,
  noTVShows: () => <Film size={36} className="text-primary-500 animate-pulse" />,
  noFiles: () => <FileWarning size={36} className="text-amber-500" />,
  
  // Success state (all configured)
  allSet: () => <CheckCircle size={36} className="text-green-500" />,
  
  // Search variants
  noSearchResults: () => <Search size={36} className="text-secondary-500" />,
  clearFilters: () => <Settings size={36} className="text-secondary-500" />,
  
  // Error variants
  loadingError: () => <AlertCircle size={36} className="text-red-500 animate-bounce" />,
  connectionError: () => <AlertCircle size={36} className="text-red-500" />,
  
  // Loading variants
  loading: () => <Loader2 size={36} className="text-primary-500 animate-spin" />,
}

export default EmptyStateIcon
