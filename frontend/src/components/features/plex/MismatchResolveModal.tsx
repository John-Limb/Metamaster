import React from 'react'
import type { PlexMismatchItem } from '../../../services/plexService'

interface Props {
  mismatch: PlexMismatchItem
  ourTmdbId: string
  onResolve: (recordId: number, trust: 'metamaster' | 'plex') => void
  onClose: () => void
}

const BTN =
  'px-4 py-2 rounded-lg text-sm font-medium transition disabled:opacity-50'

export function MismatchResolveModal({ mismatch, ourTmdbId, onResolve, onClose }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card rounded-xl shadow-xl p-6 max-w-md w-full mx-4 space-y-4">
        <h2 className="text-lg font-semibold text-body">
          TMDB ID Mismatch
        </h2>
        <p className="text-sm text-dim">
          MetaMaster and Plex have matched this item to different TMDB IDs. Which is correct?
        </p>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="p-3 rounded-lg bg-subtle">
            <p className="font-medium text-dim">MetaMaster</p>
            <p className="text-body">TMDB #{ourTmdbId}</p>
          </div>
          <div className="p-3 rounded-lg bg-subtle">
            <p className="font-medium text-dim">Plex</p>
            <p className="text-body">TMDB #{mismatch.plex_tmdb_id}</p>
          </div>
        </div>
        <div className="flex gap-3 pt-2">
          <button
            onClick={() => onResolve(mismatch.id, 'metamaster')}
            className={`${BTN} bg-primary-600 text-white hover:bg-primary-700 flex-1`}
          >
            Trust MetaMaster
          </button>
          <button
            onClick={() => onResolve(mismatch.id, 'plex')}
            className={`${BTN} bg-orange-500 text-white hover:bg-orange-600 flex-1`}
          >
            Trust Plex
          </button>
        </div>
        <button
          onClick={onClose}
          className="w-full text-sm text-hint hover:text-dim"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
