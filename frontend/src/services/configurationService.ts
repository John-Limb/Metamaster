import { apiClient } from '@/utils/api'
import { errorHandler } from '@/utils/errorHandler'

export type ConfigurationSeverity = 'critical' | 'important' | 'optional'
export type ConfigurationStatus = 'valid' | 'invalid' | 'checking'

export interface ConfigurationItem {
  id: string
  name: string
  description: string
  severity: ConfigurationSeverity
  status: ConfigurationStatus
  actionLabel?: string
  actionPath?: string
}

export interface ConfigurationState {
  items: ConfigurationItem[]
  isComplete: boolean
  lastChecked: Date
}

export interface ConfigurationServiceInterface {
  checkAll(): Promise<ConfigurationState>
  checkItem(id: string): Promise<ConfigurationItem>
  dismissItem(id: string): void
  restoreItem(id: string): void
}

// Configuration items to check
const CONFIGURATION_ITEMS: ConfigurationItem[] = [
  // Critical (Error)
  {
    id: 'api-keys-omdb',
    name: 'OMDB API Key',
    description: 'API key for fetching movie metadata from OMDB',
    severity: 'critical',
    status: 'checking',
    actionLabel: 'Configure API Key',
    actionPath: '/settings?section=api-keys',
  },
  {
    id: 'api-keys-tvdb',
    name: 'TVDB API Key',
    description: 'API key for fetching TV show metadata from TVDB',
    severity: 'critical',
    status: 'checking',
    actionLabel: 'Configure API Key',
    actionPath: '/settings?section=api-keys',
  },
  {
    id: 'database-connection',
    name: 'Database Connection',
    description: 'Connection to the PostgreSQL database',
    severity: 'critical',
    status: 'checking',
    actionLabel: 'Check Database',
    actionPath: '/settings?section=database',
  },
  {
    id: 'file-system-paths',
    name: 'File System Paths',
    description: 'Base paths for media library and downloads',
    severity: 'critical',
    status: 'checking',
    actionLabel: 'Configure Paths',
    actionPath: '/settings?section=paths',
  },
  // Important (Warning)
  {
    id: 'file-monitoring',
    name: 'File Monitoring',
    description: 'Watch configured directories for new media files',
    severity: 'important',
    status: 'checking',
    actionLabel: 'Enable Monitoring',
    actionPath: '/settings?section=monitoring',
  },
  {
    id: 'metadata-sources',
    name: 'Metadata Sources',
    description: 'Configured sources for fetching movie and TV show metadata',
    severity: 'important',
    status: 'checking',
    actionLabel: 'Configure Sources',
    actionPath: '/settings?section=metadata',
  },
  {
    id: 'storage-location',
    name: 'Storage Location',
    description: 'Accessible storage location for media files',
    severity: 'important',
    status: 'checking',
    actionLabel: 'Check Storage',
    actionPath: '/settings?section=storage',
  },
  // Optional (Info)
  {
    id: 'dark-mode-preference',
    name: 'Dark Mode',
    description: 'Your preferred theme setting',
    severity: 'optional',
    status: 'checking',
    actionLabel: 'Set Preference',
    actionPath: '/settings?section=appearance',
  },
  {
    id: 'notification-settings',
    name: 'Notifications',
    description: 'Email and push notification preferences',
    severity: 'optional',
    status: 'checking',
    actionLabel: 'Configure',
    actionPath: '/settings?section=notifications',
  },
  {
    id: 'advanced-options',
    name: 'Advanced Options',
    description: 'Cache, performance, and debugging settings',
    severity: 'optional',
    status: 'checking',
    actionLabel: 'Configure',
    actionPath: '/settings?section=advanced',
  },
]

// Store for dismissed items
const DISMISSED_ITEMS_KEY = 'metamaster_dismissed_config_items'

