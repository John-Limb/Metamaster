import React, { useState, useCallback, useEffect } from 'react'
import { TextInput, Button, Pagination, EmptyState, SkeletonCard } from '@/components/common'
import { FilterPanel, type FilterSection } from '@/components/features/filter'
import { SortDropdown, type SortOption } from '@/components/features/sort'
import { MovieCard } from '../MovieCard'
import { MediaDetailModal } from '@/components/features/media'
import { useMovieStore } from '@/stores/movieStore'
import { usePlexStore } from '@/stores/plexStore'
import { movieService } from '@/services/movieService'
import './MoviesPage.css'

const MoviesPage: React.FC = () => {
  const {
    movies,
    totalMovies,
    currentPage,
    isLoading,
    error,
    fetchMovies,
  } = useMovieStore()

  const { mismatches, resolveMismatch } = usePlexStore()

  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({})
  const [sortValue, setSortValue] = useState('title-asc')
  const [isScanning, setIsScanning] = useState(false)
  const [scanResult, setScanResult] = useState<string | null>(null)
  const [modalMovieId, setModalMovieId] = useState<string | null>(null)
  const itemsPerPage = 12

  // Fetch movies on mount
  useEffect(() => {
    fetchMovies(1, itemsPerPage)
  }, [fetchMovies])

  const totalPages = Math.ceil(totalMovies / itemsPerPage)

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
      id: 'year',
      label: 'Year',
      options: [
        { value: '2024', label: '2024', count: 0 },
        { value: '2023', label: '2023', count: 0 },
        { value: '2022', label: '2022', count: 0 },
        { value: '2021', label: '2021', count: 0 },
        { value: '2020', label: '2020', count: 0 },
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
    { value: 'title-asc', label: 'Title', direction: 'asc' },
    { value: 'title-desc', label: 'Title', direction: 'desc' },
    { value: 'year-asc', label: 'Year', direction: 'asc' },
    { value: 'year-desc', label: 'Year', direction: 'desc' },
    { value: 'rating-asc', label: 'Rating', direction: 'asc' },
    { value: 'rating-desc', label: 'Rating', direction: 'desc' },
    { value: 'date-added', label: 'Date Added' },
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
    fetchMovies(page, itemsPerPage)
  }, [fetchMovies])

  // Handle movie click — open modal
  const handleMovieClick = useCallback((movieId: string) => {
    setModalMovieId(movieId)
  }, [])

  // Handle add to queue
  const handleAddToQueue = useCallback((movieId: string) => {
    console.log('Add to queue:', movieId)
  }, [])

  // Handle edit
  const handleEdit = useCallback((movieId: string) => {
    console.log('Edit:', movieId)
  }, [])

  // Handle scan directory
  const handleScanDirectory = useCallback(async () => {
    setIsScanning(true)
    setScanResult(null)
    try {
      const result = await movieService.scanDirectory()
      setScanResult(
        `Scan complete: ${result.files_synced} file(s) synced, ${result.movies_created} movie(s) created`
      )
      fetchMovies(1, itemsPerPage)
    } catch {
      setScanResult('Scan failed. Check the server logs for details.')
    } finally {
      setIsScanning(false)
      setTimeout(() => setScanResult(null), 5000)
    }
  }, [fetchMovies])

  // Handle scan (FFprobe)
  const handleScan = useCallback(async (movieId: string) => {
    try {
      await movieService.scanMovie(movieId)
      fetchMovies(currentPage, itemsPerPage)
    } catch {
      // Error already handled by errorHandler in movieService
    }
  }, [fetchMovies, currentPage])

  // Handle delete
  const handleDelete = useCallback((movieId: string) => {
    console.log('Delete:', movieId)
  }, [])

  return (
    <div className="movies-page">
      <header className="movies-page__header">
        <div className="movies-page__title-section">
          <h1 className="movies-page__title">Movies</h1>
          <p className="movies-page__subtitle">
            {isLoading
              ? 'Loading...'
              : totalMovies > 0
                ? `${totalMovies} movie${totalMovies !== 1 ? 's' : ''} in your library`
                : 'No movies found'}
          </p>
        </div>

        <div className="movies-page__search">
          <TextInput
            placeholder="Search movies..."
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

      <div className="movies-page__toolbar">
        <div className="movies-page__toolbar-left">
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

        <div className="movies-page__toolbar-right">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleScanDirectory}
            disabled={isScanning}
          >
            {isScanning ? 'Scanning...' : 'Scan Now'}
          </Button>
          <div className="movies-page__view-toggle" role="group" aria-label="View mode">
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

      <main className="movies-page__content">
        {scanResult && (
          <div className="p-4 mb-4 text-green-700 bg-green-50 dark:bg-green-900/20 dark:text-green-400 rounded-lg border border-green-200 dark:border-green-800">
            <p>{scanResult}</p>
          </div>
        )}

        {error && (
          <div className="p-4 mb-4 text-red-700 bg-red-50 dark:bg-red-900/20 dark:text-red-400 rounded-lg border border-red-200 dark:border-red-800">
            <p>{error}</p>
            <button
              onClick={() => fetchMovies(currentPage, itemsPerPage)}
              className="mt-2 text-sm underline hover:no-underline"
            >
              Try again
            </button>
          </div>
        )}

        {isLoading ? (
          <div className={`movies-page__grid movies-page__grid--${viewMode}`}>
            {Array.from({ length: itemsPerPage }).map((_, index) => (
              <SkeletonCard key={index} />
            ))}
          </div>
        ) : movies.length === 0 ? (
          <EmptyState
            variant="empty"
            title="No movies found"
            description="Your movie library will appear here once media files are synced from your movie directory."
            action={{
              label: 'Clear filters',
              onClick: handleClearFilters,
            }}
          />
        ) : (
          <>
            <div className={`movies-page__grid movies-page__grid--${viewMode}`}>
              {movies.map((movie) => {
                const movieMismatch = mismatches.find(
                  (m) => m.item_type === 'movie' && m.item_id === Number(movie.id)
                )
                return (
                  <MovieCard
                    key={movie.id}
                    id={String(movie.id)}
                    title={movie.title}
                    year={movie.year ?? 0}
                    rating={movie.rating}
                    poster_url={movie.poster_url}
                    genres={movie.genre}
                    quality={movie.quality}
                    resolution={movie.resolution}
                    codec_video={movie.codec_video}
                    codec_audio={movie.codec_audio}
                    audio_channels={movie.audio_channels}
                    file_size={movie.file_size}
                    file_duration={movie.file_duration}
                    mismatch={movieMismatch}
                    ourTmdbId={movie.tmdb_id ?? ''}
                    onResolve={resolveMismatch}
                    onClick={() => handleMovieClick(String(movie.id))}
                    onAddToQueue={() => handleAddToQueue(String(movie.id))}
                    onScan={() => handleScan(String(movie.id))}
                    onEdit={() => handleEdit(String(movie.id))}
                    onDelete={() => handleDelete(String(movie.id))}
                    isWatched={movie.is_watched}
                  />
                )
              })}
            </div>

            {totalPages > 1 && (
              <div className="movies-page__pagination">
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
        isOpen={modalMovieId !== null}
        mediaType="movie"
        mediaId={modalMovieId || ''}
        onClose={() => setModalMovieId(null)}
        onMetadataSynced={() => fetchMovies(currentPage, itemsPerPage)}
      />
    </div>
  )
}

export default MoviesPage
