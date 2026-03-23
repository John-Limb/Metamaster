import React from 'react'
import { Card } from '@/components/common/Card'
import { EmptyState, type EmptyStateProps } from './EmptyState'
import { cn } from '@/utils/cn'

export interface EmptyStateCardProps extends Omit<EmptyStateProps, 'className'> {
  className?: string
  variant?: 'default' | 'bordered' | 'elevated'
  minHeight?: string | number
}

/**
 * Card-wrapped version of EmptyState for use in grids and layouts
 */
export const EmptyStateCard: React.FC<EmptyStateCardProps> = ({
  variant = 'bordered',
  minHeight = 200,
  className,
  ...props
}: EmptyStateCardProps) => {
  const cardVariant = variant === 'default' ? 'bordered' : variant

  return (
    <Card
      variant={cardVariant}
      className={cn('flex items-center justify-center', className)}
      style={{ minHeight }}
    >
      <EmptyState {...props} />
    </Card>
  )
}

// Skeleton loading state for EmptyStateCard
export const EmptyStateCardSkeleton: React.FC<{ count?: number; minHeight?: number }> = ({
  count = 1,
  minHeight = 200,
}: { count?: number; minHeight?: number }) => {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <Card
          key={index}
          variant="bordered"
          className="flex items-center justify-center animate-pulse"
          style={{ minHeight }}
        >
          <div className="text-center p-8">
            {/* Icon placeholder */}
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-subtle" />

            {/* Title placeholder */}
            <div className="h-5 w-32 mx-auto mb-2 rounded bg-subtle" />

            {/* Description placeholder */}
            <div className="h-4 w-48 mx-auto rounded bg-subtle" />
          </div>
        </Card>
      ))}
    </>
  )
}

// Inline empty state for smaller spaces
export const InlineEmptyState: React.FC<Omit<EmptyStateProps, 'illustration' | 'className'>> = ({
  iconVariant = 'noData',
  title,
  description,
  action,
  secondaryAction,
}: Omit<EmptyStateProps, 'illustration' | 'className'>) => {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <div className="flex items-center gap-3 mb-3">
        {/* Small icon */}
        <div className="w-8 h-8 rounded-full bg-subtle flex items-center justify-center">
          <svg
            className="w-4 h-4 text-hint"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            {iconVariant === 'noData' && (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            )}
            {iconVariant === 'noResults' && (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            )}
            {iconVariant === 'error' && (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            )}
            {iconVariant === 'loading' && (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            )}
          </svg>
        </div>
        
        <div className="text-left">
          <p className="text-sm font-medium text-body">{title}</p>
          <p className="text-xs text-hint">{description}</p>
        </div>
      </div>

      {(action || secondaryAction) && (
        <div className="flex gap-2 mt-3">
          {secondaryAction && (
            <button
              onClick={secondaryAction.onClick}
              className="text-xs px-3 py-1.5 text-dim hover:text-body transition-colors"
            >
              {secondaryAction.label}
            </button>
          )}
          {action && (
            <button
              onClick={action.onClick}
              className="text-xs px-3 py-1.5 bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors"
            >
              {action.label}
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export default EmptyStateCard
