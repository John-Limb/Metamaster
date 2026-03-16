import React, { useEffect, useState, useRef } from 'react'
import {
  getLocalTmdbCollections,
  searchTmdbCollections,
} from '../../../services/plexCollectionService'
import type {
  LocalTmdbCollection,
  TmdbCollectionSearchResult,
} from '../../../services/plexCollectionService'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { Button } from '@/components/common/Button'
import { TextInput } from '@/components/common/TextInput'

export interface SelectedTmdbCollection {
  id: number
  name: string
  description: string
}

interface TmdbCollectionBuilderProps {
  selected: SelectedTmdbCollection | null
  onSelect: (collection: SelectedTmdbCollection) => void
  onRemove: () => void
}

export function TmdbCollectionBuilder({
  selected,
  onSelect,
  onRemove,
}: TmdbCollectionBuilderProps) {
  const [local, setLocal] = useState<LocalTmdbCollection[]>([])
  const [localLoading, setLocalLoading] = useState(true)
  const [localError, setLocalError] = useState<string | null>(null)

  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<TmdbCollectionSearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const searchTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  useEffect(() => {
    getLocalTmdbCollections()
      .then(setLocal)
      .catch(() => setLocalError('Failed to load library matches'))
      .finally(() => setLocalLoading(false))
  }, [])

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setSearchQuery(val)
    clearTimeout(searchTimer.current)
    if (!val) {
      setSearchResults([])
      return
    }
    searchTimer.current = setTimeout(() => {
      setSearching(true)
      setSearchError(null)
      searchTmdbCollections(val)
        .then(setSearchResults)
        .catch(() => setSearchError('TMDB search failed'))
        .finally(() => setSearching(false))
    }, 500)
  }

  const isSelected = (id: number) => selected?.id === id

  const handleSelectLocal = (col: LocalTmdbCollection) => {
    onSelect({ id: col.tmdb_collection_id, name: col.name, description: '' })
  }

  const handleSelectSearch = (col: TmdbCollectionSearchResult) => {
    onSelect({ id: col.id, name: col.name, description: '' })
  }

  return (
    <div className="space-y-3">
      <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-4">
        <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">
          Matched in your library
        </p>
        {localLoading && <LoadingSpinner />}
        {localError && <p className="text-sm text-red-500">{localError}</p>}
        {!localLoading && !localError && local.length === 0 && (
          <p className="text-sm text-slate-400 dark:text-slate-500">
            No TMDB collections matched in your library yet.
          </p>
        )}
        {!localLoading && local.length > 0 && (
          <div className="rounded-lg border border-slate-200 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700 overflow-hidden">
            {local.map((col) => (
              <div
                key={col.tmdb_collection_id}
                className={`flex items-center justify-between px-3 py-2.5 ${
                  isSelected(col.tmdb_collection_id)
                    ? 'bg-green-50 dark:bg-green-900/20'
                    : 'bg-white dark:bg-slate-800'
                }`}
              >
                <div>
                  <p className="text-sm font-medium text-slate-800 dark:text-slate-100">
                    {col.name}
                  </p>
                  <p className="text-xs text-slate-400">
                    ID {col.tmdb_collection_id} · {col.movie_count} film
                    {col.movie_count !== 1 ? 's' : ''} in library
                  </p>
                </div>
                {isSelected(col.tmdb_collection_id) ? (
                  <Button size="sm" variant="outline" onClick={onRemove}>
                    Remove
                  </Button>
                ) : (
                  <Button size="sm" onClick={() => handleSelectLocal(col)}>
                    Select
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-4">
        <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">
          Search TMDB
        </p>
        <TextInput
          placeholder="e.g. Batman, James Bond..."
          value={searchQuery}
          onChange={handleSearchChange}
          type="search"
        />
        {searching && (
          <div className="mt-2">
            <LoadingSpinner />
          </div>
        )}
        {searchError && <p className="text-sm text-red-500 mt-2">{searchError}</p>}
        {!searching && searchResults.length > 0 && (
          <div className="mt-2 rounded-lg border border-slate-200 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700 overflow-hidden">
            {searchResults.map((col) => (
              <div
                key={col.id}
                className={`flex items-center justify-between px-3 py-2.5 ${
                  isSelected(col.id)
                    ? 'bg-green-50 dark:bg-green-900/20'
                    : 'bg-white dark:bg-slate-800'
                }`}
              >
                <div>
                  <p className="text-sm font-medium text-slate-800 dark:text-slate-100">
                    {col.name}
                  </p>
                  <p className="text-xs text-slate-400">ID {col.id}</p>
                </div>
                {isSelected(col.id) ? (
                  <Button size="sm" variant="outline" onClick={onRemove}>
                    Remove
                  </Button>
                ) : (
                  <Button size="sm" onClick={() => handleSelectSearch(col)}>
                    Select
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default TmdbCollectionBuilder
