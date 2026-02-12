// Common types
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
  page: number
  pageSize: number
  totalPages: number
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, any>
}

// File types
export interface FileItem {
  id: string
  name: string
  path: string
  type: 'file' | 'directory'
  size: number
  mimeType?: string
  createdAt: string
  updatedAt: string
  isIndexed?: boolean
  metadata?: Record<string, any>
}

export interface FileStats {
  totalFiles: number
  totalSize: number
  filesByType: Record<string, number>
  lastUpdated: string
}

// Queue types
export interface QueueTask {
  id: string
  type: 'analyze' | 'sync' | 'index' | 'process'
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  createdAt: string
  updatedAt: string
  error?: string
}

export interface QueueStats {
  totalTasks: number
  pendingTasks: number
  processingTasks: number
  completedTasks: number
  failedTasks: number
}

// Movie types
export interface Movie {
  id: string
  title: string
  year?: number
  genre?: string[]
  rating?: number
  director?: string
  plot?: string
  posterUrl?: string
  fileId?: string
}

// TV Show types
export interface TVShow {
  id: string
  title: string
  year?: number
  genre?: string[]
  rating?: number
  seasons?: number
  episodes?: number
  posterUrl?: string
}

// Search types
export interface SearchFilters {
  query?: string
  type?: 'file' | 'movie' | 'tvshow'
  fileType?: string
  dateFrom?: string
  dateTo?: string
  sizeMin?: number
  sizeMax?: number
  tags?: string[]
}

export interface SearchResult {
  id: string
  title: string
  type: 'file' | 'movie' | 'tvshow'
  path?: string
  relevance: number
}

// UI types
export interface Toast {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  message: string
  duration?: number
}

export interface Modal {
  id: string
  title: string
  content: React.ReactNode
  actions?: ModalAction[]
}

export interface ModalAction {
  label: string
  onClick: () => void
  variant?: 'primary' | 'secondary' | 'danger'
}

// Settings types
export interface UserSettings {
  theme: 'light' | 'dark' | 'auto'
  itemsPerPage: number
  autoRefresh: boolean
  autoRefreshInterval: number
  notifications: boolean
  soundEnabled: boolean
}

export interface ApiSettings {
  baseUrl: string
  timeout: number
  retryAttempts: number
  retryDelay: number
}
