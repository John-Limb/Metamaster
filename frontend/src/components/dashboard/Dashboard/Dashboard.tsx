import React, { useState, useEffect, useCallback } from 'react'
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
import { configurationService, type ConfigurationState } from '@/services/configurationService'

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

interface StorageData {
  label: string
  value: number
  color: string
}

export function Dashboard({ className = '' }: DashboardProps) {
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

  const [recentActivities, setRecentActivities] = useState<Activity[]>([])
  const [storageData, setStorageData] = useState<StorageData[]>([])
  const [hasStorageData, setHasStorageData] = useState(false)

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

      // Only load data if configured
      if (!config.isComplete) {
        setIsLoading(false)
        return
      }

      // Fetch all data in parallel
      const [health, movieResponse, tvResponse, queueStats] = await Promise.all([
        healthService.getDetailedHealth(),
        movieService.getMovies(1, 50),
        tvShowService.getTVShows(1, 50),
        queueService.getStats(),
      ]).catch(() => [
        { status: 'unknown', timestamp: new Date().toISOString() },
        { total: 0, items: [] },
        { total: 0, items: [] },
        { pendingTasks: 0, completedTasks: 0, processingTasks: 0 },
      ])

      const totalMovies = movieResponse?.total || 0
      const totalTVShows = tvResponse?.total || 0
      const totalEpisodes = (tvResponse?.items || []).reduce(
        (acc: number, show: any) => acc + (show.episodes || 0),
        0
      )
      const derivedTotalFiles = totalMovies + totalTVShows

      setStats({
        totalFiles: derivedTotalFiles,
        indexedFiles: totalMovies,
        pendingTasks: queueStats?.pendingTasks || 0,
        completedTasks: queueStats?.completedTasks || 0,
      })

      setLibraryData({
        totalMovies,
        totalTVShows,
        totalEpisodes,
        totalFiles: derivedTotalFiles,
        totalSize: 0, // Would come from storage API
        lastUpdated: new Date().toISOString(),
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

      // Generate storage data (would come from API in production)
      if (totalMovies > 0 || totalTVShows > 0) {
        const mockStorage: StorageData[] = [
          { label: 'Movies', value: totalMovies * 2.5 * 1024 * 1024 * 1024, color: '#6366f1' },
          { label: 'TV Shows', value: totalTVShows * 1.8 * 1024 * 1024 * 1024, color: '#8b5cf6' },
          { label: 'Other', value: 50 * 1024 * 1024 * 1024, color: '#64748b' },
        ]
        setStorageData(mockStorage)
        setHasStorageData(true)
      }
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
      id: 'settings',
      label: 'Settings',
      description: 'Configure options',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
      onClick: () => console.log('Open settings action triggered'),
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

  // Calculate total storage
  const totalStorage = storageData.reduce((acc, item) => acc + item.value, 0)

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

      {/* Quick Actions */}
      <QuickActions actions={quickActions} />

      {/* Stat Cards - Responsive grid: 1 col mobile, 2 cols tablet, 4 cols desktop */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Files"
          value={stats.totalFiles.toLocaleString()}
          change={{ value: 12, label: 'vs last month' }}
          variant="primary"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          }
        />
        <StatCard
          title="Indexed Files"
          value={stats.indexedFiles.toLocaleString()}
          change={{ value: 8, label: 'vs last month' }}
          variant="success"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatCard
          title="Pending Tasks"
          value={stats.pendingTasks}
          change={{ value: 2, label: 'vs yesterday' }}
          variant="warning"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatCard
          title="Completed Today"
          value={stats.completedTasks}
          change={{ value: 15, label: 'vs yesterday' }}
          variant="default"
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
        onMovieClick={() => window.location.href = '/movies'}
        onTVClick={() => window.location.href = '/tv-shows'}
      />

      {/* Storage Chart and Recent Activity - 2 column grid on desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {hasStorageData ? (
          <StorageChart data={storageData} total={totalStorage} />
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
                Storage analytics coming soon
              </h4>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Configure your media library to enable storage tracking.
              </p>
            </div>
          </Card>
        )}
        <RecentActivity
          activities={recentActivities}
          onViewAll={() => window.location.href = '/activity'}
        />
      </div>
    </div>
  )
}

export default Dashboard
