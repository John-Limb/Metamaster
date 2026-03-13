import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { PaginatedResponse } from '@/types'

export interface MediaStoreService<T> {
  getItems: (page: number, pageSize: number) => Promise<PaginatedResponse<T>>
  getItemDetails: (id: string) => Promise<T>
  searchItems: (query: string, page: number, pageSize: number) => Promise<PaginatedResponse<T>>
  getItemsByGenre: (genre: string, page: number, pageSize: number) => Promise<PaginatedResponse<T>>
  getPopularItems: (page: number, pageSize: number) => Promise<PaginatedResponse<T>>
  getTopRatedItems: (page: number, pageSize: number) => Promise<PaginatedResponse<T>>
  createItem: (item: Omit<T, 'id'>) => Promise<T>
  updateItem: (id: string, updates: Partial<T>) => Promise<T>
  deleteItem: (id: string) => Promise<unknown>
}

export interface MediaState<T extends { id: string }> {
  items: T[]
  selectedItem: T | null
  total: number
  currentPage: number
  pageSize: number
  isLoading: boolean
  error: string | null
  genreFilter: string | null
  yearFilter: number | null
  sortBy: 'title' | 'year' | 'rating' | 'createdAt'
  sortOrder: 'asc' | 'desc'

  fetchItems: (page?: number, pageSize?: number) => Promise<void>
  fetchItemDetails: (id: string) => Promise<T>
  searchItems: (query: string, page?: number, pageSize?: number) => Promise<void>
  fetchItemsByGenre: (genre: string, page?: number, pageSize?: number) => Promise<void>
  fetchPopularItems: (page?: number, pageSize?: number) => Promise<void>
  fetchTopRatedItems: (page?: number, pageSize?: number) => Promise<void>
  createItem: (item: Omit<T, 'id'>) => Promise<T>
  updateItem: (id: string, updates: Partial<T>) => Promise<T>
  deleteItem: (id: string) => Promise<void>

  selectItem: (item: T | null) => void

  getById: (id: string) => T | undefined

  setGenreFilter: (genre: string | null) => void
  setYearFilter: (year: number | null) => void
  setSortBy: (sort: 'title' | 'year' | 'rating' | 'createdAt') => void
  setSortOrder: (order: 'asc' | 'desc') => void
  clearFilters: () => void

  addItem: (item: T) => void
  removeItem: (id: string) => void
  updateLocalItem: (id: string, updates: Partial<T>) => void
}

function errMsg(e: unknown, fallback: string): string {
  return e instanceof Error ? e.message : fallback
}

