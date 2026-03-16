import React, { useEffect, useState } from 'react'
import { movieService } from '../../../services/movieService'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

interface GenreBuilderProps {
  selected: string | null
  onSelect: (genre: string) => void
}

export function GenreBuilder({ selected, onSelect }: GenreBuilderProps) {
  const [genres, setGenres] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    movieService
      .getMovieGenres()
      .then(setGenres)
      .catch(() => setError('Failed to load genres'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-4">
      <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">
        Choose one genre
      </p>
      {loading && <LoadingSpinner />}
      {error && <p className="text-sm text-red-500">{error}</p>}
      {!loading && !error && (
        <div className="flex flex-wrap gap-2">
          {genres.map((genre) => (
            <button
              key={genre}
              type="button"
              onClick={() => onSelect(genre)}
              className={`rounded-full px-3.5 py-1.5 text-sm font-medium transition-colors ${
                selected === genre
                  ? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 border-2 border-indigo-500'
                  : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-indigo-400 dark:hover:border-indigo-500'
              }`}
            >
              {genre}
            </button>
          ))}
        </div>
      )}
      <p className="text-xs text-slate-400 dark:text-slate-500 mt-3">
        One genre per collection · Movies only · From your library
      </p>
    </div>
  )
}

export default GenreBuilder
