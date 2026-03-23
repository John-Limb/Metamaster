import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  AlertTriangle, 
  AlertCircle, 
  Info, 
  ChevronUp, 
  ChevronDown, 
  X, 
  CheckCircle2,
  RefreshCw 
} from 'lucide-react'
import { Button } from '@/components/common/Button'
import { useConfiguration, useIncompleteConfiguration } from '@/context/ConfigurationContext'
import { cn } from '@/utils/cn'
import type { ConfigurationItem } from '@/services/configurationService'

export interface ConfigurationStatusBarProps {
  onConfigure?: () => void
  autoHide?: boolean
  className?: string
}

// Severity styling
const severityConfig = {
  critical: {
    icon: AlertCircle,
    iconColor: 'text-red-500',
    bgColor: 'bg-red-50 dark:bg-red-900/20',
    borderColor: 'border-red-200 dark:border-red-800',
    badgeColor: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    textColor: 'text-red-800 dark:text-red-200',
  },
  important: {
    icon: AlertTriangle,
    iconColor: 'text-amber-500',
    bgColor: 'bg-amber-50 dark:bg-amber-900/20',
    borderColor: 'border-amber-200 dark:border-amber-800',
    badgeColor: 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200',
    textColor: 'text-amber-800 dark:text-amber-200',
  },
  optional: {
    icon: Info,
    iconColor: 'text-blue-500',
    bgColor: 'bg-blue-50 dark:bg-blue-900/20',
    borderColor: 'border-blue-200 dark:border-blue-800',
    badgeColor: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    textColor: 'text-blue-800 dark:text-blue-200',
  },
}

const COMPLETED_KEY = 'metamaster_config_completed'

// Check if previously completed and should auto-hide
const wasPreviouslyCompleted = (): boolean => {
  if (typeof window === 'undefined') return false
  return localStorage.getItem(COMPLETED_KEY) === 'true'
}

// Mark as completed
const markAsCompleted = (): void => {
  if (typeof window === 'undefined') return
  localStorage.setItem(COMPLETED_KEY, 'true')
}

// Reset completion flag
const resetCompletion = (): void => {
  if (typeof window === 'undefined') return
  localStorage.removeItem(COMPLETED_KEY)
}

