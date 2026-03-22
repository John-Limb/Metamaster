import React from 'react'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { Skeleton, SkeletonText } from '@/components/common/Skeleton'

export interface StatCardBreakdownItem {
  label: string
  value: number
  color: 'success' | 'warning' | 'danger'
}

export interface StatCardProps {
  title: string
  value: string | number
  change?: {
    value: number
    label: string // e.g., "vs last month"
  }
  breakdown?: StatCardBreakdownItem[]
  icon?: React.ReactNode
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger'
  loading?: boolean
  className?: string
  onClick?: () => void
}

const VARIANT_STYLES = {
  default: {
    iconBg: 'bg-slate-100 dark:bg-slate-800',
    iconColor: 'text-dim',
    badge: 'primary' as const,
  },
  primary: {
    iconBg: 'bg-primary-100 dark:bg-primary-900/50',
    iconColor: 'text-primary-600 dark:text-primary-400',
    badge: 'primary' as const,
  },
  success: {
    iconBg: 'bg-emerald-100 dark:bg-emerald-900/50',
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    badge: 'success' as const,
  },
  warning: {
    iconBg: 'bg-amber-100 dark:bg-amber-900/50',
    iconColor: 'text-amber-600 dark:text-amber-400',
    badge: 'warning' as const,
  },
  danger: {
    iconBg: 'bg-red-100 dark:bg-red-900/50',
    iconColor: 'text-red-600 dark:text-red-400',
    badge: 'danger' as const,
  },
}

const TREND_ICONS = {
  up: (
    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
    </svg>
  ),
  down: (
    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
    </svg>
  ),
  neutral: (
    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
    </svg>
  ),
}

const getTrendDirection = (value: number): 'up' | 'down' | 'neutral' => {
  if (value > 0) return 'up'
  if (value < 0) return 'down'
  return 'neutral'
}

const BREAKDOWN_COLOR_CLASSES = {
  success: 'text-emerald-600 dark:text-emerald-400',
  warning: 'text-amber-600 dark:text-amber-400',
  danger: 'text-red-600 dark:text-red-400',
}

export function StatCard({
  title,
  value,
  change,
  breakdown,
  icon,
  variant = 'default',
  loading = false,
  className = '',
  onClick,
}: StatCardProps) {
  const styles = VARIANT_STYLES[variant]

  const formatChange = (val: number) => {
    const prefix = val >= 0 ? '+' : ''
    return `${prefix}${val}%`
  }

  if (loading) {
    return (
      <Card
        variant="elevated"
        className={`transition-all duration-200 hover:shadow-lg ${className}`}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <Skeleton className="h-4 w-24 mb-3" />
            <Skeleton className="h-8 w-16 mb-3" />
            {change && (
              <SkeletonText className="h-5 w-20" />
            )}
          </div>
          <Skeleton className="h-12 w-12 rounded-lg" />
        </div>
      </Card>
    )
  }

  return (
    <Card
      variant="elevated"
      onClick={onClick}
      className={`
        transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
      role="region"
      aria-label={`${title}: ${value}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-dim">
            {title}
          </p>
          <p className="mt-2 text-3xl font-bold text-body">
            {value}
          </p>
          {change && (
            <div className="mt-2 flex items-center gap-2">
              <Badge variant={styles.badge} size="sm">
                <span className="flex items-center gap-0.5">
                  {TREND_ICONS[getTrendDirection(change.value)]}
                  {formatChange(change.value)}
                </span>
              </Badge>
              <span className="text-xs text-hint">
                {change.label}
              </span>
            </div>
          )}
          {breakdown && breakdown.length > 0 && (
            <div className="mt-3 flex items-center gap-3">
              {breakdown.map((item) => (
                <div key={item.label} className="flex items-center gap-1">
                  <span className={`text-sm font-semibold ${BREAKDOWN_COLOR_CLASSES[item.color]}`}>
                    {item.value}
                  </span>
                  <span className="text-xs text-hint">
                    {item.label}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
        {icon && (
          <div
            className={`
              p-3 rounded-xl ${styles.iconBg} ${styles.iconColor}
              transition-transform duration-200 hover:scale-110
            `}
            aria-hidden="true"
          >
            {icon}
          </div>
        )}
      </div>
    </Card>
  )
}

export default StatCard
