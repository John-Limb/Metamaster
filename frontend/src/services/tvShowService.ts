import { apiClient } from '@/utils/api'
import { errorHandler } from '@/utils/errorHandler'
import type { TVShow, PaginatedResponse, ApiResponse } from '@/types'

const buildPaginationQuery = (page?: number, pageSize?: number) => {
  const params = new URLSearchParams()
  if (page && page >= 1) {
    params.append('page', String(page))
  }
  if (pageSize && pageSize > 0) {
    params.append('pageSize', String(pageSize))
  }
  return params.toString()
}

export const tvShowService = {
  // Get all TV shows
  getTVShows: async (page = 1, pageSize = 20) => {
    try {
      const paginationQuery = buildPaginationQuery(page, pageSize)
      const suffix = paginationQuery ? `?${paginationQuery}` : ''
      const response = await apiClient.get<PaginatedResponse<TVShow>>(`/tv-shows${suffix}`)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `getTVShows: page=${page}`)
      throw error
    }
  },

  // Get TV show details
  getTVShowDetails: async (id: string) => {
    try {
      const response = await apiClient.get<TVShow>(`/tv-shows/${id}`)
      return response.data
    } catch (error: any) {
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
    } catch (error: any) {
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
    } catch (error: any) {
      errorHandler.handleError(error, `getTVShowsByGenre: ${genre}`)
      throw error
    }
  },

  // Create TV show
  createTVShow: async (tvShow: Omit<TVShow, 'id'>) => {
    try {
      const response = await apiClient.post<TVShow>('/tv-shows', tvShow)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `createTVShow: ${tvShow.title}`)
      throw error
    }
  },

  // Update TV show
  updateTVShow: async (id: string, updates: Partial<TVShow>) => {
    try {
      const response = await apiClient.put<TVShow>(`/tv-shows/${id}`, updates)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `updateTVShow: ${id}`)
      throw error
    }
  },

  // Delete TV show
  deleteTVShow: async (id: string) => {
    try {
      const response = await apiClient.delete<ApiResponse<void>>(`/tv-shows/${id}`)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `deleteTVShow: ${id}`)
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
    } catch (error: any) {
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
    } catch (error: any) {
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
    } catch (error: any) {
      errorHandler.handleError(error, 'getTopRatedTVShows')
      throw error
    }
  },
}
