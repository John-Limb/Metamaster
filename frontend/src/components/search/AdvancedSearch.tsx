import React, { useState, useCallback } from 'react'
import { useSearchStore } from '@/stores/searchStore'
import { SearchBar } from './SearchBar'
import { FilterPanel } from './FilterPanel'
import { SavedSearches } from './SavedSearches'

interface AdvancedSearchProps {
  onSearch?: (query: string, filters: Record<string, unknown>) => void
  showSavedSearches?: boolean
  className?: string
}

export function AdvancedSearch({
  onSearch,
  showSavedSearches = true,
  className = '',
}: AdvancedSearchProps) {
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const [isSavedSearchesOpen, setIsSavedSearchesOpen] = useState(false)
  const { filters, search, query } = useSearchStore()

  const handleSearch = useCallback(
    (searchQuery: string) => {
      search()
      onSearch?.(searchQuery, filters as Record<string, unknown>)
    },
    [filters, search, onSearch]
  )

  const toggleFilters = useCallback(() => {
    setIsFilterOpen((prev) => !prev)
    setIsSavedSearchesOpen(false)
  }, [])

  const toggleSavedSearches = useCallback(() => {
    setIsSavedSearchesOpen((prev) => !prev)
    setIsFilterOpen(false)
  }, [])

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Search Bar with Actions */}
      <div className="flex gap-2">
        <div className="flex-1">
          <SearchBar
            placeholder="Search files, movies, TV shows..."
            onSearch={handleSearch}
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={toggleFilters}
            className={`px-4 py-2 rounded-lg border font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
              isFilterOpen
                ? 'bg-blue-50 border-blue-200 text-blue-700'
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
            }`}
            aria-pressed={isFilterOpen}
            aria-label="Toggle filters"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
              />
            </svg>
          </button>
          {showSavedSearches && (
            <button
              onClick={toggleSavedSearches}
              className={`px-4 py-2 rounded-lg border font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                isSavedSearchesOpen
                  ? 'bg-blue-50 border-blue-200 text-blue-700'
                  : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
              aria-pressed={isSavedSearchesOpen}
              aria-label="Toggle saved searches"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
                />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Filter Panel */}
      {isFilterOpen && (
        <FilterPanel
          isOpen={isFilterOpen}
          onClose={() => setIsFilterOpen(false)}
        />
      )}

      {/* Saved Searches Panel */}
      {isSavedSearchesOpen && (
        <div className="bg-white shadow-lg rounded-lg p-4">
          <SavedSearches
            onSelect={() => {
              setIsSavedSearchesOpen(false)
              handleSearch(query)
            }}
          />
        </div>
      )}

      {/* Active Filters Summary */}
      {(filters.type || filters.fileType || filters.dateFrom || filters.sizeMin) && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Active filters:</span>
          <div className="flex flex-wrap gap-2">
            {filters.type && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Type: {filters.type}
                <button
                  onClick={() => useSearchStore.getState().setFilters({ ...filters, type: undefined })}
                  className="ml-1 text-blue-600 hover:text-blue-800 focus:outline-none"
                  aria-label={`Remove ${filters.type} filter`}
                >
                  ×
                </button>
              </span>
            )}
            {filters.fileType && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                File: {filters.fileType}
                <button
                  onClick={() =>
                    useSearchStore.getState().setFilters({ ...filters, fileType: undefined })
                  }
                  className="ml-1 text-green-600 hover:text-green-800 focus:outline-none"
                  aria-label={`Remove ${filters.fileType} filter`}
                >
                  ×
                </button>
              </span>
            )}
            {filters.dateFrom && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                Date: {new Date(filters.dateFrom).toLocaleDateString()}
                <button
                  onClick={() =>
                    useSearchStore.getState().setFilters({ ...filters, dateFrom: undefined })
                  }
                  className="ml-1 text-yellow-600 hover:text-yellow-800 focus:outline-none"
                  aria-label="Remove date filter"
                >
                  ×
                </button>
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default AdvancedSearch
