import { apiClient } from '@/utils/api'

export interface DiskStats {
  total_bytes: number
  used_bytes: number
  available_bytes: number
}

export interface LibraryBreakdown {
  movies_bytes: number
  tv_bytes: number
  other_bytes: number
}

export interface StorageSummary {
  disk: DiskStats
  library: LibraryBreakdown
  potential_savings_bytes: number
  files_analyzed: number
  files_pending_analysis: number
  unwatched_movie_size_bytes: number
  unwatched_tv_size_bytes: number
}

export interface StorageFileItem {
  id: number
  name: string
  media_type: 'movie' | 'tv' | 'other'
  size_bytes: number
  duration_seconds: number | null
  video_codec: string | null
  video_width: number | null
  video_height: number | null
  mb_per_min: number | null
  resolution_tier: '4k' | '1080p' | '720p' | 'sd' | 'unknown'
  efficiency_tier: 'efficient' | 'moderate' | 'large' | 'unknown'
  estimated_savings_bytes: number
  is_watched: boolean | null
  show_title: string | null
  show_fully_unwatched: boolean | null
}

export interface StorageFilesResponse {
  total: number
  items: StorageFileItem[]
}

export interface StorageFilesParams {
  page?: number
  pageSize?: number
  sortBy?: string
  sortDir?: 'asc' | 'desc'
  mediaType?: string
  codec?: string
  resolutionTier?: string
  efficiencyTier?: string
  watchedStatus?: 'watched' | 'unwatched'
}

export const storageService = {
  async getSummary(): Promise<StorageSummary> {
    const response = await apiClient.get<StorageSummary>('/storage/summary')
    return response.data
  },

  async getFiles(params: StorageFilesParams = {}): Promise<StorageFilesResponse> {
    const response = await apiClient.get<StorageFilesResponse>('/storage/files', { params })
    return response.data
  },

  async triggerScan(): Promise<void> {
    await apiClient.post('/storage/scan-technical')
  },
}
