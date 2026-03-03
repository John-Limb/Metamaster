import { useQuery, useQueryClient } from '@tanstack/react-query'
import { searchService } from '@/services/searchService'
import type { SearchResult, SearchFilters, PaginatedResponse } from '@/types'

const SEARCH_QUERY_KEY = ['search']

export const useSearch = (filters: SearchFilters, page = 1, pageSize = 20) => {
  return useQuery<PaginatedResponse<SearchResult>>({
    queryKey: [...SEARCH_QUERY_KEY, filters, page, pageSize],
    queryFn: () => searchService.search(filters, page, pageSize),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled: !!filters.query,
  })
}

export const useSearchFiles = (query: string, page = 1, pageSize = 20) => {
  return useQuery<PaginatedResponse<SearchResult>>({
    queryKey: [...SEARCH_QUERY_KEY, 'files', query, page, pageSize],
    queryFn: () => searchService.searchFiles(query, page, pageSize),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    enabled: !!query,
  })
}

export const useSearchMovies = (query: string, page = 1, pageSize = 20) => {
  return useQuery<PaginatedResponse<SearchResult>>({
    queryKey: [...SEARCH_QUERY_KEY, 'movies', query, page, pageSize],
    queryFn: () => searchService.searchMovies(query, page, pageSize),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    enabled: !!query,
  })
}

export const useSearchTVShows = (query: string, page = 1, pageSize = 20) => {
  return useQuery<PaginatedResponse<SearchResult>>({
    queryKey: [...SEARCH_QUERY_KEY, 'tvshows', query, page, pageSize],
    queryFn: () => searchService.searchTVShows(query, page, pageSize),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    enabled: !!query,
  })
}

export const useSearchSuggestions = (query: string, limit = 10) => {
  return useQuery<string[]>({
    queryKey: [...SEARCH_QUERY_KEY, 'suggestions', query, limit],
    queryFn: () => searchService.getSuggestions(query, limit),
    staleTime: 10 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
    enabled: !!query && query.length > 0,
  })
}

export const useSearchFilters = () => {
  return useQuery<Record<string, unknown>>({
    queryKey: [...SEARCH_QUERY_KEY, 'filters'],
    queryFn: () => searchService.getFilters(),
    staleTime: 30 * 60 * 1000, // 30 minutes
    gcTime: 60 * 60 * 1000, // 1 hour
  })
}

export const useRecentSearches = (limit = 10) => {
  return useQuery<string[]>({
    queryKey: [...SEARCH_QUERY_KEY, 'recent', limit],
    queryFn: () => searchService.getRecentSearches(limit),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })
}

export const useClearSearchHistory = () => {
  const queryClient = useQueryClient()

  return {
    clearHistory: async () => {
      await searchService.clearSearchHistory()
      queryClient.invalidateQueries({ queryKey: [...SEARCH_QUERY_KEY, 'recent'] })
    },
  }
}
