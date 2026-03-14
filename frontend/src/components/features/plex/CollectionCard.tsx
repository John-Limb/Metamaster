import React from 'react'
import type { PlexCollection } from '../../../services/plexCollectionService'

interface CollectionCardProps {
  collection: PlexCollection
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number) => void
}

const BUILDER_LABELS: Record<string, string> = {
  tmdb_collection: 'TMDB Collection',
  static_items: 'Static',
  genre: 'Genre',
  decade: 'Decade',
}

function formatSyncDate(dateStr: string | null): string {
  if (!dateStr) return 'Never synced'
  return new Date(dateStr).toLocaleString()
}

export function CollectionCard({ collection, onToggleEnabled, onPush, onDelete }: CollectionCardProps) {
  const builderLabel = BUILDER_LABELS[collection.builder_type] ?? collection.builder_type

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="font-semibold text-slate-900 dark:text-white truncate">{collection.name}</h3>
          {collection.description && (
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5 truncate">{collection.description}</p>
          )}
        </div>
        <span className="shrink-0 inline-flex px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400">
          {builderLabel}
        </span>
      </div>

      <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
        <span>{collection.items.length} item{collection.items.length !== 1 ? 's' : ''}</span>
        <span>{formatSyncDate(collection.last_synced_at)}</span>
      </div>

      <div className="flex items-center justify-between gap-2 pt-1">
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={collection.enabled}
            onChange={e => onToggleEnabled(collection.id, e.target.checked)}
            className="w-4 h-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
          />
          <span className="text-sm text-slate-700 dark:text-slate-300">Enabled</span>
        </label>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onPush(collection.id)}
            disabled={!collection.enabled}
            className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors"
          >
            Push to Plex
          </button>
          <button
            onClick={() => onDelete(collection.id)}
            className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
          >
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}

export default CollectionCard
