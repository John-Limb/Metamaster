import React from 'react'
import { QueuePanel } from '@/components/queue/QueuePanel'

export function QueuePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-body">Task Queue</h1>
        <p className="text-hint mt-1">
          Monitor and manage background tasks — retry failures, cancel pending work, inspect task details.
        </p>
      </div>
      <QueuePanel autoRefresh refreshInterval={5000} />
    </div>
  )
}

export default QueuePage
