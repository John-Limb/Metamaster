import React, { useState } from 'react'
import { Card } from '@/components/common/Card'
import { formatFileSize } from '@/utils/helpers'

export interface StorageData {
  label: string
  value: number
  color: string
}

export interface StorageChartProps {
  data: StorageData[]
  total: number
  className?: string
  showLegend?: boolean
  diskUsedBytes?: number
  diskTotalBytes?: number
}

const DEFAULT_COLORS = [
  '#6366f1', // var(--color-primary-500) - indigo
  '#8b5cf6', // violet-500 (accent color)
  '#06b6d4', // cyan-500 (accent color, similar to info)
  '#10b981', // var(--color-success) - emerald
  '#f59e0b', // var(--color-warning) - amber
]

export function StorageChart({
  data,
  total,
  className = '',
  showLegend = true,
  diskUsedBytes,
  diskTotalBytes,
}: StorageChartProps) {
  const [activeSegment, setActiveSegment] = useState<string | null>(null)

  const renderChart = () => {
    if (data.length === 0) return null

    const chartData = data.map((item, index) => ({
      ...item,
      color: item.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length],
    }))

    const circumference = 2 * Math.PI * 40
    let currentOffset = 0

    return (
      <div
        className="relative h-48 w-48 flex-shrink-0"
        role="img"
        aria-label="Storage usage chart"
      >
        <svg viewBox="0 0 100 100" className="transform -rotate-90 w-full h-full">
          {chartData.map((item) => {
            const percentage = (item.value / total) * 100
            const segmentLength = (percentage / 100) * circumference
            const offset = circumference * (currentOffset / 100)
            currentOffset += percentage

            return (
              <circle
                key={item.label}
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke={item.color}
                strokeWidth="12"
                strokeDasharray={`${segmentLength} ${circumference}`}
                strokeDashoffset={-offset}
                className={`
                  transition-all duration-500 ease-out cursor-pointer
                  ${activeSegment === item.label ? 'opacity-100' : 'opacity-70 hover:opacity-90'}
                `}
                onMouseEnter={() => setActiveSegment(item.label)}
                onMouseLeave={() => setActiveSegment(null)}
              />
            )
          })}
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r="40"
            fill="none"
            stroke="currentColor"
            strokeWidth="12"
            className="text-slate-100 dark:text-slate-800 opacity-50"
          />
        </svg>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-slate-900 dark:text-white">
            {formatFileSize(total)}
          </span>
          <span className="text-xs text-slate-500 dark:text-slate-400">
            Total Used
          </span>
        </div>
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <Card variant="elevated" className={className}>
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
    )
  }

  const chartData = data.map((item, index) => ({
    ...item,
    color: item.color || DEFAULT_COLORS[index % DEFAULT_COLORS.length],
    percentage: ((item.value / total) * 100).toFixed(1),
  }))

  return (
    <Card variant="elevated" className={className}>
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
        Storage Usage
      </h3>
      <div className="flex flex-col md:flex-row items-center gap-6">
        {renderChart()}
        {showLegend && (
          <div className="flex-1 space-y-3 w-full" role="list" aria-label="Storage breakdown">
            {chartData.map((item) => (
              <div
                key={item.label}
                className={`
                  flex items-center gap-3 p-3 rounded-lg transition-all duration-200
                  ${activeSegment === item.label ? 'bg-slate-50 dark:bg-slate-800/50' : ''}
                `}
                role="listitem"
                onMouseEnter={() => setActiveSegment(item.label)}
                onMouseLeave={() => setActiveSegment(null)}
              >
                <div
                  className="w-4 h-4 rounded-full flex-shrink-0 ring-2 ring-white dark:ring-slate-900"
                  style={{ backgroundColor: item.color }}
                  aria-hidden="true"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300 truncate">
                      {item.label}
                    </span>
                    <span className="text-sm text-slate-500 dark:text-slate-400 flex-shrink-0 ml-2">
                      {item.percentage}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 dark:text-slate-500">
                      {formatFileSize(item.value)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Disk usage bar */}
      {diskUsedBytes !== undefined && diskTotalBytes !== undefined && diskTotalBytes > 0 && (() => {
        const pct = Math.round((diskUsedBytes / diskTotalBytes) * 100)
        return (
          <div className="mt-6 pt-4 border-t border-slate-200 dark:border-slate-700">
            <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400 mb-1.5">
              <span>{formatFileSize(diskUsedBytes)} used</span>
              <span>{formatFileSize(diskTotalBytes)} total</span>
            </div>
            <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-1.5">
              <div
                className={`h-1.5 rounded-full transition-all ${pct > 90 ? 'bg-red-500' : pct > 70 ? 'bg-amber-400' : 'bg-emerald-500'}`}
                style={{ width: `${Math.min(pct, 100)}%` }}
              />
            </div>
          </div>
        )
      })()}
    </Card>
  )
}

export default StorageChart
