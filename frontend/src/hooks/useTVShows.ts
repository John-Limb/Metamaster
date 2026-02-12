import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tvShowService } from '@/services/tvShowService'
import type { TVShow, PaginatedResponse } from '@/types'

const TV_SHOWS_QUERY_KEY = ['tvShows']

export const useTVShows = (page = 1, pageSize = 20) => {
  return useQuery<PaginatedResponse<TVShow>>({
    queryKey: [...TV_SHOWS_QUERY_KEY, page, pageSize],
    queryFn: () => tvShowService.getTVShows(page, pageSize),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
  })
}

export const useTVShowDetails = (id: string) => {
  return useQuery<TVShow>({
    queryKey: [...TV_SHOWS_QUERY_KEY, 'details', id],
    queryFn: () => tvShowService.getTVShowDetails(id),
    staleTime: 10 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
    enabled: !!id,
  })
}

export const useSearchTVShows = (query: string, page = 1, pageSize = 20) => {
  return useQuery<PaginatedResponse<TVShow>>({
    queryKey: [...TV_SHOWS_QUERY_KEY, 'search', query, page, pageSize],
    queryFn: () => tvShowService.searchTVShows(query, page, pageSize),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    enabled: !!query,
  })
}

export const useTVShowsByGenre = (genre: string, page = 1, pageSize = 20) => {
  return useQuery<PaginatedResponse<TVShow>>({
    queryKey: [...TV_SHOWS_QUERY_KEY, 'genre', genre, page, pageSize],
    queryFn: () => tvShowService.getTVShowsByGenre(genre, page, pageSize),
    staleTime: 10 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
    enabled: !!genre,
  })
}

export const usePopularTVShows = (page = 1, pageSize = 20) => {
  return useQuery<PaginatedResponse<TVShow>>({
    queryKey: [...TV_SHOWS_QUERY_KEY, 'popular', page, pageSize],
    queryFn: () => tvShowService.getPopularTVShows(page, pageSize),
    staleTime: 10 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  })
}

export const useTopRatedTVShows = (page = 1, pageSize = 20) => {
  return useQuery<PaginatedResponse<TVShow>>({
    queryKey: [...TV_SHOWS_QUERY_KEY, 'top-rated', page, pageSize],
    queryFn: () => tvShowService.getTopRatedTVShows(page, pageSize),
    staleTime: 10 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  })
}

export const useCreateTVShow = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (tvShow: Omit<TVShow, 'id'>) => tvShowService.createTVShow(tvShow),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TV_SHOWS_QUERY_KEY })
    },
  })
}

export const useUpdateTVShow = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<TVShow> }) =>
      tvShowService.updateTVShow(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TV_SHOWS_QUERY_KEY })
    },
  })
}

export const useDeleteTVShow = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => tvShowService.deleteTVShow(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TV_SHOWS_QUERY_KEY })
    },
  })
}
