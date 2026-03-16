import React from 'react'
import type { PlexPlaylist } from '../../../services/plexCollectionService'
import { Checkbox, CheckboxInput } from '@/components/common/Checkbox'

interface PlaylistCardProps {
  playlist: PlexPlaylist
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number) => void
  selectable?: boolean
  selected?: boolean
  onSelect?: (id: number, selected: boolean) => void
}

function formatSyncDate(dateStr: string | null): string {
  if (!dateStr) return 'Never synced'
  return new Date(dateStr).toLocaleString()
}

export function PlaylistCard({
  playlist,
  onToggleEnabled,
  onPush,
  onDelete,
  selectable,
  selected,
  onSelect,
}: PlaylistCardProps) {
  return (
    <div className={`rounded-xl border bg-white dark:bg-slate-800 p-4 space-y-3 transition-colors ${
      selected
        ? 'border-indigo-400 dark:border-indigo-500 ring-1 ring-indigo-400 dark:ring-indigo-500'
        : 'border-slate-200 dark:border-slate-700'
    }`}>
      <div className="flex items-start justify-between gap-2 min-w-0">
        <h3 className="font-semibold text-slate-900 dark:text-white truncate">{playlist.name}</h3>
        {selectable && (
          <CheckboxInput
            checked={!!selected}
            onChange={checked => onSelect?.(playlist.id, checked)}
            aria-label={`Select ${playlist.name}`}
          />
        )}
      </div>

      {playlist.description && (
        <p className="text-sm text-slate-500 dark:text-slate-400 truncate">{playlist.description}</p>
      )}

      <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
        <span>{playlist.items.length} item{playlist.items.length !== 1 ? 's' : ''}</span>
        <span>{formatSyncDate(playlist.last_synced_at)}</span>
      </div>

      <div className="flex items-center justify-between gap-2 pt-1">
        <Checkbox
          label="Enabled"
          checked={playlist.enabled}
          onChange={checked => onToggleEnabled(playlist.id, checked)}
        />

        <div className="flex items-center gap-2">
          <button
            onClick={() => onPush(playlist.id)}
            disabled={!playlist.enabled}
            className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors"
          >
            Push to Plex
          </button>
          <button
            onClick={() => onDelete(playlist.id)}
            className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}

export default PlaylistCard
