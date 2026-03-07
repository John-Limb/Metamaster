import React, { useEffect, useState, useRef, useCallback } from 'react'
import { healthService, type DetailedHealthCheck, type ComponentLogs, type LogEntry } from '@/services/healthService'
import { Card } from '@/components/common/Card'
import { Button } from '@/components/common/Button'
import { PlexHealthPanel } from '@/components/features/plex/PlexHealthPanel'

const STATUS_DOT: Record<string, string> = {
  healthy: 'bg-emerald-500',
  warning: 'bg-amber-400',
  degraded: 'bg-amber-400',
  unhealthy: 'bg-red-500',
  unavailable: 'bg-slate-400',
}

const STATUS_LABEL: Record<string, string> = {
  healthy: 'Healthy',
  warning: 'Warning',
  degraded: 'Degraded',
  unhealthy: 'Unhealthy',
  unavailable: 'Unavailable',
}

const LOG_COMPONENT_MAP: Record<string, keyof ComponentLogs> = {
  database: 'database',
  cache: 'cache',
  redis: 'cache',
  tasks: 'tasks',
  application: 'api',
  system: 'api',
  api: 'api',
  external_api: 'external_api',
}

function LogTail({ entries }: { entries: LogEntry[] }) {
  if (entries.length === 0) {
    return (
      <p className="text-xs text-slate-500 dark:text-slate-400 italic">No log entries available.</p>
    )
  }
  return (
    <div className="bg-slate-950 rounded p-3 space-y-0.5 overflow-x-auto">
      {entries.map((entry, i) => (
        <div key={i} className="flex gap-2 text-xs font-mono whitespace-nowrap">
          <span className="text-slate-500 flex-shrink-0">
            {entry.timestamp ? new Date(entry.timestamp).toLocaleTimeString() : '—'}
          </span>
          <span className={`flex-shrink-0 font-semibold ${
            entry.level === 'ERROR' ? 'text-red-400' :
            entry.level === 'WARNING' ? 'text-amber-400' :
            entry.level === 'RAW' ? 'text-slate-400' :
            'text-emerald-400'
          }`}>
            {entry.level || '—'}
          </span>
          <span className="text-slate-300 flex-shrink-0">{entry.message}</span>
        </div>
      ))}
    </div>
  )
}

function ComponentCard({
  name,
  check,
  logs,
}: {
  name: string
  check: { status: string; [key: string]: unknown }
  logs: LogEntry[]
}) {
  const status = check.status ?? 'unknown'
  const dotColor = STATUS_DOT[status] ?? 'bg-slate-400'
  const label = STATUS_LABEL[status] ?? status

  const extraKeys = Object.keys(check).filter((k) => k !== 'status' && k !== 'error')

  return (
    <Card variant="elevated" className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${dotColor}`} />
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white capitalize">
            {name.replace(/_/g, ' ')}
          </h3>
        </div>
        <span className={`text-xs font-medium ${
          status === 'healthy' ? 'text-emerald-600 dark:text-emerald-400' :
          status === 'unhealthy' ? 'text-red-600 dark:text-red-400' :
          'text-amber-600 dark:text-amber-400'
        }`}>
          {label}
        </span>
      </div>

      {extraKeys.length > 0 && (
        <div className="flex flex-wrap gap-x-4 gap-y-1">
          {extraKeys.map((key) => (
            <div key={key} className="text-xs text-slate-600 dark:text-slate-400">
              <span className="font-medium">{key.replace(/_/g, ' ')}:</span>{' '}
              {typeof check[key] === 'number'
                ? (check[key] as number).toFixed(1)
                : String(check[key])}
            </div>
          ))}
        </div>
      )}

      {Boolean(check.error) && (
        <p className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded p-2">
          {String(check.error)}
        </p>
      )}

      <div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mb-1 font-medium uppercase tracking-wide">
          Recent logs
        </p>
        <LogTail entries={logs} />
      </div>
    </Card>
  )
}

export function SystemHealthPage() {
  const [health, setHealth] = useState<DetailedHealthCheck | null>(null)
  const [logs, setLogs] = useState<ComponentLogs | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const logIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const fetchHealth = useCallback(async () => {
    try {
      const data = await healthService.getDetailedHealth()
      setHealth(data)
      setError(null)
    } catch {
      setError('Failed to load health status.')
    }
  }, [])

  const fetchLogs = useCallback(async () => {
    try {
      const data = await healthService.getComponentLogs(10)
      setLogs(data)
    } catch {
      // Non-fatal — keep stale log data
    }
  }, [])

  const handleRefresh = async () => {
    setIsRefreshing(true)
    await Promise.all([fetchHealth(), fetchLogs()])
    setIsRefreshing(false)
  }

  useEffect(() => {
    void (async () => {
      await Promise.all([fetchHealth(), fetchLogs()])
      setIsLoading(false)
    })()

    logIntervalRef.current = setInterval(fetchLogs, 2000)
    return () => {
      if (logIntervalRef.current) clearInterval(logIntervalRef.current)
    }
  }, [fetchHealth, fetchLogs])

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 bg-slate-200 dark:bg-slate-700 rounded animate-pulse" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-56 bg-slate-200 dark:bg-slate-700 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (error && !health) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">System Health</h1>
        <Card variant="elevated" className="p-8 text-center">
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <Button variant="primary" onClick={handleRefresh}>Retry</Button>
        </Card>
      </div>
    )
  }

  const overallStatus = health?.status ?? 'unknown'
  const checks = health?.checks ?? {}

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">System Health</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Live component status and log tails — refreshing every 2 seconds.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${STATUS_DOT[overallStatus] ?? 'bg-slate-400'}`} />
            <span className="text-sm font-medium text-slate-700 dark:text-slate-300 capitalize">
              {STATUS_LABEL[overallStatus] ?? overallStatus}
            </span>
          </div>
          <Button variant="outline" onClick={handleRefresh} loading={isRefreshing}>
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Object.entries(checks).map(([name, check]) => {
          const logKey = LOG_COMPONENT_MAP[name]
          const componentLogs = logKey && logs ? logs[logKey] : []
          return (
            <ComponentCard
              key={name}
              name={name}
              check={check}
              logs={componentLogs}
            />
          )
        })}
      </div>

      <Card variant="elevated">
        <PlexHealthPanel />
      </Card>

      {health?.timestamp && (
        <p className="text-xs text-slate-400 dark:text-slate-500 text-right">
          Health checked at {new Date(health.timestamp).toLocaleTimeString()}
        </p>
      )}
    </div>
  )
}

export default SystemHealthPage
