import React, { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import type { PlexCollection } from '../../../services/plexCollectionService'
import {
  getCollection,
  getCollectionArtwork,
} from '../../../services/plexCollectionService'
import { Checkbox } from '@/components/common/Checkbox'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { BUILDER_LABELS, formatSyncDate } from './plexUtils'

interface CollectionDrawerProps {
  collection: PlexCollection
  onClose: () => void
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number, deleteFromPlex: boolean) => void
}

export function CollectionDrawer({
  collection,
  onClose,
  onToggleEnabled,
  onPush,
  onDelete,
}: CollectionDrawerProps) {
  const [artworkUrl, setArtworkUrl] = useState<string | null>(null)
  const [detail, setDetail] = useState<PlexCollection | null>(null)
  const [showConfirm, setShowConfirm] = useState(false)
  const [deleteFromPlex, setDeleteFromPlex] = useState(!!collection.plex_rating_key)
  const drawerRef = useRef<HTMLDivElement>(null)

  // Fetch enriched detail (items with movie titles)
  useEffect(() => {
    getCollection(collection.id).then(setDetail).catch(() => {})
  }, [collection.id])

  // Fetch and manage artwork blob URL
  useEffect(() => {
    if (!collection.plex_rating_key) return
    let objectUrl: string | null = null
    let cancelled = false
    getCollectionArtwork(collection.id)
      .then(blob => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(blob)
        setArtworkUrl(objectUrl)
      })
      .catch(() => { if (!cancelled) setArtworkUrl(null) })
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [collection.id, collection.plex_rating_key])

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  // Close on click outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (drawerRef.current && !drawerRef.current.contains(e.target as Node)) {
        onClose()
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [onClose])

  const items = detail?.items ?? []

  return (
    <div
      ref={drawerRef}
      className="w-80 flex-shrink-0 border-l border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex flex-col overflow-hidden lg:relative fixed right-0 top-0 h-full z-40 lg:z-auto"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-700">
        <h3 className="font-semibold text-slate-900 dark:text-white truncate pr-2">
          {collection.name}
        </h3>
        <button
          onClick={onClose}
          aria-label="Close drawer"
          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors flex-shrink-0"
        >
          ✕
        </button>
      </div>

      <div className="overflow-y-auto flex-1 p-4 space-y-4">
        {/* Artwork */}
        {artworkUrl ? (
          <img
            src={artworkUrl}
            alt={`${collection.name} artwork`}
            className="w-full rounded-lg object-cover"
          />
        ) : (
          <div className="w-full h-32 rounded-lg bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-400 text-sm">
            No artwork
          </div>
        )}

        {/* Metadata */}
        <div className="flex items-center gap-2 flex-wrap text-sm text-slate-500 dark:text-slate-400">
          <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400">
            {BUILDER_LABELS[collection.builder_type] ?? collection.builder_type}
          </span>
          <span>{items.length} items</span>
          <span>·</span>
          <span>{formatSyncDate(collection.last_synced_at)}</span>
        </div>

        {collection.description && (
          <p className="text-sm text-slate-500 dark:text-slate-400">{collection.description}</p>
        )}

        {/* Controls */}
        <div className="flex items-center justify-between gap-2 p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50">
          <Checkbox
            label="Enabled"
            checked={collection.enabled}
            onChange={checked => onToggleEnabled(collection.id, checked)}
          />
          <div className="flex gap-2">
            <button
              onClick={() => onPush(collection.id)}
              disabled={!collection.enabled}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white transition-colors"
            >
              Push to Plex
            </button>
            <button
              onClick={() => { setDeleteFromPlex(!!collection.plex_rating_key); setShowConfirm(true) }}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              Delete
            </button>
          </div>
        </div>

        {/* Items list */}
        <div>
          <h4 className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
            Items ({items.length})
          </h4>
          {items.length === 0 ? (
            <p className="text-sm text-slate-400 italic">No items</p>
          ) : (
            <div className="rounded-lg border border-slate-200 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
              {items.map(item => (
                <div key={item.id} className="flex items-center justify-between px-3 py-2 gap-2">
                  <div className="min-w-0">
                    {item.movie_title ? (
                      <span className="text-sm font-semibold text-slate-800 dark:text-slate-200 truncate block">
                        {item.movie_title}
                      </span>
                    ) : (
                      <span className="text-sm text-slate-400 italic truncate block">—</span>
                    )}
                    <span className="text-xs font-mono text-slate-400">
                      {item.plex_rating_key}
                    </span>
                  </div>
                  {item.movie_title && (
                    <Link
                      to={`/movies/${item.item_id}`}
                      className="text-indigo-500 hover:text-indigo-700 flex-shrink-0 text-sm"
                    >
                      →
                    </Link>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <ConfirmDialog
        isOpen={showConfirm}
        title={`Delete ${collection.name}?`}
        confirmText="Delete"
        isDangerous
        onConfirm={() => { setShowConfirm(false); onDelete(collection.id, deleteFromPlex) }}
        onCancel={() => setShowConfirm(false)}
      >
        {collection.plex_rating_key && (
          <Checkbox
            label="Also delete from Plex"
            checked={deleteFromPlex}
            onChange={setDeleteFromPlex}
          />
        )}
      </ConfirmDialog>
    </div>
  )
}

export default CollectionDrawer
