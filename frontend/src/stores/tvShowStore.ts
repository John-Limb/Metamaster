import type { TVShow } from '@/types'
import { tvShowService } from '@/services/tvShowService'
import { createMediaStore } from './createMediaStore'

const useTVShowStoreBase = createMediaStore<TVShow>(
  {
    getItems: (page, pageSize) => tvShowService.getTVShows(page, pageSize),
    getItemDetails: (id) => tvShowService.getTVShowDetails(id),
    searchItems: (query, page, pageSize) => tvShowService.searchTVShows(query, page, pageSize),
    getItemsByGenre: (genre, page, pageSize) => tvShowService.getTVShowsByGenre(genre, page, pageSize),
    getPopularItems: (page, pageSize) => tvShowService.getPopularTVShows(page, pageSize),
    getTopRatedItems: (page, pageSize) => tvShowService.getTopRatedTVShows(page, pageSize),
    createItem: (tvShow) => tvShowService.createTVShow(tvShow),
    updateItem: (id, updates) => tvShowService.updateTVShow(id, updates),
    deleteItem: (id) => tvShowService.deleteTVShow(id),
  },
  'tvshow-store',
)

export const useTVShowStore = () => {
  const s = useTVShowStoreBase()
  return {
    tvShows: s.items,
    selectedTVShow: s.selectedItem,
    totalTVShows: s.total,
    currentPage: s.currentPage,
    pageSize: s.pageSize,
    isLoading: s.isLoading,
    error: s.error,
    genreFilter: s.genreFilter,
    yearFilter: s.yearFilter,
    sortBy: s.sortBy,
    sortOrder: s.sortOrder,
    fetchTVShows: s.fetchItems,
    fetchTVShowDetails: s.fetchItemDetails,
    searchTVShows: s.searchItems,
    fetchTVShowsByGenre: s.fetchItemsByGenre,
    fetchPopularTVShows: s.fetchPopularItems,
    fetchTopRatedTVShows: s.fetchTopRatedItems,
    createTVShow: s.createItem,
    updateTVShow: s.updateItem,
    deleteTVShow: s.deleteItem,
    selectTVShow: s.selectItem,
    getTVShowById: s.getById,
    setGenreFilter: s.setGenreFilter,
    setYearFilter: s.setYearFilter,
    setSortBy: s.setSortBy,
    setSortOrder: s.setSortOrder,
    clearFilters: s.clearFilters,
    addTVShow: s.addItem,
    removeTVShow: s.removeItem,
    updateLocalTVShow: s.updateLocalItem,
  }
}
