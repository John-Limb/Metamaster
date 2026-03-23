import React from 'react'
import type { QueueTask } from '@/types'

interface TaskProgressProps {
  task: QueueTask
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const STATUS_COLORS: Record<QueueTask['status'], string> = {
  pending: 'bg-yellow-400',
  processing: 'bg-blue-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
}

const STATUS_LABELS: Record<QueueTask['status'], string> = {
  pending: 'Pending',
  processing: 'Processing',
  completed: 'Completed',
  failed: 'Failed',
}

export function TaskProgress({
  task,
  showLabel = true,
  size = 'md',
}: TaskProgressProps) {
  const sizeClasses = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  }

  const labelSizes = {
    sm: 'text-xs',
    md: 'text-sm',
    lg: 'text-base',
  }

  return (
    <div className="w-full">
      {(showLabel || task.status === 'processing') && (
        <div className="flex items-center justify-between mb-1">
          {showLabel && (
            <span className={`${labelSizes[size]} font-medium text-dim`}>
              {STATUS_LABELS[task.status]}
            </span>
          )}
          {task.status === 'processing' && (
            <span className={`${labelSizes[size]} text-hint`}>
              {task.progress}%
            </span>
          )}
        </div>
      )}
      <div className={`w-full bg-subtle rounded-full overflow-hidden ${sizeClasses[size]}`}>
        <div
          className={`${STATUS_COLORS[task.status]} ${sizeClasses[size]} rounded-full transition-all duration-300 ease-out`}
          style={{ width: `${task.progress}%` }}
          role="progressbar"
          aria-valuenow={task.progress}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Task progress: ${task.progress}%`}
        />
      </div>
    </div>
  )
}

export default TaskProgress
