import React, { useState } from 'react'
import type { PlexMismatchItem } from '../../../services/plexService'
import { MismatchResolveModal } from './MismatchResolveModal'

interface Props {
  mismatches: PlexMismatchItem[]
  onResolve: (recordId: number, trust: 'metamaster' | 'plex') => void
}

export function MismatchesPanel({ mismatches, onResolve }: Props) {
  const [active, setActive] = useState<PlexMismatchItem | null>(null)

  if (mismatches.length === 0) return null

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-orange-600 dark:text-orange-400">
        {mismatches.length} TMDB mismatch{mismatches.length !== 1 ? 'es' : ''} detected
      </h3>
      <ul className="space-y-2">
        {mismatches.map((m) => (
          <li
            key={m.id}
            className="flex items-center justify-between text-sm p-3 rounded-lg bg-orange-50 dark:bg-orange-900/20"
          >
            <span className="text-gray-700 dark:text-gray-300">
              {m.item_type} #{m.item_id} — Plex TMDB #{m.plex_tmdb_id}
            </span>
            <button
              onClick={() => setActive(m)}
              className="ml-3 px-3 py-1 text-xs bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition"
            >
              Resolve
            </button>
          </li>
        ))}
      </ul>

      {active && (
        <MismatchResolveModal
          mismatch={active}
          ourTmdbId={active.plex_tmdb_id}
          onResolve={(id, trust) => {
            onResolve(id, trust)
            setActive(null)
          }}
          onClose={() => setActive(null)}
        />
      )}
    </div>
  )
}
