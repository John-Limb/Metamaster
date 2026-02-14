import { apiClient } from '@/utils/api'
import { errorHandler } from '@/utils/errorHandler'
import type { Movie, PaginatedResponse, ApiResponse } from '@/types'
import type { paths } from '@/types/api-schema'

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

export const movieService = {
  // Get all movies
  getMovies: async (page = 1, pageSize = 20) => {
    try {
      const paginationQuery = buildPaginationQuery(page, pageSize)
      const suffix = paginationQuery ? `?${paginationQuery}` : ''
      const response = await apiClient.get<PaginatedResponse<Movie>>(`/movies${suffix}`)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `getMovies: page=${page}`)
      throw error
    }
  },

  // Get movie details
  getMovieDetails: async (id: string) => {
    try {
      const response = await apiClient.get<Movie>(`/movies/${id}`)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `getMovieDetails: ${id}`)
      throw error
    }
  },

  // Search movies
  searchMovies: async (query: string, page = 1, pageSize = 20) => {
    try {
      const paginationQuery = buildPaginationQuery(page, pageSize)
      const separator = paginationQuery ? `&${paginationQuery}` : ''
      const response = await apiClient.get<PaginatedResponse<Movie>>(
        `/movies/search?q=${encodeURIComponent(query)}${separator}`
      )
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `searchMovies: ${query}`)
      throw error
    }
  },

  // Get movies by genre
  getMoviesByGenre: async (genre: string, page = 1, pageSize = 20) => {
    try {
      const paginationQuery = buildPaginationQuery(page, pageSize)
      const suffix = paginationQuery ? `?${paginationQuery}` : ''
      const response = await apiClient.get<PaginatedResponse<Movie>>(
        `/genres/${encodeURIComponent(genre)}/movies${suffix}`
      )
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `getMoviesByGenre: ${genre}`)
      throw error
    }
  },

  // Create movie
  createMovie: async (movie: Omit<Movie, 'id'>) => {
    try {
      const response = await apiClient.post<Movie>('/movies', movie)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `createMovie: ${movie.title}`)
      throw error
    }
  },

  // Update movie
  updateMovie: async (id: string, updates: Partial<Movie>) => {
    try {
      const response = await apiClient.put<Movie>(`/movies/${id}`, updates)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `updateMovie: ${id}`)
      throw error
    }
  },

  // Delete movie
  deleteMovie: async (id: string) => {
    try {
      const response = await apiClient.delete<ApiResponse<void>>(`/movies/${id}`)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `deleteMovie: ${id}`)
      throw error
    }
  },

  // Get popular movies
  getPopularMovies: async (page = 1, pageSize = 20) => {
    try {
      const paginationQuery = buildPaginationQuery(page, pageSize)
      const suffix = paginationQuery ? `?${paginationQuery}` : ''
      const response = await apiClient.get<PaginatedResponse<Movie>>(
        `/movies/popular${suffix}`
      )
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'getPopularMovies')
      throw error
    }
  },

  // Scan a movie file with FFprobe
  scanMovie: async (id: string) => {
    try {
      const response = await apiClient.post<Movie>(`/movies/${id}/scan`)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `scanMovie: ${id}`)
      throw error
    }
  },

  // Get top rated movies
  getTopRatedMovies: async (page = 1, pageSize = 20) => {
    try {
      const paginationQuery = buildPaginationQuery(page, pageSize)
      const suffix = paginationQuery ? `?${paginationQuery}` : ''
      const response = await apiClient.get<PaginatedResponse<Movie>>(
        `/movies/top-rated${suffix}`
      )
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'getTopRatedMovies')
      throw error
    }
  },
}
