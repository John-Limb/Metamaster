import React from 'react'
import { useQueueStore } from '@/stores/queueStore'

interface QueueStatsProps {
  className?: string
}

export function QueueStats({ className = '' }: QueueStatsProps) {
  const { stats, isLoading, error } = useQueueStore()

  if (isLoading && !stats) {
    return (
      <div className={`grid grid-cols-2 md:grid-cols-5 gap-4 ${className}`}>
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="bg-gray-100 rounded-lg p-4 animate-pulse"
          >
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2" />
            <div className="h-8 bg-gray-200 rounded w-3/4" />
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className={`text-red-600 p-4 rounded-lg bg-red-50 ${className}`} role="alert">
        <p className="font-medium">Error loading stats</p>
        <p className="text-sm">{error}</p>
      </div>
    )
  }

  if (!stats) {
    return null
  }

  const statItems = [
    {
      label: 'Total',
      value: stats.totalTasks,
      color: 'bg-gray-100 text-gray-800',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      ),
    },
    {
      label: 'Pending',
      value: stats.pendingTasks,
      color: 'bg-yellow-100 text-yellow-800',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      label: 'Processing',
      value: stats.processingTasks,
      color: 'bg-blue-100 text-blue-800',
      icon: (
        <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      ),
    },
    {
      label: 'Completed',
      value: stats.completedTasks,
      color: 'bg-green-100 text-green-800',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      ),
    },
    {
      label: 'Failed',
      value: stats.failedTasks,
      color: 'bg-red-100 text-red-800',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      ),
    },
  ]

  return (
    <div className={`grid grid-cols-2 md:grid-cols-5 gap-4 ${className}`} role="region" aria-label="Queue statistics">
      {statItems.map((item) => (
        <div
          key={item.label}
          className={`${item.color} rounded-lg p-4`}
        >
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium opacity-75">{item.label}</span>
            {item.icon}
          </div>
          <p className="text-2xl font-bold" aria-label={`${item.label} count: ${item.value}`}>
            {item.value}
          </p>
        </div>
      ))}
    </div>
  )
}

export default QueueStats
