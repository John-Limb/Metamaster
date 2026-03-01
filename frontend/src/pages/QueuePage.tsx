import React from 'react'
import { QueuePanel } from '@/components/queue/QueuePanel'

export function QueuePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Task Queue</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Monitor and manage background tasks — retry failures, cancel pending work, inspect task details.
        </p>
      </div>
      <QueuePanel autoRefresh refreshInterval={5000} />
    </div>
  )
}

export default QueuePage
