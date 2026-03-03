// Persistence configuration types

interface StoreApi {
  getState: () => unknown
  setState: (state: unknown, replace?: boolean) => void
  subscribe: (listener: (state: unknown) => void) => () => void
}

export interface PersistenceConfig {
  name: string
  storage?: 'localStorage' | 'sessionStorage'
  partialize?: (state: unknown) => unknown
  onRehydrateStorage?: (state: unknown) => void
  skipHydration?: boolean
}

// Custom persistence middleware factory
export function createPersistenceMiddleware(config: PersistenceConfig) {
  return (store: StoreApi) => {
    const storage = config.storage === 'sessionStorage' ? sessionStorage : localStorage
    const storageKey = `metamaster-${config.name}`

    // Load persisted state
    const loadPersistedState = () => {
      try {
        const serializedState = storage.getItem(storageKey)
        if (serializedState) {
          const persistedState = JSON.parse(serializedState) as unknown
          if (config.partialize) {
            const partialState = config.partialize(persistedState)
            store.setState({ ...(store.getState() as object), ...(partialState as object) }, true)
          } else {
            store.setState({ ...(store.getState() as object), ...(persistedState as object) }, true)
          }
        }
      } catch (error) {
        console.warn(`Failed to load persisted state for ${config.name}:`, error)
      }
    }

    // Save state to storage
    const saveState = (state: unknown) => {
      try {
        let stateToSave = state
        if (config.partialize) {
          stateToSave = config.partialize(state)
        }
        const serializedState = JSON.stringify(stateToSave)
        storage.setItem(storageKey, serializedState)
      } catch (error) {
        console.warn(`Failed to save state for ${config.name}:`, error)
      }
    }

    // Subscribe to store changes
    const unsubscribe = store.subscribe(saveState)

    // Load initial state
    loadPersistedState()

    // Call onRehydrateStorage callback if provided
    if (config.onRehydrateStorage) {
      config.onRehydrateStorage(store.getState())
    }

    return unsubscribe
  }
}

// Auto-save middleware with debounce
export function createAutoSaveMiddleware(
  storageKey: string,
  delay: number = 1000
) {
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  return (store: StoreApi) => {
    const storage = localStorage
    const key = `metamaster-${storageKey}`

    const saveState = () => {
      if (timeoutId) {
        clearTimeout(timeoutId)
      }

      timeoutId = setTimeout(() => {
        try {
          const state = store.getState()
          const serializedState = JSON.stringify(state)
          storage.setItem(key, serializedState)
        } catch (error) {
          console.warn(`Failed to auto-save state for ${storageKey}:`, error)
        }
      }, delay)
    }

    const unsubscribe = store.subscribe(saveState)

    // Cleanup
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
      unsubscribe()
    }
  }
}

// State encryption middleware
export function createEncryptedStorageMiddleware(
  storageKey: string
) {
  const storage = localStorage
  const key = `metamaster-${storageKey}`

  // Simple encryption (use proper encryption in production)
  const encrypt = (data: string): string => {
    try {
      // Use Base64 encoding with a simple transformation
      // In production, use proper encryption like AES
      return btoa(unescape(encodeURIComponent(data)))
    } catch {
      return data
    }
  }

  const decrypt = (data: string): string => {
    try {
      return decodeURIComponent(escape(atob(data)))
    } catch {
      return data
    }
  }

  return (store: StoreApi) => {
    // Load encrypted state
    const loadEncryptedState = () => {
      try {
        const encryptedData = storage.getItem(key)
        if (encryptedData) {
          const decryptedState = JSON.parse(decrypt(encryptedData)) as unknown
          store.setState({ ...(store.getState() as object), ...(decryptedState as object) }, true)
        }
      } catch (error) {
        console.warn(`Failed to load encrypted state for ${storageKey}:`, error)
      }
    }

    // Save encrypted state
    const saveEncryptedState = (state: unknown) => {
      try {
        const serializedState = JSON.stringify(state)
        const encryptedState = encrypt(serializedState)
        storage.setItem(key, encryptedState)
      } catch (error) {
        console.warn(`Failed to save encrypted state for ${storageKey}:`, error)
      }
    }

    const unsubscribe = store.subscribe(saveEncryptedState)
    loadEncryptedState()

    return unsubscribe
  }
}

// Storage quota management
export function checkStorageQuota(): {
  used: number
  available: number
  percentage: number
} {
  let used = 0
  let available = 0

  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key?.startsWith('metamaster-')) {
        used += (localStorage.getItem(key)?.length || 0) * 2 // UTF-16
      }
    }

    // Estimate available space (not precise)
    available = 5 * 1024 * 1024 // ~5MB default quota
  } catch {
    used = 0
    available = 0
  }

  return {
    used,
    available,
    percentage: available > 0 ? (used / available) * 100 : 0,
  }
}

// Clear all app storage
export function clearAllAppStorage(): void {
  const keysToRemove: string[] = []

  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i)
    if (key?.startsWith('metamaster-') || key?.startsWith('zustand')) {
      keysToRemove.push(key)
    }
  }

  keysToRemove.forEach((key) => localStorage.removeItem(key))
}

// Export storage for debugging
export function exportStorageDebug(): Record<string, unknown> {
  const debug: Record<string, unknown> = {
    quota: checkStorageQuota(),
    stores: {},
  }

  try {
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key?.startsWith('metamaster-') || key?.startsWith('zustand')) {
        const value = localStorage.getItem(key)
        if (value) {
          try {
            (debug.stores as Record<string, unknown>)[key] = JSON.parse(value) as unknown
          } catch {
            (debug.stores as Record<string, unknown>)[key] = value.substring(0, 100) + '...'
          }
        }
      }
    }
  } catch (error) {
    debug.error = String(error)
  }

  return debug
}