export function createMediaStore<T extends { id: string }>(
  service: MediaStoreService<T>,
  storeName: string,
) {
  return create<MediaState<T>>()(
    persist(
      (set, get) => ({
        items: [],
        selectedItem: null,
        total: 0,
        currentPage: 1,
        pageSize: 20,
        isLoading: false,
        error: null,
        genreFilter: null,
        yearFilter: null,
        sortBy: 'title',
        sortOrder: 'asc',

        fetchItems: async (page = 1, pageSize = 20) => {
          try {
            set({ isLoading: true, error: null })
            const res = await service.getItems(page, pageSize)
            set({ items: res.items, total: res.total, currentPage: page, pageSize })
          } catch (error: unknown) {
            set({ error: errMsg(error, 'Failed to fetch items') })
            throw error
          } finally {
            set({ isLoading: false })
          }
        },

        fetchItemDetails: async (id) => {
          try {
            set({ isLoading: true, error: null })
            const item = await service.getItemDetails(id)
            set({ selectedItem: item })
            return item
          } catch (error: unknown) {
            set({ error: errMsg(error, 'Failed to fetch item details') })
            throw error
          } finally {
            set({ isLoading: false })
          }
        },

        searchItems: async (query, page = 1, pageSize = 20) => {
          try {
            set({ isLoading: true, error: null })
            const res = await service.searchItems(query, page, pageSize)
            set({ items: res.items, total: res.total, currentPage: page, pageSize })
          } catch (error: unknown) {
            set({ error: errMsg(error, 'Search failed') })
            throw error
          } finally {
            set({ isLoading: false })
          }
        },

        fetchItemsByGenre: async (genre, page = 1, pageSize = 20) => {
          try {
            set({ isLoading: true, error: null })
            const res = await service.getItemsByGenre(genre, page, pageSize)
            set({ items: res.items, total: res.total, currentPage: page, pageSize, genreFilter: genre })
          } catch (error: unknown) {
            set({ error: errMsg(error, 'Failed to fetch items by genre') })
            throw error
          } finally {
            set({ isLoading: false })
          }
        },

        fetchPopularItems: async (page = 1, pageSize = 20) => {
          try {
            set({ isLoading: true, error: null })
            const res = await service.getPopularItems(page, pageSize)
            set({ items: res.items, total: res.total, currentPage: page, pageSize })
          } catch (error: unknown) {
            set({ error: errMsg(error, 'Failed to fetch popular items') })
            throw error
          } finally {
            set({ isLoading: false })
          }
        },

        fetchTopRatedItems: async (page = 1, pageSize = 20) => {
          try {
            set({ isLoading: true, error: null })
            const res = await service.getTopRatedItems(page, pageSize)
            set({ items: res.items, total: res.total, currentPage: page, pageSize })
          } catch (error: unknown) {
            set({ error: errMsg(error, 'Failed to fetch top rated items') })
            throw error
          } finally {
            set({ isLoading: false })
          }
        },

        createItem: async (item) => {
          try {
            set({ isLoading: true, error: null })
            const created = await service.createItem(item)
            set((state) => ({ items: [created, ...state.items], total: state.total + 1 }))
            return created
          } catch (error: unknown) {
            set({ error: errMsg(error, 'Failed to create item') })
            throw error
          } finally {
            set({ isLoading: false })
          }
        },

        updateItem: async (id, updates) => {
          try {
            set({ isLoading: true, error: null })
            const updated = await service.updateItem(id, updates)
            set((state) => ({
              items: state.items.map((i) => (i.id === id ? updated : i)),
              selectedItem: state.selectedItem?.id === id ? updated : state.selectedItem,
            }))
            return updated
          } catch (error: unknown) {
            set({ error: errMsg(error, 'Failed to update item') })
            throw error
          } finally {
            set({ isLoading: false })
          }
        },

        deleteItem: async (id) => {
          try {
            set({ isLoading: true, error: null })
            await service.deleteItem(id)
            set((state) => ({
              items: state.items.filter((i) => i.id !== id),
              total: state.total - 1,
              selectedItem: state.selectedItem?.id === id ? null : state.selectedItem,
            }))
          } catch (error: unknown) {
            set({ error: errMsg(error, 'Failed to delete item') })
            throw error
          } finally {
            set({ isLoading: false })
          }
        },

        selectItem: (item) => set({ selectedItem: item }),
        getById: (id) => get().items.find((i) => i.id === id),

        setGenreFilter: (genre) => set({ genreFilter: genre }),
        setYearFilter: (year) => set({ yearFilter: year }),
        setSortBy: (sort) => set({ sortBy: sort }),
        setSortOrder: (order) => set({ sortOrder: order }),
        clearFilters: () => set({ genreFilter: null, yearFilter: null }),

        addItem: (item) =>
          set((state) => ({ items: [item, ...state.items], total: state.total + 1 })),

        removeItem: (id) =>
          set((state) => ({
            items: state.items.filter((i) => i.id !== id),
            total: state.total - 1,
          })),

        updateLocalItem: (id, updates) =>
          set((state) => ({
            items: state.items.map((i) => (i.id === id ? { ...i, ...updates } : i)),
            selectedItem:
              state.selectedItem?.id === id
                ? { ...state.selectedItem, ...updates }
                : state.selectedItem,
          })),
      }),
      {
        name: storeName,
        partialize: (state) => ({
          genreFilter: state.genreFilter,
          yearFilter: state.yearFilter,
          sortBy: state.sortBy,
          sortOrder: state.sortOrder,
        }),
      },
    ),
  )
}
