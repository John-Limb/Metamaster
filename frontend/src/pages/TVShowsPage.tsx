import React, { useEffect, useState } from 'react'
import { FaFilter, FaSort } from 'react-icons/fa'
import { useTVShowStore } from '@/stores/tvShowStore'
import { MediaDetailModal } from '@/components/features/media'

export const TVShowsPage: React.FC = () => {
  const {
    tvShows,
    totalTVShows,
    currentPage,
    pageSize,
    isLoading,
    error,
    sortBy,
    setSortBy,
    fetchTVShows,
  } = useTVShowStore()

  const [modalShowId, setModalShowId] = useState<string | null>(null)

  useEffect(() => {
    fetchTVShows(1, 20)
  }, [fetchTVShows])

  const handleSortChange = (value: string) => {
    setSortBy(value as 'title' | 'year' | 'rating' | 'createdAt')
    fetchTVShows(1, pageSize)
  }

  const totalPages = Math.ceil(totalTVShows / pageSize)

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-body mb-2">TV Shows</h1>
        <p className="text-dim">
          Browse and manage your TV show collection
          {totalTVShows > 0 && ` — ${totalTVShows} show${totalTVShows !== 1 ? 's' : ''}`}
        </p>
      </div>

      {/* Filters and Sort */}
      <div className="bg-card rounded-lg shadow-md p-4 flex flex-col sm:flex-row gap-4">
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
            onClick={() => fetchTVShows(currentPage, pageSize)}
            className="mt-2 text-sm text-red-600 dark:text-red-400 underline hover:no-underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Loading state */}
      {isLoading && tvShows.length === 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="bg-card rounded-lg shadow-md overflow-hidden animate-pulse">
              <div className="aspect-[2/3] bg-gray-200 dark:bg-slate-700" />
              <div className="p-4 space-y-2">
                <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded w-3/4" />
                <div className="h-3 bg-gray-200 dark:bg-slate-700 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TV Shows Grid */}
      {!isLoading && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
          {tvShows.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <p className="text-hint text-lg">No TV shows found</p>
              <p className="text-hint text-sm mt-2">
                Start by scanning your media library
              </p>
            </div>
          ) : (
            tvShows.map((show) => (
              <div
                key={show.id}
                onClick={() => setModalShowId(String(show.id))}
                className="group bg-card rounded-lg shadow-md overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all duration-200 cursor-pointer"
              >
                <div className="relative aspect-[2/3] bg-gray-200 dark:bg-slate-700 flex items-center justify-center overflow-hidden">
                  {show.poster_url ? (
                    <img
                      src={show.poster_url}
                      alt={show.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      loading="lazy"
                    />
                  ) : (
                    <div className="flex flex-col items-center gap-2 text-hint">
                      <svg
                        className="w-12 h-12"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"
                        />
                      </svg>
                      <span className="text-xs">No poster</span>
                    </div>
                  )}

                  {/* Rating badge */}
                  {show.rating != null && (
                    <div className="absolute top-2 left-2 flex items-center gap-1 px-2 py-1 bg-black/60 backdrop-blur-sm rounded-full">
                      <span className="text-amber-400 text-xs">★</span>
                      <span className="text-white text-xs font-medium">{show.rating.toFixed(1)}</span>
                    </div>
                  )}

                  {/* Status badge */}
                  {show.status && (
                    <span className={`absolute top-2 right-2 px-2 py-0.5 text-white text-xs font-medium rounded-full ${
                      show.status.toLowerCase() === 'ended'
                        ? 'bg-gray-500/90'
                        : 'bg-green-600/90'
                    }`}>
                      {show.status}
                    </span>
                  )}
                </div>
                <div className="p-3">
                  <h3 className="font-semibold text-body truncate text-sm">
                    {show.title}
                  </h3>
                  <p className="text-xs text-hint mt-1">
                    {show.seasons != null && show.seasons > 0 && `${show.seasons} Season${show.seasons !== 1 ? 's' : ''}`}
                    {show.episodes != null && show.episodes > 0 && ` · ${show.episodes} Episodes`}
                    {show.genre && show.genre.length > 0 && ` · ${show.genre.slice(0, 2).join(', ')}`}
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
            onClick={() => fetchTVShows(currentPage - 1, pageSize)}
            disabled={currentPage <= 1 || isLoading}
            className="px-4 py-2 rounded-lg border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-dim">
            Page {currentPage} of {totalPages}
          </span>
          <button
            onClick={() => fetchTVShows(currentPage + 1, pageSize)}
            disabled={currentPage >= totalPages || isLoading}
            className="px-4 py-2 rounded-lg border border-gray-300 dark:border-slate-600 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Next
          </button>
        </div>
      )}

      {/* Detail Modal */}
      <MediaDetailModal
        isOpen={modalShowId !== null}
        mediaType="tv_show"
        mediaId={modalShowId || ''}
        onClose={() => setModalShowId(null)}
        onMetadataSynced={() => fetchTVShows(currentPage, pageSize)}
      />
    </div>
  )
}
