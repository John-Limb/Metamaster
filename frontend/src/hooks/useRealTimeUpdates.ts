import { useEffect, useRef, useCallback, useState } from 'react'
import { useQueueStore } from '@/stores/queueStore'
import { useFileStore } from '@/stores/fileStore'
import { useSettingsStore } from '@/stores/settingsStore'

interface UseRealTimeOptions {
  enabled?: boolean
  interval?: number
  onError?: (error: Error) => void
}

// Polling hook for queue updates
export function useQueuePolling(options: UseRealTimeOptions = {}) {
  const { enabled = true, interval = 5000, onError } = options
  const { fetchTasks, fetchStats, pollingEnabled, setPollingEnabled } = useQueueStore()
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const isActiveRef = useRef(false)

  const startPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }

    intervalRef.current = setInterval(async () => {
      if (!isActiveRef.current) return

      try {
        await Promise.all([fetchTasks(), fetchStats()])
      } catch (error) {
        if (onError && error instanceof Error) {
          onError(error)
        }
      }
    }, interval)

    isActiveRef.current = true
  }, [fetchTasks, fetchStats, interval, onError])

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    isActiveRef.current = false
  }, [])

  useEffect(() => {
    if (enabled && pollingEnabled) {
      startPolling()
    } else {
      stopPolling()
    }

    return () => {
      stopPolling()
    }
  }, [enabled, pollingEnabled, startPolling, stopPolling])

  // Derive polling status from stable inputs instead of reading ref during render
  const isPolling = enabled && pollingEnabled

  return {
    startPolling,
    stopPolling,
    isPolling,
    setPollingEnabled,
  }
}

// Auto-refresh hook for files
export function useFileAutoRefresh(options: UseRealTimeOptions = {}) {
  const { enabled = true, interval = 30000, onError } = options
  const { currentPath, fetchFiles } = useFileStore()
  const { userSettings } = useSettingsStore()
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (enabled && userSettings.autoRefresh) {
      intervalRef.current = setInterval(() => {
        try {
          fetchFiles(currentPath)
        } catch (error) {
          if (onError && error instanceof Error) {
            onError(error)
          }
        }
      }, interval || userSettings.autoRefreshInterval)
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [enabled, currentPath, fetchFiles, interval, userSettings.autoRefresh, userSettings.autoRefreshInterval, onError])
}

// WebSocket connection hook (optional support)
export function useWebSocket(
  url: string,
  options: {
    onMessage?: (data: unknown) => void
    onOpen?: () => void
    onClose?: () => void
    onError?: (error: Event) => void
    reconnect?: boolean
    reconnectInterval?: number
  } = {}
) {
  const {
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnect = true,
    reconnectInterval = 5000,
  } = options

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const isConnectedRef = useRef(false)
  const [isConnected, setIsConnected] = useState(false)

  // Use a ref to hold connect so the onclose handler can call it without
  // creating a circular useCallback dependency.
  const connectRef = useRef<() => void>(() => undefined)

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      wsRef.current = new WebSocket(url)

      wsRef.current.onopen = () => {
        isConnectedRef.current = true
        setIsConnected(true)
        onOpen?.()
      }

      wsRef.current.onmessage = (event: MessageEvent) => {
        try {
          const data: unknown = JSON.parse(event.data as string)
          onMessage?.(data)
        } catch {
          onMessage?.(event.data as unknown)
        }
      }

      wsRef.current.onclose = () => {
        isConnectedRef.current = false
        setIsConnected(false)
        onClose?.()

        if (reconnect) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connectRef.current()
          }, reconnectInterval)
        }
      }

      wsRef.current.onerror = (error) => {
        onError?.(error)
      }
    } catch (error) {
      console.error('WebSocket connection error:', error)
    }
  }, [url, onMessage, onOpen, onClose, onError, reconnect, reconnectInterval])

  // Keep the ref in sync with the latest connect callback
  useEffect(() => {
    connectRef.current = connect
  }, [connect])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    isConnectedRef.current = false
    setIsConnected(false)
  }, [])

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }, [])

  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [connect, disconnect])

  return {
    connect,
    disconnect,
    send,
    isConnected,
  }
}

// Background sync hook
export function useBackgroundSync(
  options: {
    syncQueue?: boolean
    syncFiles?: boolean
    syncInterval?: number
    onSyncComplete?: () => void
    onSyncError?: (error: Error) => void
  } = {}
) {
  const {
    syncQueue = true,
    syncFiles = false,
    syncInterval = 60000,
    onSyncComplete,
    onSyncError,
  } = options

  const { fetchTasks, fetchStats } = useQueueStore()
  const { fetchFiles, currentPath } = useFileStore()
  const syncTimeoutRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const performSync = useCallback(async () => {
    try {
      if (syncQueue) {
        await Promise.all([fetchTasks(), fetchStats()])
      }

      if (syncFiles) {
        await fetchFiles(currentPath)
      }

      onSyncComplete?.()
    } catch (error) {
      if (onSyncError && error instanceof Error) {
        onSyncError(error)
      }
    }
  }, [syncQueue, syncFiles, fetchTasks, fetchStats, fetchFiles, currentPath, onSyncComplete, onSyncError])

  useEffect(() => {
    // Initial sync
    performSync()

    // Periodic sync
    syncTimeoutRef.current = setInterval(performSync, syncInterval)

    return () => {
      if (syncTimeoutRef.current) {
        clearInterval(syncTimeoutRef.current)
      }
    }
  }, [performSync, syncInterval])

  return {
    sync: performSync,
  }
}

// Hook to manage visibility change (background/foreground)
export function useVisibilityChange(onVisibilityChange?: (isVisible: boolean) => void) {
  useEffect(() => {
    const handleVisibilityChange = () => {
      onVisibilityChange?.(document.visibilityState === 'visible')
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [onVisibilityChange])
}
