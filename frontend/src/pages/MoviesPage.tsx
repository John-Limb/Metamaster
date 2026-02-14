import React, { useEffect } from 'react'
import { FaFilter, FaSort } from 'react-icons/fa'
import { useMovieStore } from '@/stores/movieStore'

export const MoviesPage: React.FC = () => {
  const {
    movies,
    totalMovies,
    currentPage,
    pageSize,
    isLoading,
    error,
    sortBy,
    setSortBy,
    fetchMovies,
  } = useMovieStore()

  useEffect(() => {
    fetchMovies(1, 20)
  }, [fetchMovies])

  const handleSortChange = (value: string) => {
    setSortBy(value as 'title' | 'year' | 'rating' | 'createdAt')
    fetchMovies(1, pageSize)
  }

  const totalPages = Math.ceil(totalMovies / pageSize)

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Movies</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Browse and manage your movie collection
          {totalMovies > 0 && ` — ${totalMovies} movie${totalMovies !== 1 ? 's' : ''}`}
        </p>
      </div>

      {/* Filters and Sort */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md p-4 flex flex-col sm:flex-row gap-4">
        <div className="flex-1 flex gap-2">
          <button className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-slate-600 transition">
            <FaFilter className="w-4 h-4" />
            Filters
          </button>
          <select
            value={sortBy}
            onChange={(e) => handleSortChange(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="title">Sort by Title</option>
            <option value="year">Sort by Year</option>
            <option value="rating">Sort by Rating</option>
            <option value="createdAt">Sort by Added Date</option>
          </select>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition">
          <FaSort className="w-4 h-4" />
          View Options
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-700 dark:text-red-400">{error}</p>
          <button
            onClick={() => fetchMovies(currentPage, pageSize)}
            className="mt-2 text-sm text-red-600 dark:text-red-400 underline hover:no-underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Loading state */}
      {isLoading && movies.length === 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="bg-white dark:bg-slate-800 rounded-lg shadow-md overflow-hidden animate-pulse">
              <div className="aspect-video bg-gray-200 dark:bg-slate-700" />
              <div className="p-4 space-y-2">
                <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded w-3/4" />
                <div className="h-3 bg-gray-200 dark:bg-slate-700 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Movies Grid */}
      {!isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {movies.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <p className="text-gray-500 dark:text-gray-400 text-lg">No movies found</p>
              <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">
                Start by scanning your media library
              </p>
            </div>
          ) : (
            movies.map((movie) => (
              <div
                key={movie.id}
                className="bg-white dark:bg-slate-800 rounded-lg shadow-md overflow-hidden hover:shadow-lg transition"
              >
                <div className="aspect-video bg-gray-200 dark:bg-slate-700 flex items-center justify-center">
                  {movie.posterUrl ? (
                    <img
                      src={movie.posterUrl}
                      alt={movie.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <svg
                      className="w-12 h-12 text-gray-400 dark:text-slate-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"
                      />
                    </svg>
                  )}
                </div>
                <div className="p-4">
                  <h3 className="font-semibold text-gray-900 dark:text-white truncate">
                    {movie.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {movie.year ?? 'Unknown year'}
                    {movie.rating != null && ` · ${movie.rating.toFixed(1)}`}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => fetchMovies(currentPage - 1, pageSize)}
            disabled={currentPage <= 1 || isLoading}
            className="px-4 py-2 rounded-lg border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-gray-600 dark:text-gray-400">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => fetchMovies(currentPage + 1, pageSize)}
            disabled={currentPage >= totalPages || isLoading}
            className="px-4 py-2 rounded-lg border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
