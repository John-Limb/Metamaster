import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { SearchFilters, SearchResult, PaginatedResponse } from '@/types'
import { searchService } from '@/services/searchService'

interface SavedSearch {
  id: string
  name: string
  filters: SearchFilters
  createdAt: string
}

interface SearchState {
  // Search state
  query: string
  filters: SearchFilters
  results: SearchResult[]
  totalResults: number
  currentPage: number
  pageSize: number
  isSearching: boolean
  error: string | null

  // Suggestions
  suggestions: string[]
  isLoadingSuggestions: boolean

  // Saved searches
  savedSearches: SavedSearch[]
  recentSearches: string[]

  // Actions
  setQuery: (query: string) => void
  setFilters: (filters: SearchFilters) => void
  clearFilters: () => void

  // Search operations
  search: (page?: number, pageSize?: number) => Promise<void>
  loadMore: () => Promise<void>

  // Suggestions
  fetchSuggestions: (query: string) => Promise<void>
  clearSuggestions: () => void

  // Saved searches
  saveSearch: (name: string) => void
  loadSearch: (id: string) => void
  deleteSavedSearch: (id: string) => void
  getSavedSearch: (id: string) => SavedSearch | undefined

  // Recent searches
  addRecentSearch: (query: string) => void
  clearRecentSearches: () => void
  getRecentSearches: () => string[]
}

export const useSearchStore = create<SearchState>()(
  persist(
    (set, get) => ({
      // Search state
      query: '',
      filters: {},
      results: [],
      totalResults: 0,
      currentPage: 1,
      pageSize: 20,
      isSearching: false,
      error: null,

      // Suggestions
      suggestions: [],
      isLoadingSuggestions: false,

      // Saved searches
      savedSearches: [],
      recentSearches: [],

      // Actions
      setQuery: (query) => set({ query }),
      setFilters: (filters) => set({ filters }),
      clearFilters: () => set({ filters: {} }),

      // Search operations
      search: async (page = 1, pageSize = 20) => {
        try {
          set({ isSearching: true, error: null })
          const response = await searchService.search(
            { ...get().filters, query: get().query },
            page,
            pageSize
          )
          set({
            results: response.items,
            totalResults: response.total,
            currentPage: page,
            pageSize,
          })
          if (page === 1) {
            get().addRecentSearch(get().query)
          }
        } catch (error: any) {
          set({ error: error.message || 'Search failed' })
          throw error
        } finally {
          set({ isSearching: false })
        }
      },
      loadMore: async () => {
        const { currentPage, totalResults, pageSize, query, filters } = get()
        const nextPage = currentPage + 1
        if (nextPage * pageSize > totalResults) return

        try {
          set({ isSearching: true, error: null })
          const response = await searchService.search({ ...filters, query }, nextPage, pageSize)
          set({
            results: [...get().results, ...response.items],
            currentPage: nextPage,
          })
        } catch (error: any) {
          set({ error: error.message || 'Failed to load more results' })
          throw error
        } finally {
          set({ isSearching: false })
        }
      },

      // Suggestions
      fetchSuggestions: async (query) => {
        try {
          set({ isLoadingSuggestions: true })
          const suggestions = await searchService.getSuggestions(query)
          set({ suggestions })
        } catch (error: any) {
          set({ suggestions: [] })
        } finally {
          set({ isLoadingSuggestions: false })
        }
      },
      clearSuggestions: () => set({ suggestions: [] }),

      // Saved searches
      saveSearch: (name) => {
        const newSearch: SavedSearch = {
          id: `saved-${Date.now()}`,
          name,
          filters: { ...get().filters, query: get().query },
          createdAt: new Date().toISOString(),
        }
        set((state) => ({
          savedSearches: [newSearch, ...state.savedSearches],
        }))
      },
      loadSearch: (id) => {
        const search = get().savedSearches.find((s) => s.id === id)
        if (search) {
          set({
            query: search.filters.query || '',
            filters: search.filters,
          })
        }
      },
      deleteSavedSearch: (id) =>
        set((state) => ({
          savedSearches: state.savedSearches.filter((s) => s.id !== id),
        })),
      getSavedSearch: (id) => get().savedSearches.find((s) => s.id === id),

      // Recent searches
      addRecentSearch: (query) => {
        if (!query.trim()) return
        set((state) => {
          const filtered = state.recentSearches.filter((s) => s !== query)
          return {
            recentSearches: [query, ...filtered].slice(0, 10),
          }
        })
      },
      clearRecentSearches: () => set({ recentSearches: [] }),
      getRecentSearches: () => get().recentSearches,
    }),
    {
      name: 'search-store',
      partialize: (state) => ({
        savedSearches: state.savedSearches,
        recentSearches: state.recentSearches,
      }),
    }
  )
)
