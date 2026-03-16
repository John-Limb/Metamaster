import React, { useState } from 'react'
import { FaChevronDown, FaChevronUp } from 'react-icons/fa'
import type { PlexCollection } from '../../../services/plexCollectionService'
import { Checkbox } from '@/components/common/Checkbox'

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
  const [expanded, setExpanded] = useState(false)
  const builderLabel = BUILDER_LABELS[collection.builder_type] ?? collection.builder_type
  const hasItems = collection.items.length > 0

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
        <button
          onClick={() => hasItems && setExpanded(v => !v)}
          disabled={!hasItems}
          className="flex items-center gap-1 hover:text-slate-700 dark:hover:text-slate-200 disabled:cursor-default transition-colors"
        >
          <span>{collection.items.length} item{collection.items.length !== 1 ? 's' : ''}</span>
          {hasItems && (expanded ? <FaChevronUp className="w-3 h-3" /> : <FaChevronDown className="w-3 h-3" />)}
        </button>
        <span>{formatSyncDate(collection.last_synced_at)}</span>
      </div>

      {expanded && (
        <ul className="max-h-48 overflow-y-auto rounded-lg border border-slate-100 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700 text-xs">
          {collection.items.map(item => (
            <li key={item.id} className="flex items-center justify-between px-3 py-1.5 gap-2">
              <span className="font-mono text-slate-600 dark:text-slate-400 truncate">{item.plex_rating_key}</span>
              <span className="shrink-0 text-slate-400 dark:text-slate-500 capitalize">{item.item_type}</span>
            </li>
          ))}
        </ul>
      )}

      <div className="flex items-center justify-between gap-2 pt-1">
        <Checkbox
          label="Enabled"
          checked={collection.enabled}
          onChange={checked => onToggleEnabled(collection.id, checked)}
        />

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
