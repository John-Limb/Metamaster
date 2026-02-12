import React, { useState, useCallback } from 'react'
import { useSearchStore } from '@/stores/searchStore'
import type { SearchFilters } from '@/types'

interface FilterPanelProps {
  isOpen?: boolean
  onClose?: () => void
  className?: string
}

const FILE_TYPES = [
  { value: 'video', label: 'Video' },
  { value: 'audio', label: 'Audio' },
  { value: 'image', label: 'Image' },
  { value: 'document', label: 'Document' },
  { value: 'archive', label: 'Archive' },
]

const DATE_RANGES = [
  { value: 'today', label: 'Today' },
  { value: 'week', label: 'This Week' },
  { value: 'month', label: 'This Month' },
  { value: 'year', label: 'This Year' },
]

const SIZE_RANGES = [
  { value: 'small', label: 'Small (< 10 MB)' },
  { value: 'medium', label: 'Medium (10 - 100 MB)' },
  { value: 'large', label: 'Large (100 MB - 1 GB)' },
  { value: 'xlarge', label: 'Very Large (> 1 GB)' },
]

export function FilterPanel({ isOpen = true, onClose, className = '' }: FilterPanelProps) {
  const { filters, setFilters, clearFilters } = useSearchStore()
  const [localFilters, setLocalFilters] = useState<SearchFilters>(filters)

  const handleApplyFilters = useCallback(() => {
    setFilters(localFilters)
    onClose?.()
  }, [localFilters, setFilters, onClose])

  const handleClearFilters = useCallback(() => {
    const emptyFilters: SearchFilters = {}
    setLocalFilters(emptyFilters)
    clearFilters()
    onClose?.()
  }, [clearFilters, onClose])

  const handleFilterChange = useCallback(
    (key: keyof SearchFilters, value: any) => {
      setLocalFilters((prev) => ({
        ...prev,
        [key]: value === '' ? undefined : value,
      }))
    },
    []
  )

  const handleDateRangeChange = useCallback(
    (range: string) => {
      const now = new Date()
      let dateFrom: string | undefined

      switch (range) {
        case 'today':
          dateFrom = new Date(now.setHours(0, 0, 0, 0)).toISOString()
          break
        case 'week':
          dateFrom = new Date(now.setDate(now.getDate() - 7)).toISOString()
          break
        case 'month':
          dateFrom = new Date(now.setMonth(now.getMonth() - 1)).toISOString()
          break
        case 'year':
          dateFrom = new Date(now.setFullYear(now.getFullYear() - 1)).toISOString()
          break
      }

      setLocalFilters((prev) => ({
        ...prev,
        dateFrom,
        dateTo: undefined,
      }))
    },
    []
  )

  const handleSizeRangeChange = useCallback(
    (range: string) => {
      let sizeMin: number | undefined
      let sizeMax: number | undefined

      switch (range) {
        case 'small':
          sizeMax = 10 * 1024 * 1024
          break
        case 'medium':
          sizeMin = 10 * 1024 * 1024
          sizeMax = 100 * 1024 * 1024
          break
        case 'large':
          sizeMin = 100 * 1024 * 1024
          sizeMax = 1024 * 1024 * 1024
          break
        case 'xlarge':
          sizeMin = 1024 * 1024 * 1024
          break
      }

      setLocalFilters((prev) => ({
        ...prev,
        sizeMin,
        sizeMax,
      }))
    },
    []
  )

  if (!isOpen) return null

  return (
    <div
      className={`bg-white shadow-lg rounded-lg p-4 ${className}`}
      role="region"
      aria-label="Filter panel"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Filters</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
          aria-label="Close filter panel"
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="space-y-4">
        {/* Content Type */}
        <div>
          <label
            htmlFor="filter-type"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Content Type
          </label>
          <select
            id="filter-type"
            value={localFilters.type || ''}
            onChange={(e) => handleFilterChange('type', e.target.value)}
            className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="">All Types</option>
            <option value="file">Files</option>
            <option value="movie">Movies</option>
            <option value="tvshow">TV Shows</option>
          </select>
        </div>

        {/* File Type */}
        <div>
          <label
            htmlFor="filter-file-type"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            File Type
          </label>
          <select
            id="filter-file-type"
            value={localFilters.fileType || ''}
            onChange={(e) => handleFilterChange('fileType', e.target.value)}
            className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="">All File Types</option>
            {FILE_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {/* Date Range */}
        <div>
          <label
            htmlFor="filter-date-range"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Date Range
          </label>
          <select
            id="filter-date-range"
            value={
              localFilters.dateFrom
                ? localFilters.dateTo
                  ? 'custom'
                  : 'today'
                : ''
            }
            onChange={(e) => handleDateRangeChange(e.target.value)}
            className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="">Any Time</option>
            {DATE_RANGES.map((range) => (
              <option key={range.value} value={range.value}>
                {range.label}
              </option>
            ))}
            <option value="custom">Custom Range</option>
          </select>
        </div>

        {/* Custom Date From */}
        {localFilters.dateFrom && (
          <div>
            <label
              htmlFor="filter-date-from"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              From Date
            </label>
            <input
              type="date"
              id="filter-date-from"
              value={localFilters.dateFrom?.split('T')[0] || ''}
              onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
        )}

        {/* Custom Date To */}
        {localFilters.dateFrom && (
          <div>
            <label
              htmlFor="filter-date-to"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              To Date
            </label>
            <input
              type="date"
              id="filter-date-to"
              value={localFilters.dateTo?.split('T')[0] || ''}
              onChange={(e) => handleFilterChange('dateTo', e.target.value)}
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
        )}

        {/* Size Range */}
        <div>
          <label
            htmlFor="filter-size-range"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            File Size
          </label>
          <select
            id="filter-size-range"
            onChange={(e) => handleSizeRangeChange(e.target.value)}
            className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            <option value="">Any Size</option>
            {SIZE_RANGES.map((range) => (
              <option key={range.value} value={range.value}>
                {range.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Active Filters Summary */}
      {(filters.type || filters.fileType || filters.dateFrom || filters.sizeMin) && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-sm text-gray-600 mb-2">Active filters:</p>
          <div className="flex flex-wrap gap-2">
            {filters.type && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Type: {filters.type}
              </span>
            )}
            {filters.fileType && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                File: {filters.fileType}
              </span>
            )}
            {filters.dateFrom && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                Date: {new Date(filters.dateFrom).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="mt-4 pt-4 border-t border-gray-200 flex justify-end space-x-3">
        <button
          onClick={handleClearFilters}
          className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Clear All
        </button>
        <button
          onClick={handleApplyFilters}
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Apply Filters
        </button>
      </div>
    </div>
  )
}

export default FilterPanel
