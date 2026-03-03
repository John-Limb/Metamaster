import { apiClient } from '@/utils/api'
import { errorHandler } from '@/utils/errorHandler'
import type { SearchResult, SearchFilters, PaginatedResponse } from '@/types'

export const searchService = {
  // Global search across all content types
  search: async (filters: SearchFilters, page = 1, pageSize = 20) => {
    try {
      const params = new URLSearchParams()
      params.append('page', String(page))
      params.append('pageSize', String(pageSize))

      if (filters.query) params.append('query', filters.query)
      if (filters.type) params.append('type', filters.type)
      if (filters.fileType) params.append('fileType', filters.fileType)
      if (filters.dateFrom) params.append('dateFrom', filters.dateFrom)
      if (filters.dateTo) params.append('dateTo', filters.dateTo)
      if (filters.sizeMin) params.append('sizeMin', String(filters.sizeMin))
      if (filters.sizeMax) params.append('sizeMax', String(filters.sizeMax))
      if (filters.tags?.length) params.append('tags', filters.tags.join(','))

      const response = await apiClient.get<PaginatedResponse<SearchResult>>(
        `/search?${params.toString()}`
      )
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `search: ${filters.query}`)
      throw error
    }
  },

  // Search files only
  searchFiles: async (query: string, page = 1, pageSize = 20) => {
    try {
      const response = await apiClient.get<PaginatedResponse<SearchResult>>(
        `/search/files?query=${encodeURIComponent(query)}&page=${page}&pageSize=${pageSize}`
      )
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `searchFiles: ${query}`)
      throw error
    }
  },

  // Search movies only
  searchMovies: async (query: string, page = 1, pageSize = 20) => {
    try {
      const response = await apiClient.get<PaginatedResponse<SearchResult>>(
        `/search/movies?query=${encodeURIComponent(query)}&page=${page}&pageSize=${pageSize}`
      )
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `searchMovies: ${query}`)
      throw error
    }
  },

  // Search TV shows only
  searchTVShows: async (query: string, page = 1, pageSize = 20) => {
    try {
      const response = await apiClient.get<PaginatedResponse<SearchResult>>(
        `/search/tv-shows?query=${encodeURIComponent(query)}&page=${page}&pageSize=${pageSize}`
      )
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `searchTVShows: ${query}`)
      throw error
    }
  },

  // Get search suggestions
  getSuggestions: async (query: string, limit = 10) => {
    try {
      const response = await apiClient.get<string[]>(
        `/search/suggestions?query=${encodeURIComponent(query)}&limit=${limit}`
      )
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `getSuggestions: ${query}`)
      throw error
    }
  },

  // Get search filters/facets
  getFilters: async () => {
    try {
      const response = await apiClient.get<Record<string, unknown>>('/search/filters')
      return response.data
    } catch (error) {
      errorHandler.handleError(error, 'getFilters')
      throw error
    }
  },

  // Get recent searches
  getRecentSearches: async (limit = 10) => {
    try {
      const response = await apiClient.get<string[]>(`/search/recent?limit=${limit}`)
      return response.data
    } catch (error) {
      errorHandler.handleError(error, 'getRecentSearches')
      throw error
    }
  },

  // Clear search history
  clearSearchHistory: async () => {
    try {
      const response = await apiClient.post('/search/clear-history')
      return response.data
    } catch (error) {
      errorHandler.handleError(error, 'clearSearchHistory')
      throw error
    }
  },
}
