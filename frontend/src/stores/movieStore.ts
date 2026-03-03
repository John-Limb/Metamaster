import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Movie } from '@/types'
import { movieService } from '@/services/movieService'

interface MovieState {
  // Movie state
  movies: Movie[]
  selectedMovie: Movie | null
  totalMovies: number
  currentPage: number
  pageSize: number
  isLoading: boolean
  error: string | null

  // Filters
  genreFilter: string | null
  yearFilter: number | null
  sortBy: 'title' | 'year' | 'rating' | 'createdAt'
  sortOrder: 'asc' | 'desc'

  // Actions
  // Fetch operations
  fetchMovies: (page?: number, pageSize?: number) => Promise<void>
  fetchMovieDetails: (id: string) => Promise<Movie>
  searchMovies: (query: string, page?: number, pageSize?: number) => Promise<void>
  fetchMoviesByGenre: (genre: string, page?: number, pageSize?: number) => Promise<void>
  fetchPopularMovies: (page?: number, pageSize?: number) => Promise<void>
  fetchTopRatedMovies: (page?: number, pageSize?: number) => Promise<void>

  // CRUD operations
  createMovie: (movie: Omit<Movie, 'id'>) => Promise<Movie>
  updateMovie: (id: string, updates: Partial<Movie>) => Promise<Movie>
  deleteMovie: (id: string) => Promise<void>

  // Selection
  selectMovie: (movie: Movie | null) => void
  getMovieById: (id: string) => Movie | undefined

  // Filters
  setGenreFilter: (genre: string | null) => void
  setYearFilter: (year: number | null) => void
  setSortBy: (sort: 'title' | 'year' | 'rating' | 'createdAt') => void
  setSortOrder: (order: 'asc' | 'desc') => void
  clearFilters: () => void

  // Local state management
  addMovie: (movie: Movie) => void
  removeMovie: (id: string) => void
  updateLocalMovie: (id: string, updates: Partial<Movie>) => void
}

export const useMovieStore = create<MovieState>()(
  persist(
    (set, get) => ({
      // Movie state
      movies: [],
      selectedMovie: null,
      totalMovies: 0,
      currentPage: 1,
      pageSize: 20,
      isLoading: false,
      error: null,

      // Filters
      genreFilter: null,
      yearFilter: null,
      sortBy: 'title',
      sortOrder: 'asc',

      // Fetch operations
      fetchMovies: async (page = 1, pageSize = 20) => {
        try {
          set({ isLoading: true, error: null })
          const response = await movieService.getMovies(page, pageSize)
          set({
            movies: response.items,
            totalMovies: response.total,
            currentPage: page,
            pageSize,
          })
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to fetch movies' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      fetchMovieDetails: async (id) => {
        try {
          set({ isLoading: true, error: null })
          const movie = await movieService.getMovieDetails(id)
          set({ selectedMovie: movie })
          return movie
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to fetch movie details' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      searchMovies: async (query, page = 1, pageSize = 20) => {
        try {
          set({ isLoading: true, error: null })
          const response = await movieService.searchMovies(query, page, pageSize)
          set({
            movies: response.items,
            totalMovies: response.total,
            currentPage: page,
            pageSize,
          })
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Search failed' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      fetchMoviesByGenre: async (genre, page = 1, pageSize = 20) => {
        try {
          set({ isLoading: true, error: null })
          const response = await movieService.getMoviesByGenre(genre, page, pageSize)
          set({
            movies: response.items,
            totalMovies: response.total,
            currentPage: page,
            pageSize,
            genreFilter: genre,
          })
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to fetch movies by genre' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      fetchPopularMovies: async (page = 1, pageSize = 20) => {
        try {
          set({ isLoading: true, error: null })
          const response = await movieService.getPopularMovies(page, pageSize)
          set({
            movies: response.items,
            totalMovies: response.total,
            currentPage: page,
            pageSize,
          })
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to fetch popular movies' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      fetchTopRatedMovies: async (page = 1, pageSize = 20) => {
        try {
          set({ isLoading: true, error: null })
          const response = await movieService.getTopRatedMovies(page, pageSize)
          set({
            movies: response.items,
            totalMovies: response.total,
            currentPage: page,
            pageSize,
          })
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to fetch top rated movies' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },

      // CRUD operations
      createMovie: async (movie) => {
        try {
          set({ isLoading: true, error: null })
          const created = await movieService.createMovie(movie)
          set((state) => ({
            movies: [created, ...state.movies],
            totalMovies: state.totalMovies + 1,
          }))
          return created
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to create movie' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      updateMovie: async (id, updates) => {
        try {
          set({ isLoading: true, error: null })
          const updated = await movieService.updateMovie(id, updates)
          set((state) => ({
            movies: state.movies.map((m) => (m.id === id ? updated : m)),
            selectedMovie: state.selectedMovie?.id === id ? updated : state.selectedMovie,
          }))
          return updated
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to update movie' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      deleteMovie: async (id) => {
        try {
          set({ isLoading: true, error: null })
          await movieService.deleteMovie(id)
          set((state) => ({
            movies: state.movies.filter((m) => m.id !== id),
            totalMovies: state.totalMovies - 1,
            selectedMovie: state.selectedMovie?.id === id ? null : state.selectedMovie,
          }))
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to delete movie' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },

      // Selection
      selectMovie: (movie) => set({ selectedMovie: movie }),
      getMovieById: (id) => get().movies.find((m) => m.id === id),

      // Filters
      setGenreFilter: (genre) => set({ genreFilter: genre }),
      setYearFilter: (year) => set({ yearFilter: year }),
      setSortBy: (sort) => set({ sortBy: sort }),
      setSortOrder: (order) => set({ sortOrder: order }),
      clearFilters: () => set({ genreFilter: null, yearFilter: null }),

      // Local state management
      addMovie: (movie) =>
        set((state) => ({
          movies: [movie, ...state.movies],
          totalMovies: state.totalMovies + 1,
        })),
      removeMovie: (id) =>
        set((state) => ({
          movies: state.movies.filter((m) => m.id !== id),
          totalMovies: state.totalMovies - 1,
        })),
      updateLocalMovie: (id, updates) =>
        set((state) => ({
          movies: state.movies.map((m) => (m.id === id ? { ...m, ...updates } : m)),
          selectedMovie:
            state.selectedMovie?.id === id
              ? { ...state.selectedMovie, ...updates }
              : state.selectedMovie,
        })),
    }),
    {
      name: 'movie-store',
      partialize: (state) => ({
        genreFilter: state.genreFilter,
        yearFilter: state.yearFilter,
        sortBy: state.sortBy,
        sortOrder: state.sortOrder,
      }),
    }
  )
)
