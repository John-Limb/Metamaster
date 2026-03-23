import { apiClient } from '@/utils/api'
import { errorHandler } from '@/utils/errorHandler'
import type { TVShow, Season, Episode, PaginatedResponse, ApiResponse } from '@/types'
import type { EnrichmentStatusGroup, EnrichmentStats } from '@/services/movieService'
import { buildPaginationQuery } from './queryUtils'

export type { EnrichmentStatusGroup, EnrichmentStats }

export const tvShowService = {
  // Get all TV shows, optionally filtered by enrichment status group
  getTVShows: async (page = 1, pageSize = 20, status?: EnrichmentStatusGroup) => {
    try {
      const params = new URLSearchParams()
      if (page >= 1) params.append('page', String(page))
      if (pageSize > 0) params.append('pageSize', String(pageSize))
      if (status) params.append('status', status)
      const suffix = params.toString() ? `?${params.toString()}` : ''
      const response = await apiClient.get<PaginatedResponse<TVShow>>(`/tv-shows${suffix}`)
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `getTVShows: page=${page}`)
      throw error
    }
  },

  // Get seasons for a TV show
  getSeasons: async (showId: string, page = 1, pageSize = 50) => {
    try {
      const params = new URLSearchParams({ page: String(page), pageSize: String(pageSize) })
      const response = await apiClient.get<PaginatedResponse<Season>>(
        `/tv-shows/${showId}/seasons?${params}`
      )
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `getSeasons: showId=${showId}`)
      throw error
    }
  },

  // Get episodes for a season
  getEpisodes: async (showId: string, seasonId: number, page = 1, pageSize = 100) => {
    try {
      const params = new URLSearchParams({ page: String(page), pageSize: String(pageSize) })
      const response = await apiClient.get<PaginatedResponse<Episode>>(
        `/tv-shows/${showId}/seasons/${seasonId}/episodes?${params}`
      )
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `getEpisodes: showId=${showId}, seasonId=${seasonId}`)
      throw error
    }
  },

  // Get enrichment status counts (indexed / pending / failed)
  getEnrichmentStats: async (): Promise<EnrichmentStats> => {
    try {
      const response = await apiClient.get<EnrichmentStats>('/tv-shows/enrichment-stats')
      return response.data
    } catch (error) {
      errorHandler.handleError(error, 'getEnrichmentStats (tv-shows)')
      throw error
    }
  },

  // Get TV show details
  getTVShowDetails: async (id: string) => {
    try {
      const response = await apiClient.get<TVShow>(`/tv-shows/${id}`)
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `getTVShowDetails: ${id}`)
      throw error
    }
  },

  // Search TV shows
  searchTVShows: async (query: string, page = 1, pageSize = 20) => {
    try {
      const paginationQuery = buildPaginationQuery(page, pageSize)
      const separator = paginationQuery ? `&${paginationQuery}` : ''
      const response = await apiClient.get<PaginatedResponse<TVShow>>(
        `/tv-shows/search?q=${encodeURIComponent(query)}${separator}`
      )
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `searchTVShows: ${query}`)
      throw error
    }
  },

  // Get TV shows by genre
  getTVShowsByGenre: async (genre: string, page = 1, pageSize = 20) => {
    try {
      const paginationQuery = buildPaginationQuery(page, pageSize)
      const suffix = paginationQuery ? `?${paginationQuery}` : ''
      const response = await apiClient.get<PaginatedResponse<TVShow>>(
        `/genres/${encodeURIComponent(genre)}/tv-shows${suffix}`
      )
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `getTVShowsByGenre: ${genre}`)
      throw error
    }
  },

  // Create TV show
  createTVShow: async (tvShow: Omit<TVShow, 'id'>) => {
    try {
      const response = await apiClient.post<TVShow>('/tv-shows', tvShow)
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `createTVShow: ${tvShow.title}`)
      throw error
    }
  },

  // Update TV show
  updateTVShow: async (id: string, updates: Partial<TVShow>) => {
    try {
      const response = await apiClient.put<TVShow>(`/tv-shows/${id}`, updates)
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `updateTVShow: ${id}`)
      throw error
    }
  },

  // Delete TV show
  deleteTVShow: async (id: string) => {
    try {
      const response = await apiClient.delete<ApiResponse<void>>(`/tv-shows/${id}`)
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `deleteTVShow: ${id}`)
      throw error
    }
  },

  // Sync metadata from TMDB
  syncMetadata: async (id: string) => {
    try {
      const response = await apiClient.post<TVShow>(`/tv-shows/${id}/sync-metadata`)
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `syncMetadata: ${id}`)
      throw error
    }
  },

  // Get popular TV shows
  getPopularTVShows: async (page = 1, pageSize = 20) => {
    try {
      const paginationQuery = buildPaginationQuery(page, pageSize)
      const suffix = paginationQuery ? `?${paginationQuery}` : ''
      const response = await apiClient.get<PaginatedResponse<TVShow>>(
        `/tv-shows/popular${suffix}`
      )
      return response.data
    } catch (error) {
      errorHandler.handleError(error, 'getPopularTVShows')
      throw error
    }
  },

  // Scan TV directory for new files
  scanDirectory: async () => {
    try {
      const response = await apiClient.post<{ files_synced: number; shows_created: number }>(
        '/tv-shows/scan-directory'
      )
      return response.data
    } catch (error) {
      errorHandler.handleError(error, 'scanDirectory')
      throw error
    }
  },

  // Get top rated TV shows
  getTopRatedTVShows: async (page = 1, pageSize = 20) => {
    try {
      const paginationQuery = buildPaginationQuery(page, pageSize)
      const suffix = paginationQuery ? `?${paginationQuery}` : ''
      const response = await apiClient.get<PaginatedResponse<TVShow>>(
        `/tv-shows/top-rated${suffix}`
      )
      return response.data
    } catch (error) {
      errorHandler.handleError(error, 'getTopRatedTVShows')
      throw error
    }
  },
}
