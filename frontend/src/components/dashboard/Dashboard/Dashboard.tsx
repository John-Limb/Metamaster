import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { StatCard } from '../StatCard'
import { LibraryStats } from '../LibraryStats'
import { RecentActivity, type Activity } from '../RecentActivity'
import { QuickActions, type QuickAction } from '../QuickActions'
import { StorageChart } from '../StorageChart'
import { Card } from '@/components/common/Card'
import { Button } from '@/components/common/Button'
import { Skeleton, SkeletonCard } from '@/components/common/Skeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { healthService } from '@/services/healthService'
import { movieService } from '@/services/movieService'
import { tvShowService } from '@/services/tvShowService'
import { queueService } from '@/services/queueService'
import { fileService } from '@/services/fileService'
import { configurationService, type ConfigurationState, type ConfigurationItem } from '@/services/configurationService'
import { type EnrichmentStats } from '@/services/movieService'
import { storageService, type StorageSummary } from '@/services/storageService'

const API_STATUS_IDS = ['api-keys-tmdb-token', 'api-keys-tmdb-key']

function ExternalApiStatus({ items }: { items: ConfigurationItem[] }) {
  const apiItems = items.filter(i => API_STATUS_IDS.includes(i.id))
  const allValid = apiItems.length > 0 && apiItems.every(i => i.status === 'valid')
  const hasInvalid = apiItems.some(i => i.status === 'invalid')

  const labels: Record<string, string> = {
    'api-keys-tmdb-token': 'TMDB Access Token',
    'api-keys-tmdb-key': 'TMDB API Key',
  }

  return (
    <Card variant="elevated" className="flex flex-col gap-3">
      <h3 className="text-base font-semibold text-slate-900 dark:text-white">External APIs</h3>

      {apiItems.length === 0 ? (
        <p className="text-sm text-slate-400 dark:text-slate-500">Checking…</p>
      ) : (
        <div className="space-y-2">
          {apiItems.map(item => (
            <div key={item.id} className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full flex-shrink-0 ${
                  item.status === 'valid'
                    ? 'bg-emerald-500'
                    : item.status === 'invalid'
                    ? 'bg-red-500'
                    : 'bg-amber-400 animate-pulse'
                }`}
              />
              <span className="text-sm text-slate-700 dark:text-slate-300 flex-1">
                {labels[item.id] ?? item.name}
              </span>
              <span className={`text-xs font-medium ${
                item.status === 'valid'
                  ? 'text-emerald-600 dark:text-emerald-400'
                  : item.status === 'invalid'
                  ? 'text-red-600 dark:text-red-400'
                  : 'text-amber-600 dark:text-amber-400'
              }`}>
                {item.status === 'valid' ? 'Connected' : item.status === 'invalid' ? 'Missing' : 'Checking'}
              </span>
            </div>
          ))}
        </div>
      )}

      {allValid && (
        <p className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
          All external APIs connected
        </p>
      )}
      {hasInvalid && (
        <p className="text-xs text-red-500 dark:text-red-400">
          Missing API keys will prevent metadata enrichment.
        </p>
      )}
    </Card>
  )
}

export interface DashboardProps {
  className?: string
}

interface DashboardStats {
  totalFiles: number
  indexedFiles: number
  pendingTasks: number
  completedTasks: number
}

interface LibraryData {
  totalMovies: number
  totalTVShows: number
  totalEpisodes: number
  totalFiles: number
  totalSize: number
  lastUpdated: string
}

export function Dashboard({ className = '' }: DashboardProps) {
  const navigate = useNavigate()
  const [isLoading, setIsLoading] = useState(true)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [configStatus, setConfigStatus] = useState<{
    isConfigured: boolean
    pathsConfigured: number
  }>({ isConfigured: false, pathsConfigured: 0 })
  const [showConfigHelp, setShowConfigHelp] = useState(false)

  const [stats, setStats] = useState<DashboardStats>({
    totalFiles: 0,
    indexedFiles: 0,
    pendingTasks: 0,
    completedTasks: 0,
  })

  const [libraryData, setLibraryData] = useState<LibraryData>({
    totalMovies: 0,
    totalTVShows: 0,
    totalEpisodes: 0,
    totalFiles: 0,
    totalSize: 0,
    lastUpdated: new Date().toISOString(),
  })

  const [enrichmentStats, setEnrichmentStats] = useState<EnrichmentStats | null>(null)
  const [recentActivities, setRecentActivities] = useState<Activity[]>([])
  const [storageSummary, setStorageSummary] = useState<StorageSummary | null>(null)
  const [configItems, setConfigItems] = useState<ConfigurationItem[]>([])

  const loadDashboardData = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Check configuration status
      const config: ConfigurationState = await configurationService.checkAll()
      const criticalItems = config.items.filter(item => item.severity === 'critical' && item.status !== 'valid')
      setConfigStatus({
        isConfigured: criticalItems.length === 0,
        pathsConfigured: config.items.length > 0 ? config.items.filter(i => i.status === 'valid').length : 0,
      })
      setConfigItems(config.items)

      // Only load data if configured
      if (!config.isComplete) {
        setIsLoading(false)
        return
      }

      // Fetch all data in parallel — use allSettled so one failure doesn't wipe the rest
      const results = await Promise.allSettled([
        healthService.getDetailedHealth(),
        movieService.getMovies(1, 50),
        tvShowService.getTVShows(1, 50),
        queueService.getStats(),
        fileService.getFileStats(),
        movieService.getEnrichmentStats(),
        storageService.getSummary(),
      ])
      const health = results[0].status === 'fulfilled' ? results[0].value : { status: 'unknown', timestamp: new Date().toISOString() }
      const movieResponse = results[1].status === 'fulfilled' ? results[1].value : { total: 0, items: [] }
      const tvResponse = results[2].status === 'fulfilled' ? results[2].value : { total: 0, items: [] }
      const queueStats = results[3].status === 'fulfilled' ? results[3].value : { pendingTasks: 0, completedTasks: 0, processingTasks: 0 }
      const fileStats = results[4].status === 'fulfilled' ? results[4].value : null
      const enrichStats = results[5].status === 'fulfilled' ? results[5].value as EnrichmentStats : null
      const storageSummaryResult = results[6]
      setEnrichmentStats(enrichStats)
      setStorageSummary(storageSummaryResult.status === 'fulfilled' ? storageSummaryResult.value as StorageSummary : null)

      const totalMovies = fileStats?.movieCount ?? movieResponse?.total ?? 0
      const totalTVShows = fileStats?.tvShowCount ?? tvResponse?.total ?? 0
      const totalEpisodes = (tvResponse?.items || []).reduce(
        (acc: number, show: { episodes?: number }) => acc + (show.episodes || 0),
        0
      )
      const totalFiles = fileStats?.totalFiles ?? (totalMovies + totalTVShows)
      const totalSize = fileStats?.totalSize ?? 0

      setStats({
        totalFiles,
        indexedFiles: totalMovies,
        pendingTasks: queueStats?.pendingTasks || 0,
        completedTasks: queueStats?.completedTasks || 0,
      })

      setLibraryData({
        totalMovies,
        totalTVShows,
        totalEpisodes,
        totalFiles,
        totalSize,
        lastUpdated: fileStats?.lastUpdated ?? new Date().toISOString(),
      })

      // Build activities from health and queue
      const activities: Activity[] = []

      if (health?.status) {
        activities.push({
          id: 'health',
          type: 'update',
          title: 'Health Check',
          description: `Overall status: ${health.status}`,
          timestamp: health.timestamp || new Date().toISOString(),
          status: health.status === 'healthy' ? 'success' : 'error',
          onClick: () => navigate('/system-health'),
        })
      }

      if (queueStats?.processingTasks !== undefined) {
        activities.push({
          id: 'queue',
          type: 'sync',
          title: 'Queue Snapshot',
          description: `${queueStats.processingTasks} processing / ${queueStats.pendingTasks} pending`,
          timestamp: new Date().toISOString(),
          status: queueStats.pendingTasks > 0 ? 'pending' : 'success',
        })
      }

      if (totalMovies > 0) {
        activities.push({
          id: 'movies',
          type: 'add',
          title: 'Library Update',
          description: `${totalMovies} movies indexed`,
          timestamp: new Date().toISOString(),
          status: 'success',
        })
      }

      setRecentActivities(activities)

    } catch (err) {
      console.error('Dashboard: Error loading data', err)
      setError('Failed to load dashboard data. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await loadDashboardData()
    setIsRefreshing(false)
  }

  useEffect(() => {
    loadDashboardData()
  }, [loadDashboardData])

  // Quick actions configuration
  const quickActions: QuickAction[] = [
    {
      id: 'scan',
      label: 'Scan Library',
      description: 'Scan for new files',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      ),
      onClick: () => {
        console.log('Scan library action triggered')
        handleRefresh()
      },
      group: 'scan',
      variant: 'primary',
    },
    {
      id: 'sync',
      label: 'Sync Metadata',
      description: 'Update all metadata',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      ),
      onClick: () => {
        console.log('Sync metadata action triggered')
        handleRefresh()
      },
      group: 'scan',
    },
    {
      id: 'add',
      label: 'Add Files',
      description: 'Add new content',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
      ),
      onClick: () => console.log('Add files action triggered'),
      group: 'add',
      variant: 'primary',
    },
    {
      id: 'organisation',
      label: 'Organise Files',
      description: 'Rename & organise',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
      ),
      onClick: () => navigate('/organisation'),
      group: 'settings',
    },
  ]

  // Loading state
  if (isLoading) {
    return (
      <div className={`space-y-6 ${className}`} role="main" aria-label="Dashboard">
        {/* Header skeleton */}
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-8 w-48 mb-2" />
            <Skeleton className="h-5 w-72" />
          </div>
          <Skeleton className="h-10 w-32" />
        </div>

        {/* Quick Actions skeleton */}
        <SkeletonCard className="p-6">
          <Skeleton className="h-6 w-36 mb-4" />
          <div className="flex gap-6 overflow-hidden">
            <div className="flex gap-3">
              {[...Array(4)].map((_, i) => (
                <Skeleton key={i} className="h-24 w-28 rounded-xl" />
              ))}
            </div>
          </div>
        </SkeletonCard>

        {/* Stat Cards skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <SkeletonCard key={i} className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <Skeleton className="h-4 w-24 mb-3" />
                  <Skeleton className="h-8 w-16 mb-3" />
                  <Skeleton className="h-5 w-20" />
                </div>
                <Skeleton className="h-12 w-12 rounded-lg" />
              </div>
            </SkeletonCard>
          ))}
        </div>

        {/* Library Stats skeleton */}
        <SkeletonCard className="p-6">
          <Skeleton className="h-6 w-40 mb-6" />
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} className="h-28 rounded-xl" />
            ))}
          </div>
        </SkeletonCard>

        {/* Storage and Activity skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SkeletonCard className="p-6">
            <Skeleton className="h-6 w-36 mb-6" />
            <div className="flex items-center gap-6">
              <Skeleton className="h-48 w-48 rounded-full" />
              <div className="flex-1 space-y-3">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-12 rounded-lg" />
                ))}
              </div>
            </div>
          </SkeletonCard>
          <SkeletonCard className="p-6">
            <Skeleton className="h-6 w-36 mb-6" />
            <div className="space-y-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="flex gap-4">
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <div className="flex-1">
                    <Skeleton className="h-5 w-32 mb-2" />
                    <Skeleton className="h-4 w-48" />
                  </div>
                </div>
              ))}
            </div>
          </SkeletonCard>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className={`space-y-6 ${className}`} role="main" aria-label="Dashboard">
        <EmptyState
          iconVariant="error"
          title="Failed to load dashboard"
          description={error}
          action={{
            label: 'Retry',
            onClick: handleRefresh,
            variant: 'primary',
          }}
        />
      </div>
    )
  }

  // Not configured state
  if (!configStatus.isConfigured) {
    return (
      <div className={`space-y-6 ${className}`} role="main" aria-label="Dashboard">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              Dashboard
            </h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">
              Welcome back! Here's an overview of your library.
            </p>
          </div>
          <Button variant="outline" onClick={handleRefresh} loading={isRefreshing}>
            Refresh
          </Button>
        </div>

        <EmptyState
          iconVariant="featureDisabled"
          title="Library not configured"
          description="Add your media library paths to your docker .env file to start tracking your collection and viewing dashboard analytics."
          action={{
            label: 'Configure Library',
            onClick: () => setShowConfigHelp(true),
            variant: 'primary',
          }}
        />

        {/* Configuration Help Modal */}
        <ConfirmDialog
          isOpen={showConfigHelp}
          title="Configure Your Library"
          message="Please configure your library in the docker .env file. Add your MOVIE_DIR and TV_DIR paths to enable the dashboard features."
          confirmText="Got it"
          cancelText=""
          onConfirm={() => setShowConfigHelp(false)}
          onCancel={() => setShowConfigHelp(false)}
        />
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`} role="main" aria-label="Dashboard">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Dashboard
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Welcome back! Here's an overview of your library.
          </p>
        </div>
        <Button variant="outline" onClick={handleRefresh} loading={isRefreshing}>
          Refresh
        </Button>
      </div>

      {/* Quick Actions + External API Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2">
          <QuickActions actions={quickActions} />
        </div>
        <ExternalApiStatus items={configItems} />
      </div>

      {/* Stat Cards - Responsive grid: 1 col mobile, 2 cols tablet, 4 cols desktop */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Files"
          value={stats.totalFiles.toLocaleString()}
          variant="primary"
          onClick={() => navigate('/files')}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          }
        />
        <StatCard
          title="Indexed Files"
          value={enrichmentStats?.total ?? stats.indexedFiles}
          variant="success"
          onClick={() => navigate('/enrichment')}
          breakdown={enrichmentStats ? [
            { label: 'Indexed', value: enrichmentStats.indexed, color: 'success' },
            { label: 'Pending', value: enrichmentStats.pending, color: 'warning' },
            { label: 'Failed', value: enrichmentStats.failed, color: 'danger' },
          ] : undefined}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatCard
          title="Pending Tasks"
          value={stats.pendingTasks}
          variant="warning"
          onClick={() => navigate('/queue')}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatCard
          title="Completed Tasks"
          value={stats.completedTasks}
          variant="default"
          onClick={() => navigate('/queue')}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
            </svg>
          }
        />
      </div>

      {/* Library Stats */}
      <LibraryStats
        stats={libraryData}
        onMovieClick={() => window.location.assign('/movies')}
        onTVClick={() => window.location.assign('/tv-shows')}
      />

      {/* Storage Chart and Recent Activity - 2 column grid on desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {storageSummary ? (
          <div
            className="cursor-pointer"
            onClick={() => navigate('/storage')}
            role="link"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && navigate('/storage')}
          >
            <StorageChart
              data={[
                { label: 'Movies', value: storageSummary.library.movies_bytes, color: '#6366f1' },
                { label: 'TV Shows', value: storageSummary.library.tv_bytes, color: '#8b5cf6' },
              ]}
              total={storageSummary.library.movies_bytes + storageSummary.library.tv_bytes}
              diskUsedBytes={storageSummary.disk.used_bytes}
              diskTotalBytes={storageSummary.disk.total_bytes}
            />
          </div>
        ) : (
          <Card variant="elevated">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Storage Usage
            </h3>
            <div className="text-center py-12">
              <div className="mx-auto w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
              </div>
              <h4 className="text-base font-medium text-slate-900 dark:text-white mb-2">
                Storage analytics loading…
              </h4>
            </div>
          </Card>
        )}
        <RecentActivity
          activities={recentActivities}
        />
      </div>
    </div>
  )
}

export default Dashboard
