import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { movieService } from '@/services/movieService'
import type { Movie, PaginatedResponse } from '@/types'

const MOVIES_QUERY_KEY = ['movies']

export const useMovies = (page = 1, pageSize = 20) => {
  return useQuery<PaginatedResponse<Movie>>({
    queryKey: [...MOVIES_QUERY_KEY, page, pageSize],
    queryFn: () => movieService.getMovies(page, pageSize),
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
  })
}

export const useMovieDetails = (id: string) => {
  return useQuery<Movie>({
    queryKey: [...MOVIES_QUERY_KEY, 'details', id],
    queryFn: () => movieService.getMovieDetails(id),
    staleTime: 10 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
    enabled: !!id,
  })
}

export const useSearchMovies = (query: string, page = 1, pageSize = 20) => {
  return useQuery<PaginatedResponse<Movie>>({
    queryKey: [...MOVIES_QUERY_KEY, 'search', query, page, pageSize],
    queryFn: () => movieService.searchMovies(query, page, pageSize),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    enabled: !!query,
  })
}

export const useMoviesByGenre = (genre: string, page = 1, pageSize = 20) => {
  return useQuery<PaginatedResponse<Movie>>({
    queryKey: [...MOVIES_QUERY_KEY, 'genre', genre, page, pageSize],
    queryFn: () => movieService.getMoviesByGenre(genre, page, pageSize),
    staleTime: 10 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
    enabled: !!genre,
  })
}

export const usePopularMovies = (page = 1, pageSize = 20) => {
  return useQuery<PaginatedResponse<Movie>>({
    queryKey: [...MOVIES_QUERY_KEY, 'popular', page, pageSize],
    queryFn: () => movieService.getPopularMovies(page, pageSize),
    staleTime: 10 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  })
}

export const useTopRatedMovies = (page = 1, pageSize = 20) => {
  return useQuery<PaginatedResponse<Movie>>({
    queryKey: [...MOVIES_QUERY_KEY, 'top-rated', page, pageSize],
    queryFn: () => movieService.getTopRatedMovies(page, pageSize),
    staleTime: 10 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  })
}

export const useCreateMovie = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (movie: Omit<Movie, 'id'>) => movieService.createMovie(movie),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MOVIES_QUERY_KEY })
    },
  })
}

export const useUpdateMovie = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<Movie> }) =>
      movieService.updateMovie(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MOVIES_QUERY_KEY })
    },
  })
}

export const useDeleteMovie = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => movieService.deleteMovie(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: MOVIES_QUERY_KEY })
    },
  })
}