const getDismissedItems = (): Set<string> => {
  if (typeof window === 'undefined') return new Set()
  try {
    const stored = localStorage.getItem(DISMISSED_ITEMS_KEY)
    return stored ? new Set(JSON.parse(stored)) : new Set()
  } catch {
    return new Set()
  }
}

const saveDismissedItems = (items: Set<string>): void => {
  if (typeof window === 'undefined') return
  localStorage.setItem(DISMISSED_ITEMS_KEY, JSON.stringify(Array.from(items)))
}

// Environment variable mapping for configuration items
const ENV_VAR_MAPPING: Record<string, string[]> = {
  'api-keys-omdb': ['VITE_OMDB_API_KEY'],
  'api-keys-tvdb': ['VITE_TVDB_API_KEY', 'VITE_TVDB_PIN'],
  'database-connection': ['VITE_DATABASE_URL', 'DATABASE_URL'],
  'file-system-paths': ['VITE_MOVIE_DIR', 'VITE_TV_DIR', 'MOVIE_DIR', 'TV_DIR'],
  'file-monitoring': ['VITE_WATCH_EXTENSIONS', 'VITE_FILE_MONITORING'],
  'metadata-sources': ['VITE_OMDB_API_KEY', 'VITE_TVDB_API_KEY'],
  'storage-location': ['VITE_MOVIE_DIR', 'VITE_TV_DIR'],
  'dark-mode-preference': ['VITE_DARK_MODE'],
  'notification-settings': ['VITE_NOTIFICATIONS_ENABLED'],
  'advanced-options': ['VITE_ADVANCED_OPTIONS'],
}

// Simulate configuration check (replace with actual API calls)
const checkConfigurationItem = async (item: ConfigurationItem): Promise<ConfigurationItem> => {
  // In production, this would make actual API calls to check configuration
  // For now, we'll simulate based on environment variables
  const envVars = ENV_VAR_MAPPING[item.id] || []
  
  // Check if any of the mapped environment variables are set
  const isConfigured = envVars.some(envVar => {
    const value = import.meta.env?.[envVar]
    return value && value !== '' && value !== 'your_omdb_api_key_here' && value !== 'your_tvdb_api_key_here'
  })

  // Simulate async check
  await new Promise(resolve => setTimeout(resolve, 100 + Math.random() * 200))

  return {
    ...item,
    status: isConfigured ? 'valid' : 'invalid',
  }
}

// Check all configuration items
const checkAllConfigurations = async (): Promise<ConfigurationState> => {
  const dismissedItems = getDismissedItems()
  const itemsToCheck = CONFIGURATION_ITEMS.filter(item => !dismissedItems.has(item.id))
  
  const checkedItems = await Promise.all(
    itemsToCheck.map(item => checkConfigurationItem(item))
  )

  const incompleteItems = checkedItems.filter(item => item.status !== 'valid')
  
  return {
    items: checkedItems,
    isComplete: incompleteItems.length === 0,
    lastChecked: new Date(),
  }
}

export const configurationService: ConfigurationServiceInterface = {
  async checkAll() {
    try {
      const response = await apiClient.get<ConfigurationState>('/config/check')
      return response.data
    } catch (error: any) {
      // Fall back to local check if API is not available
      errorHandler.handleError(error, 'configurationCheck')
      return checkAllConfigurations()
    }
  },

  async checkItem(id: string) {
    try {
      const response = await apiClient.get<ConfigurationItem>(`/config/check/${id}`)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'checkConfigurationItem')
      const item = CONFIGURATION_ITEMS.find(i => i.id === id)
      if (!item) {
        throw new Error(`Configuration item ${id} not found`)
      }
      return checkConfigurationItem(item)
    }
  },

  dismissItem(id: string) {
    const dismissedItems = getDismissedItems()
    dismissedItems.add(id)
    saveDismissedItems(dismissedItems)
  },

  restoreItem(id: string) {
    const dismissedItems = getDismissedItems()
    dismissedItems.delete(id)
    saveDismissedItems(dismissedItems)
  },
}

