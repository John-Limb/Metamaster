import React, { useEffect, useCallback, useMemo } from 'react'
import { useQueueStore } from '@/stores/queueStore'
import { QueueStats } from './QueueStats'
import { QueueItem } from './QueueItem'
import { LoadingSpinner } from '@/components/common'

interface QueuePanelProps {
  className?: string
  autoRefresh?: boolean
  refreshInterval?: number
}

export function QueuePanel({
  className = '',
  autoRefresh = true,
  refreshInterval = 5000,
}: QueuePanelProps) {
  const {
    tasks,
    stats,
    isLoading,
    error,
    statusFilter,
    pollingEnabled,
    pollingInterval,
    fetchTasks,
    fetchStats,
    setStatusFilter,
    setPollingEnabled,
    clearCompletedTasks,
  } = useQueueStore()

  // Fetch initial data
  useEffect(() => {
    fetchTasks()
    fetchStats()
  }, [fetchTasks, fetchStats])

  // Set up polling for real-time updates
  useEffect(() => {
    if (!pollingEnabled || !autoRefresh) return

    const pollInterval = setInterval(() => {
      fetchTasks()
      fetchStats()
    }, pollingInterval)

    return () => clearInterval(pollInterval)
  }, [pollingEnabled, autoRefresh, pollingInterval, fetchTasks, fetchStats])

  const handleRetryTask = useCallback((taskId: string) => {
    console.log('Retrying task:', taskId)
  }, [])

  const handleCancelTask = useCallback((taskId: string) => {
    console.log('Cancelling task:', taskId)
  }, [])

  const handleViewDetails = useCallback((taskId: string) => {
    console.log('Viewing details for task:', taskId)
  }, [])

  const handleClearCompleted = useCallback(async () => {
    await clearCompletedTasks()
  }, [clearCompletedTasks])

  const filteredTasks = useMemo(() => {
    if (!statusFilter) return tasks
    return tasks.filter((task) => task.status === statusFilter)
  }, [tasks, statusFilter])

  const statusFilters = [
    { value: null, label: 'All Tasks' },
    { value: 'pending', label: 'Pending' },
    { value: 'processing', label: 'Processing' },
    { value: 'completed', label: 'Completed' },
    { value: 'failed', label: 'Failed' },
  ]

  return (
    <div className={`space-y-4 ${className}`} role="region" aria-label="Task Queue Panel">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Task Queue</h2>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={pollingEnabled}
              onChange={(e) => setPollingEnabled(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            Auto-refresh
          </label>
        </div>
      </div>

      {/* Stats */}
      <QueueStats />

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm text-gray-600">Filter by status:</span>
        {statusFilters.map((filter) => (
          <button
            key={filter.label}
            onClick={() => setStatusFilter(filter.value)}
            className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
              statusFilter === filter.value
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
            aria-pressed={statusFilter === filter.value}
          >
            {filter.label}
          </button>
        ))}
        {tasks.some((t) => t.status === 'completed') && (
          <button
            onClick={handleClearCompleted}
            className="ml-auto px-3 py-1.5 border border-gray-300 rounded-full text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Clear Completed
          </button>
        )}
      </div>

      {/* Error State */}
      {error && (
        <div
          className="bg-red-50 border border-red-200 rounded-lg p-4"
          role="alert"
        >
          <div className="flex">
            <svg
              className="h-5 w-5 text-red-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Task List */}
      <div
        className="bg-white rounded-lg border border-gray-200 overflow-hidden"
        role="list"
        aria-label="Tasks"
      >
        {isLoading && tasks.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" message="Loading tasks..." />
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="text-center py-12">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No tasks</h3>
            <p className="mt-1 text-sm text-gray-500">
              {statusFilter
                ? `No ${statusFilter} tasks found.`
                : 'No tasks in the queue.'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredTasks.map((task) => (
              <QueueItem
                key={task.id}
                task={task}
                onRetry={handleRetryTask}
                onCancel={handleCancelTask}
                onViewDetails={handleViewDetails}
              />
            ))}
          </div>
        )}
      </div>

      {/* Task Count */}
      {tasks.length > 0 && (
        <p className="text-sm text-gray-500 text-right">
          Showing {filteredTasks.length} of {tasks.length} tasks
        </p>
      )}
    </div>
  )
}

export default QueuePanel
