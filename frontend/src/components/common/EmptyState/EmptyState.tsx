/* eslint-disable react-refresh/only-export-components */
import React from 'react'
import { Button, type ButtonProps } from '../Button/Button'
import { EmptyStateIcon, type EmptyStateVariant } from './EmptyStateIcon'
import { ProgressBar } from '../ProgressBar/ProgressBar'

export interface EmptyStateAction {
  label: string
  onClick: () => void
  variant?: ButtonProps['variant']
  disabled?: boolean
  loading?: boolean
}

export interface EmptyStateProps {
  icon?: React.ReactNode
  variant?: EmptyStateVariant
  iconVariant?: EmptyStateVariant
  title: string
  description: string
  action?: EmptyStateAction
  secondaryAction?: EmptyStateAction
  illustration?: React.ReactNode
  className?: string
  testId?: string
}

// Loading state with progress
export interface LoadingStateProps {
  title?: string
  progress?: number
  description?: string
  showPercentage?: boolean
  className?: string
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  title = 'Loading...',
  progress = 0,
  description,
  showPercentage = true,
  className = '',
}) => {
  const percentage = Math.round(progress * 100)

  return (
    <div
      className={`flex flex-col items-center justify-center p-8 text-center ${className}`}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <EmptyStateIcon variant="loading" size="lg" className="mb-4" />
      
      <h3 className="text-lg font-medium text-body mb-2">
        {title}
      </h3>

      {description && (
        <p className="text-sm text-hint mb-4">
          {description}
        </p>
      )}
      
      <div className="w-full max-w-xs">
        <ProgressBar
          value={percentage}
          showLabel={showPercentage}
          size="md"
          variant="default"
        />
      </div>
      
      <span className="sr-only">
        {percentage}% complete - {description || title}
      </span>
    </div>
  )
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon: _icon, // eslint-disable-line @typescript-eslint/no-unused-vars
  iconVariant = 'noData',
  title,
  description,
  action,
  secondaryAction,
  illustration,
  className = '',
  testId = 'empty-state',
}) => {
  return (
    <div
      className={`
        flex flex-col items-center justify-center
        p-8 text-center
        ${className}
      `}
      data-testid={testId}
      role="region"
      aria-label={title}
    >
      {/* Icon or Illustration */}
      <div className="mb-4">
        {illustration || (
          <EmptyStateIcon
            variant={iconVariant}
            size="lg"
          />
        )}
      </div>

      {/* Title */}
      <h3 className="text-lg font-medium text-body mb-2">
        {title}
      </h3>

      {/* Description */}
      <p className="text-sm text-hint max-w-sm mb-6">
        {description}
      </p>

      {/* Actions */}
      {(action || secondaryAction) && (
        <div className="flex flex-col sm:flex-row gap-3">
          {secondaryAction && (
            <Button
              variant={secondaryAction.variant || 'secondary'}
              size="md"
              onClick={secondaryAction.onClick}
              disabled={secondaryAction.disabled}
              loading={secondaryAction.loading}
            >
              {secondaryAction.label}
            </Button>
          )}
          
          {action && (
            <Button
              variant={action.variant || 'primary'}
              size="md"
              onClick={action.onClick}
              disabled={action.disabled}
              loading={action.loading}
            >
              {action.label}
            </Button>
          )}
        </div>
      )}
    </div>
  )
}

// Pre-configured empty state variants for common use cases
export const EmptyStates = {
  // Initial state - nothing here yet
  noData: (onAdd: () => void, itemName = 'item') => ({
    iconVariant: 'noData' as EmptyStateVariant,
    title: `No ${itemName}s yet`,
    description: `Get started by adding your first ${itemName.toLowerCase()}`,
    action: {
      label: `Add ${itemName}`,
      onClick: onAdd,
      variant: 'primary' as const,
    },
  }),

  // Search/filter returned no results
  noResults: (onClear: () => void, searchQuery?: string) => ({
    iconVariant: 'noResults' as EmptyStateVariant,
    title: 'No results found',
    description: searchQuery
      ? `No results for "${searchQuery}". Try a different search term.`
      : 'No items match your criteria. Try adjusting your filters.',
    action: {
      label: 'Clear Filters',
      onClick: onClear,
      variant: 'secondary' as const,
    },
  }),

  // Feature requires configuration
  featureDisabled: (onConfigure: () => void, featureName = 'This feature') => ({
    iconVariant: 'featureDisabled' as EmptyStateVariant,
    title: `${featureName} Not Configured`,
    description: `${featureName} requires setup before you can use it. Configure it now to get started.`,
    action: {
      label: 'Configure Now',
      onClick: onConfigure,
      variant: 'primary' as const,
    },
  }),

  // Error state
  error: (onRetry: () => void, onReport?: () => void, errorMessage?: string) => ({
    iconVariant: 'error' as EmptyStateVariant,
    title: 'Something went wrong',
    description: errorMessage || 'An error occurred while loading data. Please try again.',
    action: {
      label: 'Retry',
      onClick: onRetry,
      variant: 'primary' as const,
    },
    secondaryAction: onReport
      ? {
          label: 'Report Issue',
          onClick: onReport,
          variant: 'ghost' as const,
        }
      : undefined,
  }),

  // Loading state
  loading: (title = 'Loading...', progress?: number, description?: string) => ({
    iconVariant: 'loading' as EmptyStateVariant,
    title,
    description,
    progress,
  }),

  // Dashboard section empty
  dashboardEmpty: (onAction: () => void, sectionName: string, actionLabel: string) => ({
    iconVariant: 'noData' as EmptyStateVariant,
    title: `No ${sectionName} yet`,
    description: `Add ${sectionName.toLowerCase()} to see them here`,
    action: {
      label: actionLabel,
      onClick: onAction,
      variant: 'secondary' as const,
    },
  }),

  // No files found
  noFiles: (onConfigure: () => void) => ({
    iconVariant: 'noData' as EmptyStateVariant,
    title: 'No files found',
    description: 'Configure your file paths and monitoring settings to discover media files',
    action: {
      label: 'Configure File Monitoring',
      onClick: onConfigure,
      variant: 'primary' as const,
    },
  }),
}

export default EmptyState
