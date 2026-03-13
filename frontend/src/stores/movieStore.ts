import type { Movie } from '@/types'
import { movieService } from '@/services/movieService'
import { createMediaStore } from './createMediaStore'

const useMovieStoreBase = createMediaStore<Movie>(
  {
    getItems: (page, pageSize) => movieService.getMovies(page, pageSize),
    getItemDetails: (id) => movieService.getMovieDetails(id),
    searchItems: (query, page, pageSize) => movieService.searchMovies(query, page, pageSize),
    getItemsByGenre: (genre, page, pageSize) => movieService.getMoviesByGenre(genre, page, pageSize),
    getPopularItems: (page, pageSize) => movieService.getPopularMovies(page, pageSize),
    getTopRatedItems: (page, pageSize) => movieService.getTopRatedMovies(page, pageSize),
    createItem: (movie) => movieService.createMovie(movie),
    updateItem: (id, updates) => movieService.updateMovie(id, updates),
    deleteItem: (id) => movieService.deleteMovie(id),
  },
  'movie-store',
)

export const useMovieStore = () => {
  const s = useMovieStoreBase()
  return {
    movies: s.items,
    selectedMovie: s.selectedItem,
    totalMovies: s.total,
    currentPage: s.currentPage,
    pageSize: s.pageSize,
    isLoading: s.isLoading,
    error: s.error,
    genreFilter: s.genreFilter,
    yearFilter: s.yearFilter,
    sortBy: s.sortBy,
    sortOrder: s.sortOrder,
    fetchMovies: s.fetchItems,
    fetchMovieDetails: s.fetchItemDetails,
    searchMovies: s.searchItems,
    fetchMoviesByGenre: s.fetchItemsByGenre,
    fetchPopularMovies: s.fetchPopularItems,
    fetchTopRatedMovies: s.fetchTopRatedItems,
    createMovie: s.createItem,
    updateMovie: s.updateItem,
    deleteMovie: s.deleteItem,
    selectMovie: s.selectItem,
    getMovieById: s.getById,
    setGenreFilter: s.setGenreFilter,
    setYearFilter: s.setYearFilter,
    setSortBy: s.setSortBy,
    setSortOrder: s.setSortOrder,
    clearFilters: s.clearFilters,
    addMovie: s.addItem,
    removeMovie: s.removeItem,
    updateLocalMovie: s.updateLocalItem,
  }
}
