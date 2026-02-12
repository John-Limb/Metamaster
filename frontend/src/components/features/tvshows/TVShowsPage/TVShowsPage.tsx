import React, { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { TextInput, Button, Pagination, EmptyState, Skeleton, SkeletonCard } from '@/components/common'
import { FilterPanel, type FilterSection } from '@/components/features/filter'
import { SortDropdown, type SortOption } from '@/components/features/sort'
import { TVShowCard, type TVShowCardProps } from '../TVShowCard'
import './TVShowsPage.css'

// Mock TV show type for empty state demonstration
interface TVShow extends Omit<TVShowCardProps, 'onClick' | 'onAddToQueue' | 'onEdit' | 'onDelete'> {}

const TVShowsPage: React.FC = () => {
  const navigate = useNavigate()
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({})
  const [sortValue, setSortValue] = useState('name-asc')
  const [currentPage, setCurrentPage] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [tvShows, setTvShows] = useState<TVShow[]>([])
  const [totalPages, setTotalPages] = useState(1)
  const itemsPerPage = 12

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery)
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  // Filter sections (with additional status and network filters for TV shows)
  const filterSections: FilterSection[] = [
    {
      id: 'genre',
      label: 'Genre',
      options: [
        { value: 'action', label: 'Action', count: 15 },
        { value: 'comedy', label: 'Comedy', count: 22 },
        { value: 'drama', label: 'Drama', count: 28 },
        { value: 'horror', label: 'Horror', count: 10 },
        { value: 'sci-fi', label: 'Sci-Fi', count: 12 },
        { value: 'thriller', label: 'Thriller', count: 18 },
        { value: 'reality', label: 'Reality', count: 8 },
      ],
      multiSelect: true,
    },
    {
      id: 'status',
      label: 'Status',
      options: [
        { value: 'continuing', label: 'Continuing', count: 25 },
        { value: 'ended', label: 'Ended', count: 45 },
        { value: 'returning', label: 'Returning', count: 12 },
      ],
      multiSelect: true,
    },
    {
      id: 'network',
      label: 'Network',
      options: [
        { value: 'netflix', label: 'Netflix', count: 18 },
        { value: 'hbo', label: 'HBO', count: 12 },
        { value: 'hulu', label: 'Hulu', count: 8 },
        { value: 'amazon', label: 'Amazon Prime', count: 15 },
        { value: 'disney', label: 'Disney+', count: 10 },
        { value: 'apple', label: 'Apple TV+', count: 6 },
      ],
      multiSelect: true,
    },
    {
      id: 'year',
      label: 'Year',
      options: [
        { value: '2024', label: '2024', count: 8 },
        { value: '2023', label: '2023', count: 15 },
        { value: '2022', label: '2022', count: 22 },
        { value: '2021', label: '2021', count: 18 },
        { value: '2020', label: '2020', count: 25 },
      ],
      multiSelect: true,
    },
    {
      id: 'rating',
      label: 'Rating',
      options: [
        { value: '5', label: '5 Stars', count: 6 },
        { value: '4', label: '4+ Stars', count: 22 },
        { value: '3', label: '3+ Stars', count: 38 },
      ],
      multiSelect: false,
    },
  ]

  // Sort options
  const sortOptions: SortOption[] = [
    { value: 'name-asc', label: 'Name', direction: 'asc' },
    { value: 'name-desc', label: 'Name', direction: 'desc' },
    { value: 'premiere-asc', label: 'Premiere Date', direction: 'asc' },
    { value: 'premiere-desc', label: 'Premiere Date', direction: 'desc' },
    { value: 'rating-asc', label: 'Rating', direction: 'asc' },
    { value: 'rating-desc', label: 'Rating', direction: 'desc' },
    { value: 'seasons-asc', label: 'Seasons', direction: 'asc' },
    { value: 'seasons-desc', label: 'Seasons', direction: 'desc' },
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

  // Handle TV show click
  const handleShowClick = useCallback((showId: string) => {
    navigate(`/tv-shows/${showId}`)
  }, [navigate])

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

  // Simulate loading
  useEffect(() => {
    setIsLoading(true)
    const timer = setTimeout(() => {
      setTvShows([])
      setTotalPages(1)
      setIsLoading(false)
    }, 1000)
    return () => clearTimeout(timer)
  }, [debouncedSearch, selectedFilters, sortValue, currentPage])

  return (
    <div className="tvshows-page">
      <header className="tvshows-page__header">
        <div className="tvshows-page__title-section">
          <h1 className="tvshows-page__title">TV Shows</h1>
          <p className="tvshows-page__subtitle">
            {isLoading ? 'Loading...' : 'No TV shows found'}
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
            description="Try adjusting your search or filters to find what you're looking for."
            action={{
              label: 'Clear filters',
              onClick: handleClearFilters,
            }}
          />
        ) : (
          <>
            <div className={`tvshows-page__grid tvshows-page__grid--${viewMode}`}>
              {tvShows.map((show) => (
                <TVShowCard
                  key={show.id}
                  {...show}
                  onClick={() => handleShowClick(show.id)}
                  onAddToQueue={() => handleAddToQueue(show.id)}
                  onEdit={() => handleEdit(show.id)}
                  onDelete={() => handleDelete(show.id)}
                />
              ))}
            </div>

            {totalPages > 1 && (
              <div className="tvshows-page__pagination">
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

export default TVShowsPage
