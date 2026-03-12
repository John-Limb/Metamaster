import React, { useState, useCallback, useEffect } from 'react'
import { TextInput, Button, Pagination, EmptyState, SkeletonCard } from '@/components/common'
import { FilterPanel, type FilterSection } from '@/components/features/filter'
import { SortDropdown, type SortOption } from '@/components/features/sort'
import { TVShowCard } from '../TVShowCard'
import { MediaDetailModal } from '@/components/features/media'
import { useTVShowStore } from '@/stores/tvShowStore'
import { usePlexStore } from '@/stores/plexStore'
import { tvShowService } from '@/services/tvShowService'
import './TVShowsPage.css'

const TVShowsPage: React.FC = () => {
  const {
    tvShows,
    totalTVShows,
    currentPage,
    isLoading,
    error,
    fetchTVShows,
  } = useTVShowStore()

  const { mismatches, resolveMismatch } = usePlexStore()

  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({})
  const [sortValue, setSortValue] = useState('name-asc')
  const [isScanning, setIsScanning] = useState(false)
  const [scanResult, setScanResult] = useState<string | null>(null)
  const [modalShowId, setModalShowId] = useState<string | null>(null)
  const itemsPerPage = 12

  // Fetch TV shows on mount
  useEffect(() => {
    fetchTVShows(1, itemsPerPage)
  }, [fetchTVShows])

  const totalPages = Math.ceil(totalTVShows / itemsPerPage)

  // Filter sections
  const filterSections: FilterSection[] = [
    {
      id: 'genre',
      label: 'Genre',
      options: [
        { value: 'action', label: 'Action', count: 0 },
        { value: 'comedy', label: 'Comedy', count: 0 },
        { value: 'drama', label: 'Drama', count: 0 },
        { value: 'horror', label: 'Horror', count: 0 },
        { value: 'sci-fi', label: 'Sci-Fi', count: 0 },
        { value: 'thriller', label: 'Thriller', count: 0 },
      ],
      multiSelect: true,
    },
    {
      id: 'status',
      label: 'Status',
      options: [
        { value: 'continuing', label: 'Continuing', count: 0 },
        { value: 'ended', label: 'Ended', count: 0 },
      ],
      multiSelect: true,
    },
    {
      id: 'rating',
      label: 'Rating',
      options: [
        { value: '5', label: '5 Stars', count: 0 },
        { value: '4', label: '4+ Stars', count: 0 },
        { value: '3', label: '3+ Stars', count: 0 },
      ],
      multiSelect: false,
    },
  ]

  // Sort options
  const sortOptions: SortOption[] = [
    { value: 'name-asc', label: 'Name', direction: 'asc' },
    { value: 'name-desc', label: 'Name', direction: 'desc' },
    { value: 'rating-asc', label: 'Rating', direction: 'asc' },
    { value: 'rating-desc', label: 'Rating', direction: 'desc' },
  ]

  // Handle filter change
  const handleFilterChange = useCallback((sectionId: string, values: string[]) => {
    setSelectedFilters((prev) => ({
      ...prev,
      [sectionId]: values,
    }))
  }, [])

  // Handle clear all filters
  const handleClearFilters = useCallback(() => {
    setSelectedFilters({})
  }, [])

  // Handle page change
  const handlePageChange = useCallback((page: number) => {
    fetchTVShows(page, itemsPerPage)
  }, [fetchTVShows])

  // Handle TV show click — open modal
  const handleShowClick = useCallback((showId: string) => {
    setModalShowId(showId)
  }, [])

  // Handle add to queue
  const handleAddToQueue = useCallback((showId: string) => {
    console.log('Add to queue:', showId)
  }, [])

  // Handle edit
  const handleEdit = useCallback((showId: string) => {
    console.log('Edit:', showId)
  }, [])

  // Handle delete
  const handleDelete = useCallback((showId: string) => {
    console.log('Delete:', showId)
  }, [])

  // Handle scan directory
  const handleScanDirectory = useCallback(async () => {
    setIsScanning(true)
    setScanResult(null)
    try {
      const result = await tvShowService.scanDirectory()
      setScanResult(
        `Scan complete: ${result.files_synced} file(s) synced, ${result.shows_created} episode(s) created`
      )
      fetchTVShows(1, itemsPerPage)
    } catch {
      setScanResult('Scan failed. Check the server logs for details.')
    } finally {
      setIsScanning(false)
      setTimeout(() => setScanResult(null), 5000)
    }
  }, [fetchTVShows])

  return (
    <div className="tvshows-page">
      <header className="tvshows-page__header">
        <div className="tvshows-page__title-section">
          <h1 className="tvshows-page__title">TV Shows</h1>
          <p className="tvshows-page__subtitle">
            {isLoading
              ? 'Loading...'
              : totalTVShows > 0
                ? `${totalTVShows} show${totalTVShows !== 1 ? 's' : ''} in your library`
                : 'No TV shows found'}
          </p>
        </div>

        <div className="tvshows-page__search">
          <TextInput
            placeholder="Search TV shows..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            leftIcon={
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
              </svg>
            }
          />
        </div>
      </header>

      <div className="tvshows-page__toolbar">
        <div className="tvshows-page__toolbar-left">
          <FilterPanel
            sections={filterSections}
            selectedFilters={selectedFilters}
            onFilterChange={handleFilterChange}
            onClearAll={handleClearFilters}
            isOpen={isFilterOpen}
            onToggle={() => setIsFilterOpen(!isFilterOpen)}
          />
          <SortDropdown
            options={sortOptions}
            value={sortValue}
            onChange={setSortValue}
          />
        </div>

        <div className="tvshows-page__toolbar-right">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleScanDirectory}
            disabled={isScanning}
          >
            {isScanning ? 'Scanning...' : 'Scan Now'}
          </Button>
          <div className="tvshows-page__view-toggle" role="group" aria-label="View mode">
            <Button
              variant={viewMode === 'grid' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setViewMode('grid')}
              aria-pressed={viewMode === 'grid'}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <rect x="3" y="3" width="7" height="7" />
                <rect x="14" y="3" width="7" height="7" />
                <rect x="14" y="14" width="7" height="7" />
                <rect x="3" y="14" width="7" height="7" />
              </svg>
            </Button>
            <Button
              variant={viewMode === 'list' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setViewMode('list')}
              aria-pressed={viewMode === 'list'}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <line x1="8" y1="6" x2="21" y2="6" />
                <line x1="8" y1="12" x2="21" y2="12" />
                <line x1="8" y1="18" x2="21" y2="18" />
                <line x1="3" y1="6" x2="3.01" y2="6" />
                <line x1="3" y1="12" x2="3.01" y2="12" />
                <line x1="3" y1="18" x2="3.01" y2="18" />
              </svg>
            </Button>
          </div>
        </div>
      </div>

      <main className="tvshows-page__content">
        {scanResult && (
          <div className="p-4 mb-4 text-green-700 bg-green-50 dark:bg-green-900/20 dark:text-green-400 rounded-lg border border-green-200 dark:border-green-800">
            <p>{scanResult}</p>
          </div>
        )}

        {error && (
          <div className="p-4 mb-4 text-red-700 bg-red-50 dark:bg-red-900/20 dark:text-red-400 rounded-lg border border-red-200 dark:border-red-800">
            <p>{error}</p>
            <button
              onClick={() => fetchTVShows(currentPage, itemsPerPage)}
              className="mt-2 text-sm underline hover:no-underline"
            >
              Try again
            </button>
          </div>
        )}

        {isLoading ? (
          <div className={`tvshows-page__grid tvshows-page__grid--${viewMode}`}>
            {Array.from({ length: itemsPerPage }).map((_, index) => (
              <SkeletonCard key={index} />
            ))}
          </div>
        ) : tvShows.length === 0 ? (
          <EmptyState
            variant="empty"
            title="No TV shows found"
            description="Your TV show library will appear here once media files are synced from your TV directory."
            action={{
              label: 'Clear filters',
              onClick: handleClearFilters,
            }}
          />
        ) : (
          <>
            <div className={`tvshows-page__grid tvshows-page__grid--${viewMode}`}>
              {tvShows.map((show) => {
                const showMismatch = mismatches.find(
                  (m) => m.item_type === 'tv_show' && m.item_id === Number(show.id)
                )
                return (
                  <TVShowCard
                    key={show.id}
                    id={String(show.id)}
                    title={show.title}
                    rating={show.rating}
                    poster_url={show.poster_url}
                    genres={show.genre}
                    seasons={show.seasons}
                    episodes={show.episodes}
                    mismatch={showMismatch}
                    ourTmdbId={show.tmdb_id ?? ''}
                    onResolve={resolveMismatch}
                    onClick={() => handleShowClick(String(show.id))}
                    onAddToQueue={() => handleAddToQueue(String(show.id))}
                    onEdit={() => handleEdit(String(show.id))}
                    onDelete={() => handleDelete(String(show.id))}
                  />
                )
              })}
            </div>

            {totalPages > 1 && (
              <div className="tvshows-page__pagination">
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                />
              </div>
            )}
          </>
        )}
      </main>

      <MediaDetailModal
        isOpen={modalShowId !== null}
        mediaType="tv_show"
        mediaId={modalShowId || ''}
        onClose={() => setModalShowId(null)}
        onMetadataSynced={() => fetchTVShows(currentPage, itemsPerPage)}
      />
    </div>
  )
}

export default TVShowsPage
