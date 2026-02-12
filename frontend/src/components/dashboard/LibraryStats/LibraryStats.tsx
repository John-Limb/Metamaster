import React from 'react'
import { Card } from '@/components/common/Card'
import { Button } from '@/components/common/Button'
import { ProgressBar } from '@/components/common/ProgressBar'
import { formatFileSize } from '@/utils/helpers'

export interface LibraryStatsProps {
  stats: {
    totalMovies: number
    totalTVShows: number
    totalEpisodes: number
    totalFiles: number
    totalSize: number
    lastUpdated: string
    storageUsed?: number
    storageTotal?: number
  }
  className?: string
  onMovieClick?: () => void
  onTVClick?: () => void
  onConfigure?: () => void
  loading?: boolean
}

interface StatItem {
  label: string
  value: number | string
  icon: React.ReactNode
  color: string
  onClick?: () => void
}

type StatConfigType = {
  movies: { icon: React.ReactNode; color: string; bg: string }
  tv: { icon: React.ReactNode; color: string; bg: string }
  episodes: { icon: React.ReactNode; color: string; bg: string }
  files: { icon: React.ReactNode; color: string; bg: string }
  storage: { icon: React.ReactNode; color: string; bg: string }
}

const STAT_CONFIG: StatConfigType & Record<string, { icon: React.ReactNode; color: string; bg: string }> = {
  movies: {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
      </svg>
    ),
    color: 'text-indigo-600 dark:text-indigo-400',
    bg: 'bg-indigo-100 dark:bg-indigo-900/50',
  },
  tv: {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
    color: 'text-purple-600 dark:text-purple-400',
    bg: 'bg-purple-100 dark:bg-purple-900/50',
  },
  episodes: {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    ),
    color: 'text-emerald-600 dark:text-emerald-400',
    bg: 'bg-emerald-100 dark:bg-emerald-900/50',
  },
  files: {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
      </svg>
    ),
    color: 'text-amber-600 dark:text-amber-400',
    bg: 'bg-amber-100 dark:bg-amber-900/50',
  },
  storage: {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
      </svg>
    ),
    color: 'text-slate-600 dark:text-slate-400',
    bg: 'bg-slate-100 dark:bg-slate-800',
  },
}

export function LibraryStats({
  stats,
  className = '',
  onMovieClick,
  onTVClick,
  onConfigure,
  loading = false,
}: LibraryStatsProps) {
  const hasData = stats.totalMovies > 0 || stats.totalTVShows > 0

  const statItems: StatItem[] = [
    {
      label: 'Movies',
      value: stats.totalMovies.toLocaleString(),
      icon: STAT_CONFIG.movies.icon,
      color: STAT_CONFIG.movies.color,
      onClick: onMovieClick,
    },
    {
      label: 'TV Shows',
      value: stats.totalTVShows.toLocaleString(),
      icon: STAT_CONFIG.tv.icon,
      color: STAT_CONFIG.tv.color,
      onClick: onTVClick,
    },
    {
      label: 'Episodes',
      value: stats.totalEpisodes.toLocaleString(),
      icon: STAT_CONFIG.episodes.icon,
      color: STAT_CONFIG.episodes.color,
    },
    {
      label: 'Total Files',
      value: stats.totalFiles.toLocaleString(),
      icon: STAT_CONFIG.files.icon,
      color: STAT_CONFIG.files.color,
    },
    {
      label: 'Storage Used',
      value: formatFileSize(stats.totalSize),
      icon: STAT_CONFIG.storage.icon,
      color: STAT_CONFIG.storage.color,
    },
  ]

  if (loading) {
    return (
      <Card variant="elevated" className={className}>
        <div className="flex items-center justify-between mb-6">
          <div className="h-6 w-40 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
          <div className="h-5 w-28 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/50">
              <div className="h-8 w-8 rounded-lg bg-slate-200 dark:bg-slate-700 mb-3 animate-pulse" />
              <div className="h-8 w-16 bg-slate-200 dark:bg-slate-700 rounded mb-1 animate-pulse" />
              <div className="h-4 w-20 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
            </div>
          ))}
        </div>
      </Card>
    )
  }

  if (!hasData) {
    return (
      <Card variant="elevated" className={className}>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
            Library Statistics
          </h3>
          <span className="text-sm text-slate-500 dark:text-slate-400">
            Not configured
          </span>
        </div>
        <div className="text-center py-12">
          <div className="mx-auto w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
            </svg>
          </div>
          <h4 className="text-base font-medium text-slate-900 dark:text-white mb-2">
            No library configured
          </h4>
          <p className="text-sm text-slate-500 dark:text-slate-400 mb-4 max-w-sm mx-auto">
            Add your media library paths to start tracking your collection.
          </p>
          {onConfigure && (
            <Button variant="primary" size="sm" onClick={onConfigure}>
              Configure Library
            </Button>
          )}
        </div>
      </Card>
    )
  }

  const storagePercentage = stats.storageTotal
    ? (stats.storageUsed || stats.totalSize) / stats.storageTotal * 100
    : 0

  return (
    <Card variant="elevated" className={className}>
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
          Library Statistics
        </h3>
        <span className="text-sm text-slate-500 dark:text-slate-400">
          Updated: {new Date(stats.lastUpdated).toLocaleDateString()}
        </span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6" role="list" aria-label="Library statistics">
        {statItems.map((item) => (
          <div
            key={item.label}
            className={`
              p-4 rounded-xl transition-all duration-200
              ${item.onClick ? 'cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50' : ''}
              bg-slate-50 dark:bg-slate-800/50
            `}
            role="listitem"
            onClick={item.onClick}
            onKeyDown={(e) => {
              if (item.onClick && (e.key === 'Enter' || e.key === ' ')) {
                e.preventDefault()
                item.onClick()
              }
            }}
            tabIndex={item.onClick ? 0 : -1}
          >
            <div className={`inline-flex p-2 rounded-lg ${STAT_CONFIG[item.label.toLowerCase().replace(' ', '')]?.bg || 'bg-slate-100 dark:bg-slate-700'} mb-3`}>
              <span className={STAT_CONFIG[item.label.toLowerCase().replace(' ', '')]?.color || 'text-slate-600'}>
                {item.icon}
              </span>
            </div>
            <p className="text-2xl font-bold text-slate-900 dark:text-white">
              {item.value}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {item.label}
            </p>
          </div>
        ))}
      </div>

      {stats.storageTotal && (
        <div className="pt-4 border-t border-slate-200 dark:border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Storage Usage
            </span>
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {formatFileSize(stats.totalSize)} / {formatFileSize(stats.storageTotal)}
            </span>
          </div>
          <ProgressBar
            value={storagePercentage}
            max={100}
            variant={storagePercentage > 90 ? 'danger' : storagePercentage > 70 ? 'warning' : 'success'}
            size="md"
            showLabel={false}
          />
        </div>
      )}
    </Card>
  )
}

export default LibraryStats
