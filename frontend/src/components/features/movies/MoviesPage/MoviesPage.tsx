import React, { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { TextInput, Button, Pagination, EmptyState, Skeleton, SkeletonCard } from '@/components/common'
import { FilterPanel, type FilterSection } from '@/components/features/filter'
import { SortDropdown, type SortOption } from '@/components/features/sort'
import { MovieCard, type MovieCardProps } from '../MovieCard'
import './MoviesPage.css'

// Mock movie type for empty state demonstration
interface Movie extends Omit<MovieCardProps, 'onClick' | 'onAddToQueue' | 'onEdit' | 'onDelete'> {}

const MoviesPage: React.FC = () => {
  const navigate = useNavigate()
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({})
  const [sortValue, setSortValue] = useState('title-asc')
  const [currentPage, setCurrentPage] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [movies, setMovies] = useState<Movie[]>([])
  const [totalPages, setTotalPages] = useState(1)
  const itemsPerPage = 12

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  // Filter sections
  const filterSections: FilterSection[] = [
    {
      id: 'genre',
      label: 'Genre',
      options: [
        { value: 'action', label: 'Action', count: 24 },
        { value: 'comedy', label: 'Comedy', count: 18 },
        { value: 'drama', label: 'Drama', count: 32 },
        { value: 'horror', label: 'Horror', count: 12 },
        { value: 'sci-fi', label: 'Sci-Fi', count: 15 },
        { value: 'thriller', label: 'Thriller', count: 21 },
      ],
      multiSelect: true,
    },
    {
      id: 'year',
      label: 'Year',
      options: [
        { value: '2024', label: '2024', count: 5 },
        { value: '2023', label: '2023', count: 12 },
        { value: '2022', label: '2022', count: 18 },
        { value: '2021', label: '2021', count: 15 },
        { value: '2020', label: '2020', count: 22 },
      ],
      multiSelect: true,
    },
    {
      id: 'rating',
      label: 'Rating',
      options: [
        { value: '5', label: '5 Stars', count: 8 },
        { value: '4', label: '4+ Stars', count: 25 },
        { value: '3', label: '3+ Stars', count: 45 },
      ],
      multiSelect: false,
    },
    {
      id: 'quality',
      label: 'Quality',
      options: [
        { value: '4k', label: '4K', count: 35 },
        { value: '1080p', label: '1080p', count: 62 },
        { value: '720p', label: '720p', count: 28 },
      ],
      multiSelect: true,
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
    setCurrentPage(1)
  }, [])

  // Handle clear all filters
  const handleClearFilters = useCallback(() => {
    setSelectedFilters({})
    setCurrentPage(1)
  }, [])

  // Handle movie click
  const handleMovieClick = useCallback((movieId: string) => {
    navigate(`/movies/${movieId}`)
  }, [navigate])

  // Handle add to queue
  const handleAddToQueue = useCallback((movieId: string) => {
    console.log('Add to queue:', movieId)
  }, [])

  // Handle edit
  const handleEdit = useCallback((movieId: string) => {
    console.log('Edit:', movieId)
  }, [])

  // Handle delete
  const handleDelete = useCallback((movieId: string) => {
    console.log('Delete:', movieId)
  }, [])

  // Simulate loading
  useEffect(() => {
    setIsLoading(true)
    const timer = setTimeout(() => {
      setMovies([])
      setTotalPages(1)
      setIsLoading(false)
    }, 1000)
    return () => clearTimeout(timer)
  }, [debouncedSearch, selectedFilters, sortValue, currentPage])

  return (
    <div className="movies-page">
      <header className="movies-page__header">
        <div className="movies-page__title-section">
          <h1 className="movies-page__title">Movies</h1>
          <p className="movies-page__subtitle">
            {isLoading ? 'Loading...' : 'No movies found'}
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
            description="Try adjusting your search or filters to find what you're looking for."
            action={{
              label: 'Clear filters',
              onClick: handleClearFilters,
            }}
          />
        ) : (
          <>
            <div className={`movies-page__grid movies-page__grid--${viewMode}`}>
              {movies.map((movie) => (
                <MovieCard
                  key={movie.id}
                  {...movie}
                  onClick={() => handleMovieClick(movie.id)}
                  onAddToQueue={() => handleAddToQueue(movie.id)}
                  onEdit={() => handleEdit(movie.id)}
                  onDelete={() => handleDelete(movie.id)}
                />
              ))}
            </div>

            {totalPages > 1 && (
              <div className="movies-page__pagination">
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={setCurrentPage}
                />
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}

export default MoviesPage
