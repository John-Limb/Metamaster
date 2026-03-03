import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { TVShow } from '@/types'
import { tvShowService } from '@/services/tvShowService'

interface TVShowState {
  // TV Show state
  tvShows: TVShow[]
  selectedTVShow: TVShow | null
  totalTVShows: number
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
  fetchTVShows: (page?: number, pageSize?: number) => Promise<void>
  fetchTVShowDetails: (id: string) => Promise<TVShow>
  searchTVShows: (query: string, page?: number, pageSize?: number) => Promise<void>
  fetchTVShowsByGenre: (genre: string, page?: number, pageSize?: number) => Promise<void>
  fetchPopularTVShows: (page?: number, pageSize?: number) => Promise<void>
  fetchTopRatedTVShows: (page?: number, pageSize?: number) => Promise<void>

  // CRUD operations
  createTVShow: (tvShow: Omit<TVShow, 'id'>) => Promise<TVShow>
  updateTVShow: (id: string, updates: Partial<TVShow>) => Promise<TVShow>
  deleteTVShow: (id: string) => Promise<void>

  // Selection
  selectTVShow: (tvShow: TVShow | null) => void
  getTVShowById: (id: string) => TVShow | undefined

  // Filters
  setGenreFilter: (genre: string | null) => void
  setYearFilter: (year: number | null) => void
  setSortBy: (sort: 'title' | 'year' | 'rating' | 'createdAt') => void
  setSortOrder: (order: 'asc' | 'desc') => void
  clearFilters: () => void

  // Local state management
  addTVShow: (tvShow: TVShow) => void
  removeTVShow: (id: string) => void
  updateLocalTVShow: (id: string, updates: Partial<TVShow>) => void
}

export const useTVShowStore = create<TVShowState>()(
  persist(
    (set, get) => ({
      // TV Show state
      tvShows: [],
      selectedTVShow: null,
      totalTVShows: 0,
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
      fetchTVShows: async (page = 1, pageSize = 20) => {
        try {
          set({ isLoading: true, error: null })
          const response = await tvShowService.getTVShows(page, pageSize)
          set({
            tvShows: response.items,
            totalTVShows: response.total,
            currentPage: page,
            pageSize,
          })
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to fetch TV shows' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      fetchTVShowDetails: async (id) => {
        try {
          set({ isLoading: true, error: null })
          const tvShow = await tvShowService.getTVShowDetails(id)
          set({ selectedTVShow: tvShow })
          return tvShow
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to fetch TV show details' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      searchTVShows: async (query, page = 1, pageSize = 20) => {
        try {
          set({ isLoading: true, error: null })
          const response = await tvShowService.searchTVShows(query, page, pageSize)
          set({
            tvShows: response.items,
            totalTVShows: response.total,
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
      fetchTVShowsByGenre: async (genre, page = 1, pageSize = 20) => {
        try {
          set({ isLoading: true, error: null })
          const response = await tvShowService.getTVShowsByGenre(genre, page, pageSize)
          set({
            tvShows: response.items,
            totalTVShows: response.total,
            currentPage: page,
            pageSize,
            genreFilter: genre,
          })
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to fetch TV shows by genre' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      fetchPopularTVShows: async (page = 1, pageSize = 20) => {
        try {
          set({ isLoading: true, error: null })
          const response = await tvShowService.getPopularTVShows(page, pageSize)
          set({
            tvShows: response.items,
            totalTVShows: response.total,
            currentPage: page,
            pageSize,
          })
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to fetch popular TV shows' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      fetchTopRatedTVShows: async (page = 1, pageSize = 20) => {
        try {
          set({ isLoading: true, error: null })
          const response = await tvShowService.getTopRatedTVShows(page, pageSize)
          set({
            tvShows: response.items,
            totalTVShows: response.total,
            currentPage: page,
            pageSize,
          })
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to fetch top rated TV shows' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },

      // CRUD operations
      createTVShow: async (tvShow) => {
        try {
          set({ isLoading: true, error: null })
          const created = await tvShowService.createTVShow(tvShow)
          set((state) => ({
            tvShows: [created, ...state.tvShows],
            totalTVShows: state.totalTVShows + 1,
          }))
          return created
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to create TV show' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      updateTVShow: async (id, updates) => {
        try {
          set({ isLoading: true, error: null })
          const updated = await tvShowService.updateTVShow(id, updates)
          set((state) => ({
            tvShows: state.tvShows.map((t) => (t.id === id ? updated : t)),
            selectedTVShow:
              state.selectedTVShow?.id === id ? updated : state.selectedTVShow,
          }))
          return updated
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to update TV show' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      deleteTVShow: async (id) => {
        try {
          set({ isLoading: true, error: null })
          await tvShowService.deleteTVShow(id)
          set((state) => ({
            tvShows: state.tvShows.filter((t) => t.id !== id),
            totalTVShows: state.totalTVShows - 1,
            selectedTVShow:
              state.selectedTVShow?.id === id ? null : state.selectedTVShow,
          }))
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to delete TV show' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },

      // Selection
      selectTVShow: (tvShow) => set({ selectedTVShow: tvShow }),
      getTVShowById: (id) => get().tvShows.find((t) => t.id === id),

      // Filters
      setGenreFilter: (genre) => set({ genreFilter: genre }),
      setYearFilter: (year) => set({ yearFilter: year }),
      setSortBy: (sort) => set({ sortBy: sort }),
      setSortOrder: (order) => set({ sortOrder: order }),
      clearFilters: () => set({ genreFilter: null, yearFilter: null }),

      // Local state management
      addTVShow: (tvShow) =>
        set((state) => ({
          tvShows: [tvShow, ...state.tvShows],
          totalTVShows: state.totalTVShows + 1,
        })),
      removeTVShow: (id) =>
        set((state) => ({
          tvShows: state.tvShows.filter((t) => t.id !== id),
          totalTVShows: state.totalTVShows - 1,
        })),
      updateLocalTVShow: (id, updates) =>
        set((state) => ({
          tvShows: state.tvShows.map((t) => (t.id === id ? { ...t, ...updates } : t)),
          selectedTVShow:
            state.selectedTVShow?.id === id
              ? { ...state.selectedTVShow, ...updates }
              : state.selectedTVShow,
        })),
    }),
    {
      name: 'tvshow-store',
      partialize: (state) => ({
        genreFilter: state.genreFilter,
        yearFilter: state.yearFilter,
        sortBy: state.sortBy,
        sortOrder: state.sortOrder,
      }),
    }
  )
)
