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
  movieCount: number
  tvShowCount: number
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

export type EnrichmentStatusValue =
  | 'pending_local'
  | 'local_only'
  | 'pending_external'
  | 'fully_enriched'
  | 'external_failed'
  | 'not_found'

// Movie types
export interface Movie {
  id: string
  title: string
  year?: number
  genre?: string[]
  genres?: string
  rating?: number
  runtime?: number
  director?: string
  plot?: string
  poster_url?: string
  tmdb_id?: string
  fileId?: string
  created_at?: string
  updated_at?: string
  enrichment_status?: EnrichmentStatusValue | null
  enrichment_error?: string | null
  // Technical metadata from FFprobe
  quality?: string
  resolution?: string
  codec_video?: string
  codec_audio?: string
  audio_channels?: string
  file_duration?: number
  file_size?: number
}

// TV Show types
export interface TVShow {
  id: string
  title: string
  year?: number
  genre?: string[]
  genres?: string
  rating?: number
  seasons?: number
  episodes?: number
  status?: string
  plot?: string
  poster_url?: string
  tmdb_id?: string
  created_at?: string
  updated_at?: string
  enrichment_status?: EnrichmentStatusValue | null
  enrichment_error?: string | null
}

export interface Season {
  id: number
  season_number: number
  tmdb_id?: string | null
  episode_count?: number | null
  created_at: string
}

export interface Episode {
  id: number
  episode_number: number
  title?: string | null
  plot?: string | null
  air_date?: string | null
  rating?: number | null
  tmdb_id?: string | null
  quality?: string | null
  runtime?: number | null
  created_at: string
  updated_at: string
}

// File classification types
export interface FileClassificationResult {
  filename: string
  type: 'movie' | 'tv_show'
  confidence: 'high' | 'medium' | 'low'
  pattern_matched: string
  title?: string
  show_name?: string
  year?: number
  season?: number
  episode?: number
}

export interface FileClassifyResponse {
  results: FileClassificationResult[]
  total: number
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
