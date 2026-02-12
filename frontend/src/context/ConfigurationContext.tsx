import React, { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react'
import { configurationService, type ConfigurationState, type ConfigurationItem } from '@/services/configurationService'

export interface ConfigurationContextType {
  state: ConfigurationState
  isLoading: boolean
  error: Error | null
  refresh: () => Promise<void>
  checkItem: (id: string) => Promise<ConfigurationItem>
  dismissItem: (id: string) => void
  restoreItem: (id: string) => void
  isConfigurationComplete: boolean
  getItemsBySeverity: (severity: 'critical' | 'important' | 'optional') => ConfigurationItem[]
}

const ConfigurationContext = createContext<ConfigurationContextType | undefined>(undefined)

interface ConfigurationProviderProps {
  children: ReactNode
  autoRefresh?: boolean
  refreshInterval?: number
}

const INITIAL_STATE: ConfigurationState = {
  items: [],
  isComplete: false,
  lastChecked: new Date(),
}

export function ConfigurationProvider({
  children,
  autoRefresh = true,
  refreshInterval = 30000, // 30 seconds
}: ConfigurationProviderProps) {
  const [state, setState] = useState<ConfigurationState>(INITIAL_STATE)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  const refresh = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const newState = await configurationService.checkAll()
      setState(newState)
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to check configuration'))
    } finally {
      setIsLoading(false)
    }
  }, [])

  const checkItem = useCallback(async (id: string): Promise<ConfigurationItem> => {
    try {
      const item = await configurationService.checkItem(id)
      setState(prevState => ({
        ...prevState,
        items: prevState.items.map(i => (i.id === id ? item : i)),
        lastChecked: new Date(),
      }))
      return item
    } catch (err) {
      setError(err instanceof Error ? err : new Error(`Failed to check item ${id}`))
      throw err
    }
  }, [])

  const dismissItem = useCallback((id: string) => {
    configurationService.dismissItem(id)
    setState(prevState => ({
      ...prevState,
      items: prevState.items.filter(item => item.id !== id),
    }))
  }, [])

  const restoreItem = useCallback((id: string) => {
    configurationService.restoreItem(id)
    // Trigger a refresh to re-include the restored item
    refresh()
  }, [refresh])

  const isConfigurationComplete = state.isComplete

  const getItemsBySeverity = useCallback(
    (severity: 'critical' | 'important' | 'optional'): ConfigurationItem[] => {
      return state.items.filter(item => item.severity === severity)
    },
    [state.items]
  )

  // Initial load
  useEffect(() => {
    refresh()
  }, [refresh])

  // Auto refresh
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      refresh()
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval, refresh])

  return (
    <ConfigurationContext.Provider
      value={{
        state,
        isLoading,
        error,
        refresh,
        checkItem,
        dismissItem,
        restoreItem,
        isConfigurationComplete,
        getItemsBySeverity,
      }}
    >
      {children}
    </ConfigurationContext.Provider>
  )
}

export function useConfiguration(): ConfigurationContextType {
  const context = useContext(ConfigurationContext)
  if (context === undefined) {
    throw new Error('useConfiguration must be used within a ConfigurationProvider')
  }
  return context
}

// Helper hook for checking specific configuration requirements
export function useConfigurationCheck(itemId: string): {
  isConfigured: boolean
  isChecking: boolean
  error: Error | null
  refresh: () => Promise<void>
} {
  const { state, isLoading, error, checkItem } = useConfiguration()

  const item = state.items.find(i => i.id === itemId)
  const isConfigured = item?.status === 'valid'
  const isChecking = item?.status === 'checking'

  const refreshCheck = useCallback(async () => {
    await checkItem(itemId)
  }, [checkItem, itemId])

  return {
    isConfigured: isConfigured || false,
    isChecking: isChecking || false,
    error,
    refresh: refreshCheck,
  }
}

// Helper hook for getting incomplete items count
export function useIncompleteConfiguration(): {
  criticalCount: number
  importantCount: number
  optionalCount: number
  totalCount: number
} {
  const { state } = useConfiguration()

  const items = state.items.filter(item => item.status !== 'valid')

  return {
    criticalCount: items.filter(i => i.severity === 'critical').length,
    importantCount: items.filter(i => i.severity === 'important').length,
    optionalCount: items.filter(i => i.severity === 'optional').length,
    totalCount: items.length,
  }
}
