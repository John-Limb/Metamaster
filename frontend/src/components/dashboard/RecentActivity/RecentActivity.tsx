import React from 'react'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { Skeleton } from '@/components/common/Skeleton'
import { formatDateTime } from '@/utils/helpers'

export interface Activity {
  id: string
  type: 'scan' | 'sync' | 'add' | 'delete' | 'update'
  title: string
  description: string
  timestamp: string
  status?: 'success' | 'pending' | 'error' | 'info'
  onClick?: () => void
}

export interface RecentActivityProps {
  activities: Activity[]
  className?: string
  onViewAll?: () => void
  loading?: boolean
}

const ACTIVITY_ICONS: Record<Activity['type'], React.ReactNode> = {
  scan: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  ),
  sync: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
  add: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
    </svg>
  ),
  delete: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
    </svg>
  ),
  update: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
    </svg>
  ),
}

const ACTIVITY_COLORS: Record<Activity['type'], { bg: string; text: string }> = {
  scan: { bg: 'bg-blue-100 dark:bg-blue-900/50', text: 'text-blue-600 dark:text-blue-400' },
  sync: { bg: 'bg-purple-100 dark:bg-purple-900/50', text: 'text-purple-600 dark:text-purple-400' },
  add: { bg: 'bg-emerald-100 dark:bg-emerald-900/50', text: 'text-emerald-600 dark:text-emerald-400' },
  delete: { bg: 'bg-red-100 dark:bg-red-900/50', text: 'text-red-600 dark:text-red-400' },
  update: { bg: 'bg-amber-100 dark:bg-amber-900/50', text: 'text-amber-600 dark:text-amber-400' },
}

const STATUS_BADGES: Record<NonNullable<Activity['status']> | 'none', { variant: 'primary' | 'success' | 'warning' | 'danger' | 'info'; label: string }> = {
  none: { variant: 'primary', label: '' },
  success: { variant: 'success', label: 'Completed' },
  pending: { variant: 'warning', label: 'Pending' },
  error: { variant: 'danger', label: 'Failed' },
  info: { variant: 'info', label: 'Info' },
}

export function RecentActivity({
  activities,
  className = '',
  onViewAll,
  loading = false,
}: RecentActivityProps) {
  if (loading) {
    return (
      <Card variant="elevated" className={className}>
        <div className="flex items-center justify-between mb-6">
          <div className="h-6 w-36 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
          <div className="h-5 w-16 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
        </div>
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="flex gap-4">
              <Skeleton className="h-10 w-10 rounded-full flex-shrink-0" />
              <div className="flex-1">
                <Skeleton className="h-5 w-32 mb-2" />
                <Skeleton className="h-4 w-48" />
              </div>
            </div>
          ))}
        </div>
      </Card>
    )
  }

  if (activities.length === 0) {
    return (
      <Card variant="elevated" className={className}>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
            Recent Activity
          </h3>
        </div>
        <div className="text-center py-12">
          <div className="mx-auto w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h4 className="text-base font-medium text-slate-900 dark:text-white mb-2">
            No recent activity
          </h4>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Activity will appear here as you use the application.
          </p>
        </div>
      </Card>
    )
  }

  return (
    <Card variant="elevated" className={className}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
          Recent Activity
        </h3>
        {onViewAll && (
          <button
            onClick={onViewAll}
            className="text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 transition-colors"
          >
            View All
          </button>
        )}
      </div>

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-[19px] top-2 bottom-2 w-0.5 bg-slate-200 dark:bg-slate-700" />

        <div className="space-y-6" role="list" aria-label="Recent activity">
          {activities.map((activity) => {
            const statusBadge = STATUS_BADGES[activity.status || 'none']
            const colors = ACTIVITY_COLORS[activity.type]

            return (
              <div
                key={activity.id}
                className={`
                  relative flex items-start gap-4
                  ${activity.onClick ? 'cursor-pointer' : ''}
                `}
                role="listitem"
                onClick={activity.onClick}
                onKeyDown={(e) => {
                  if (activity.onClick && (e.key === 'Enter' || e.key === ' ')) {
                    e.preventDefault()
                    activity.onClick()
                  }
                }}
                tabIndex={activity.onClick ? 0 : -1}
              >
                {/* Timeline dot with icon */}
                <div
                  className={`
                    relative z-10 flex items-center justify-center
                    w-10 h-10 rounded-full
                    ${colors.bg} ${colors.text}
                    transition-transform duration-200
                    ${activity.onClick ? 'hover:scale-110' : ''}
                    ring-4 ring-white dark:ring-slate-900
                  `}
                >
                  {ACTIVITY_ICONS[activity.type]}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 pt-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                      {activity.title}
                    </p>
                    {statusBadge.label && (
                      <Badge variant={statusBadge.variant} size="sm">
                        {statusBadge.label}
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">
                    {activity.description}
                  </p>
                  <time
                    className="text-xs text-slate-400 dark:text-slate-500 mt-1 block"
                    dateTime={activity.timestamp}
                  >
                    {formatDateTime(activity.timestamp)}
                  </time>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </Card>
  )
}

export default RecentActivity
