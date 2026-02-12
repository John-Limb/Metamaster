import React, { useState, useCallback } from 'react'
import type { QueueTask } from '@/types'
import { useQueueStore } from '@/stores/queueStore'
import { TaskProgress } from './TaskProgress'
import { ConfirmDialog } from '@/components/common'

interface QueueItemProps {
  task: QueueTask
  onRetry?: (taskId: string) => void
  onCancel?: (taskId: string) => void
  onViewDetails?: (taskId: string) => void
}

const TASK_TYPE_LABELS: Record<QueueTask['type'], string> = {
  analyze: 'Analyze',
  sync: 'Sync',
  index: 'Index',
  process: 'Process',
}

const STATUS_ICONS: Record<QueueTask['status'], React.ReactNode> = {
  pending: (
    <svg className="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  processing: (
    <svg className="w-5 h-5 text-blue-500 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
  completed: (
    <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
    </svg>
  ),
  failed: (
    <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
    </svg>
  ),
}

export function QueueItem({
  task,
  onRetry,
  onCancel,
  onViewDetails,
}: QueueItemProps) {
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const { retryTask, cancelTask, isLoading } = useQueueStore()

  const handleRetry = useCallback(async () => {
    await retryTask(task.id)
    onRetry?.(task.id)
  }, [task.id, retryTask, onRetry])

  const handleCancel = useCallback(async () => {
    await cancelTask(task.id)
    onCancel?.(task.id)
    setShowConfirmDialog(false)
  }, [task.id, cancelTask, onCancel])

  const handleViewDetails = useCallback(() => {
    onViewDetails?.(task.id)
  }, [task.id, onViewDetails])

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <>
      <div
        className={`bg-white rounded-lg border p-4 hover:shadow-md transition-shadow ${
          task.status === 'failed' ? 'border-red-200' : 'border-gray-200'
        }`}
        role="listitem"
        aria-label={`Task ${task.id}: ${TASK_TYPE_LABELS[task.type]} - ${task.status}`}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 mt-0.5">{STATUS_ICONS[task.status]}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    task.status === 'pending'
                      ? 'bg-yellow-100 text-yellow-800'
                      : task.status === 'processing'
                      ? 'bg-blue-100 text-blue-800'
                      : task.status === 'completed'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {TASK_TYPE_LABELS[task.type]}
                </span>
                <span className="text-sm text-gray-500 capitalize">{task.status}</span>
              </div>
              <p className="mt-1 text-sm font-medium text-gray-900">
                Task ID: {task.id}
              </p>
              <p className="mt-1 text-xs text-gray-500">
                Created: {formatDate(task.createdAt)}
              </p>
              {task.error && (
                <p className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                  {task.error}
                </p>
              )}
              {(task.status === 'pending' || task.status === 'processing') && (
                <div className="mt-3">
                  <TaskProgress task={task} size="sm" />
                </div>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {task.status === 'failed' && (
              <button
                onClick={handleRetry}
                disabled={isLoading}
                className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-green-700 bg-green-100 hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                aria-label={`Retry task ${task.id}`}
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Retry
              </button>
            )}
            {(task.status === 'pending' || task.status === 'processing') && (
              <button
                onClick={() => setShowConfirmDialog(true)}
                disabled={isLoading}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                aria-label={`Cancel task ${task.id}`}
              >
                Cancel
              </button>
            )}
            <button
              onClick={handleViewDetails}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              aria-label={`View details for task ${task.id}`}
            >
              Details
            </button>
          </div>
        </div>
      </div>

      {showConfirmDialog && (
        <ConfirmDialog
          isOpen={showConfirmDialog}
          title="Cancel Task"
          message="Are you sure you want to cancel this task? This action cannot be undone."
          confirmText="Cancel Task"
          isDangerous
          onConfirm={handleCancel}
          onCancel={() => setShowConfirmDialog(false)}
        />
      )}
    </>
  )
}

export default QueueItem
