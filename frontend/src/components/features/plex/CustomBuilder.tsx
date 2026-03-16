import React, { useState, useRef } from 'react'
import { FaTimes } from 'react-icons/fa'
import { movieService } from '../../../services/movieService'
import { Button } from '@/components/common/Button'
import { TextInput } from '@/components/common/TextInput'
import type { Movie } from '@/types'

export interface SelectedMovie {
  tmdb_id: string
  title: string
}

interface CustomBuilderProps {
  selected: SelectedMovie[]
  onAdd: (movie: SelectedMovie) => void
  onRemove: (tmdbId: string) => void
}

export function CustomBuilder({ selected, onAdd, onRemove }: CustomBuilderProps) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Movie[]>([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  const selectedIds = new Set(selected.map((s) => s.tmdb_id))

  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setQuery(val)
    clearTimeout(timer.current)
    if (val.length < 2) {
      setResults([])
      return
    }
    timer.current = setTimeout(() => {
      setSearching(true)
      setSearchError(null)
      movieService
        .searchMovies(val)
        .then((data) => setResults(data.items ?? []))
        .catch(() => setSearchError('Search failed'))
        .finally(() => setSearching(false))
    }, 300)
  }

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-4 space-y-3">
      <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
        Search your library
      </p>

      <TextInput
        placeholder="Search movies..."
        value={query}
        onChange={handleQueryChange}
        type="search"
      />

      {searching && <p className="text-xs text-slate-400">Searching...</p>}
      {searchError && <p className="text-sm text-red-500">{searchError}</p>}

      {results.length > 0 && (
        <div className="rounded-lg border border-slate-200 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700 overflow-hidden">
          {results.map((movie) => {
            const alreadyAdded = movie.tmdb_id
              ? selectedIds.has(movie.tmdb_id)
              : false
            const noId = !movie.tmdb_id
            return (
              <div
                key={movie.id}
                className="flex items-center justify-between px-3 py-2 bg-white dark:bg-slate-800"
              >
                <span className="text-sm text-slate-700 dark:text-slate-200">
                  {movie.title}
                  {movie.year && (
                    <span className="text-slate-400 dark:text-slate-500 ml-1">
                      ({movie.year})
                    </span>
                  )}
                </span>
                <span
                  title={noId ? 'Not yet enriched — no TMDB ID' : undefined}
                  className="inline-flex"
                >
                  <Button
                    size="sm"
                    variant={alreadyAdded ? 'secondary' : 'primary'}
                    disabled={alreadyAdded || noId}
                    onClick={() => {
                      if (movie.tmdb_id) {
                        onAdd({ tmdb_id: movie.tmdb_id, title: movie.title })
                      }
                    }}
                  >
                    {alreadyAdded ? 'Added' : 'Add'}
                  </Button>
                </span>
              </div>
            )
          })}
        </div>
      )}

      {selected.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 mb-1.5">
            Selected ({selected.length})
          </p>
          <div className="flex flex-wrap gap-1.5">
            {selected.map((m) => (
              <span
                key={m.tmdb_id}
                className="inline-flex items-center gap-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 px-2.5 py-1 rounded-full text-xs font-medium"
              >
                {m.title}
                <button
                  type="button"
                  onClick={() => onRemove(m.tmdb_id)}
                  className="text-indigo-400 hover:text-indigo-600 dark:hover:text-indigo-200 ml-0.5"
                  aria-label={`Remove ${m.title}`}
                >
                  <FaTimes className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default CustomBuilder
