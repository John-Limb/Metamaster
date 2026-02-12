import React, { useState, useCallback } from 'react'
import { useSearchStore } from '@/stores/searchStore'
import { ConfirmDialog } from '@/components/common'

interface SavedSearchesProps {
  className?: string
  onSelect?: (searchId: string) => void
}

export function SavedSearches({ className = '', onSelect }: SavedSearchesProps) {
  const { savedSearches, loadSearch, deleteSavedSearch } = useSearchStore()
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)

  const handleLoadSearch = useCallback(
    (id: string) => {
      loadSearch(id)
      onSelect?.(id)
    },
    [loadSearch, onSelect]
  )

  const handleDeleteClick = useCallback((id: string) => {
    setDeleteId(id)
    setShowConfirmDialog(true)
  }, [])

  const handleConfirmDelete = useCallback(() => {
    if (deleteId) {
      deleteSavedSearch(deleteId)
    }
    setShowConfirmDialog(false)
    setDeleteId(null)
  }, [deleteId, deleteSavedSearch])

  const handleCancelDelete = useCallback(() => {
    setShowConfirmDialog(false)
    setDeleteId(null)
  }, [])

  if (savedSearches.length === 0) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No saved searches</h3>
        <p className="mt-1 text-sm text-gray-500">
          Save your search filters for quick access later.
        </p>
      </div>
    )
  }

  return (
    <div className={className}>
      <h3 className="text-lg font-medium text-gray-900 mb-4">Saved Searches</h3>
      <ul className="divide-y divide-gray-200" role="list" aria-label="Saved searches">
        {savedSearches.map((search) => (
          <li
            key={search.id}
            className="py-4 flex items-center justify-between hover:bg-gray-50 px-2 rounded-md transition-colors"
          >
            <div className="flex-1 min-w-0">
              <button
                onClick={() => handleLoadSearch(search.id)}
                className="text-left focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md p-1 -ml-1"
              >
                <p className="text-sm font-medium text-blue-600 truncate">
                  {search.name}
                </p>
                <p className="text-sm text-gray-500 truncate">
                  {search.filters.query || 'No query'} •{' '}
                  {search.filters.type || 'All types'}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Saved on {new Date(search.createdAt).toLocaleDateString()}
                </p>
              </button>
            </div>
            <div className="ml-4 flex-shrink-0">
              <button
                onClick={() => handleDeleteClick(search.id)}
                className="text-gray-400 hover:text-red-500 focus:outline-none focus:ring-2 focus:ring-red-500 rounded p-1"
                aria-label={`Delete saved search "${search.name}"`}
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
            </div>
          </li>
        ))}
      </ul>

      {showConfirmDialog && (
        <ConfirmDialog
          isOpen={showConfirmDialog}
          title="Delete Saved Search"
          message="Are you sure you want to delete this saved search? This action cannot be undone."
          confirmText="Delete"
          isDangerous
          onConfirm={handleConfirmDelete}
          onCancel={handleCancelDelete}
        />
      )}
    </div>
  )
}

export default SavedSearches