export const ConfigurationStatusBar: React.FC<ConfigurationStatusBarProps> = ({
  onConfigure,
  autoHide = true,
  className = '',
}) => {
  const navigate = useNavigate()
  const { state, isLoading, refresh, dismissItem } = useConfiguration()
  const { criticalCount, importantCount, optionalCount, totalCount } = useIncompleteConfiguration()
  
  const [isExpanded, setIsExpanded] = useState(false)
  const [shouldShow, setShouldShow] = useState(false)

  // Determine if we should show the status bar
  useEffect(() => {
    const hasIncompleteItems = totalCount > 0
    const previouslyCompleted = wasPreviouslyCompleted()

    // Show if has incomplete items OR if was not previously completed (first load)
    if (hasIncompleteItems) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setShouldShow(true)
      resetCompletion() // Reset completion flag since there are incomplete items
    } else if (!previouslyCompleted && !hasIncompleteItems) {
      // No incomplete items and first load - check if we should show briefly
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setShouldShow(true)
      // Auto-hide after 3 seconds if no items
      const timer = setTimeout(() => {
        setShouldShow(false)
        markAsCompleted()
      }, 3000)
      return () => clearTimeout(timer)
    } else if (autoHide && previouslyCompleted) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setShouldShow(false)
    } else {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setShouldShow(true)
    }
  }, [totalCount, autoHide])

  // Handle configuration action
  const handleConfigure = useCallback(() => {
    if (onConfigure) {
      onConfigure()
    } else {
      navigate('/settings')
    }
  }, [onConfigure, navigate])

  // Handle individual item action
  const handleItemAction = (item: ConfigurationItem) => {
    if (item.actionPath) {
      navigate(item.actionPath)
    }
  }

  // Handle dismiss
  const handleDismiss = (id: string) => {
    dismissItem(id)
  }

  // Handle refresh
  const handleRefresh = async () => {
    await refresh()
  }

  // Group items by severity
  const criticalItems = state.items.filter(i => i.severity === 'critical' && i.status !== 'valid')
  const importantItems = state.items.filter(i => i.severity === 'important' && i.status !== 'valid')
  const optionalItems = state.items.filter(i => i.severity === 'optional' && i.status !== 'valid')

  // Generate summary text
  const getSummaryText = () => {
    if (isLoading) {
      return 'Checking configuration...'
    }
    
    const parts: string[] = []
    if (criticalCount > 0) parts.push(`${criticalCount} critical`)
    if (importantCount > 0) parts.push(`${importantCount} important`)
    if (optionalCount > 0 && parts.length === 0) parts.push(`${optionalCount} optional`)
    
    if (parts.length === 0) return 'All configurations complete!'
    
    return `${parts.join(' + ')} item${parts.length > 1 ? 's' : ''} need${parts.length === 1 ? 's' : ''} attention`
  }

  // Don't render if we shouldn't show
  if (!shouldShow) {
    return null
  }

  // All complete - show success state briefly
  if (totalCount === 0 && !isLoading) {
    return (
      <div
        className={cn(
          'fixed top-16 left-0 right-0 z-50',
          'bg-green-50 dark:bg-green-900/20',
          'border-b border-green-200 dark:border-green-800',
          'transition-all duration-300 ease-in-out',
          'flex items-center justify-center py-2',
          className
        )}
        role="status"
        aria-live="polite"
      >
        <CheckCircle2 className="w-4 h-4 text-green-500 mr-2" />
        <span className="text-sm text-green-700 dark:text-green-300 font-medium">
          All configurations complete!
        </span>
      </div>
    )
  }

  return (
    <div
      className={cn(
        'fixed top-16 left-0 right-0 z-50',
        'bg-card',
        'border-b border-edge',
        'shadow-sm',
        'transition-all duration-300 ease-in-out',
        className
      )}
      role="banner"
      aria-live="polite"
    >
      {/* Collapsed state */}
      <div
        className={cn(
          'flex items-center justify-between px-4 py-2',
          'max-w-7xl mx-auto',
          isExpanded && 'border-b border-edge'
        )}
      >
        <div className="flex items-center gap-3">
          {/* Status indicator */}
          {isLoading ? (
            <RefreshCw className="w-4 h-4 text-hint animate-spin" />
          ) : criticalCount > 0 ? (
            <AlertCircle className="w-4 h-4 text-red-500" />
          ) : importantCount > 0 ? (
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          ) : (
            <Info className="w-4 h-4 text-blue-500" />
          )}
          
          {/* Summary text */}
          <span className="text-sm text-dim">
            <span className="font-medium">
              {totalCount} item{totalCount !== 1 ? 's' : ''} need{totalCount === 1 ? 's' : ''} attention
            </span>
            {' - '}
            {getSummaryText()}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Refresh button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleRefresh}
            loading={isLoading}
            aria-label="Refresh configuration status"
          >
            <RefreshCw className={cn('w-4 h-4', isLoading && 'animate-spin')} />
          </Button>

          {/* Expand/Collapse button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            aria-label={isExpanded ? 'Collapse configuration details' : 'Expand configuration details'}
            aria-expanded={isExpanded}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </Button>

          {/* Configure button */}
          <Button
            variant="primary"
            size="sm"
            onClick={handleConfigure}
          >
            Configure All
          </Button>

          {/* Dismiss button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShouldShow(false)}
            aria-label="Dismiss configuration status bar"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Expanded state - Detailed list */}
      {isExpanded && (
        <div
          className={cn(
            'px-4 py-4',
            'max-w-7xl mx-auto',
            'bg-subtle'
          )}
          role="region"
          aria-label="Configuration details"
        >
          {/* Critical items */}
          {criticalItems.length > 0 && (
            <div className="mb-4">
              <h4 className="text-xs font-semibold text-red-600 dark:text-red-400 uppercase tracking-wide mb-2">
                Critical ({criticalItems.length})
              </h4>
              <div className="space-y-2">
                {criticalItems.map(item => (
                  <ConfigurationItemRow
                    key={item.id}
                    item={item}
                    onAction={() => handleItemAction(item)}
                    onDismiss={() => handleDismiss(item.id)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Important items */}
          {importantItems.length > 0 && (
            <div className="mb-4">
              <h4 className="text-xs font-semibold text-amber-600 dark:text-amber-400 uppercase tracking-wide mb-2">
                Important ({importantItems.length})
              </h4>
              <div className="space-y-2">
                {importantItems.map(item => (
                  <ConfigurationItemRow
                    key={item.id}
                    item={item}
                    onAction={() => handleItemAction(item)}
                    onDismiss={() => handleDismiss(item.id)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Optional items */}
          {optionalItems.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-blue-600 dark:text-blue-400 uppercase tracking-wide mb-2">
                Optional ({optionalItems.length})
              </h4>
              <div className="space-y-2">
                {optionalItems.map(item => (
                  <ConfigurationItemRow
                    key={item.id}
                    item={item}
                    onAction={() => handleItemAction(item)}
                    onDismiss={() => handleDismiss(item.id)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Individual configuration item row
interface ConfigurationItemRowProps {
  item: ConfigurationItem
  onAction: () => void
  onDismiss: () => void
}

const ConfigurationItemRow: React.FC<ConfigurationItemRowProps> = ({
  item,
  onAction,
  onDismiss,
}) => {
  const config = severityConfig[item.severity]
  const Icon = config.icon

  return (
    <div
      className={cn(
        'flex items-center justify-between gap-4 p-3 rounded-lg',
        config.bgColor,
        'border',
        config.borderColor
      )}
    >
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <Icon className={cn('w-5 h-5 flex-shrink-0', config.iconColor)} />
        
        <div className="flex-1 min-w-0">
          <p className={cn('text-sm font-medium', config.textColor)}>
            {item.name}
          </p>
          <p className="text-xs text-hint truncate">
            {item.description}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 flex-shrink-0">
        {item.status === 'checking' ? (
          <span className="text-xs text-hint animate-pulse">
            Checking...
          </span>
        ) : (
          <>
            {item.actionLabel && (
              <Button
                variant="outline"
                size="sm"
                onClick={onAction}
                className={cn(
                  'text-xs',
                  'border-edge',
                  'hover:bg-subtle'
                )}
              >
                {item.actionLabel}
              </Button>
            )}
            
            <Button
              variant="ghost"
              size="sm"
              onClick={onDismiss}
              className="text-xs text-hint hover:text-dim"
            >
              Dismiss
            </Button>
          </>
        )}
      </div>
    </div>
  )
}

// Skeleton for loading state
export const ConfigurationStatusBarSkeleton: React.FC = () => {
  return (
    <div className="fixed top-16 left-0 right-0 z-50 bg-card border-b border-edge">
      <div className="flex items-center justify-between px-4 py-3 max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 bg-subtle rounded animate-pulse" />
          <div className="h-4 w-48 bg-subtle rounded animate-pulse" />
        </div>
        <div className="flex items-center gap-2">
          <div className="w-16 h-8 bg-subtle rounded animate-pulse" />
          <div className="w-8 h-8 bg-subtle rounded animate-pulse" />
        </div>
      </div>
    </div>
  )
}

export default ConfigurationStatusBar
