import React, { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { Checkbox, Button } from '@/components/common'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { useClickOutside } from '@/hooks/useClickOutside'
import { formatSyncDate } from './plexUtils'

export type PlexItemDrawerItem = {
  id: number
  name: string
  description: string | null
  plex_rating_key: string | null
  last_synced_at: string | null
  enabled: boolean
  items: Array<{
    id: number
    plex_rating_key: string
    item_id: number
    movie_title: string | null
  }>
}

interface PlexItemDrawerProps {
  item: PlexItemDrawerItem
  fetchDetail: (id: number) => Promise<PlexItemDrawerItem>
  fetchArtwork: (id: number) => Promise<Blob>
  onClose: () => void
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: () => void
  badge?: React.ReactNode
  deleteConfirmExtra?: React.ReactNode
}

export function PlexItemDrawer({
  item,
  fetchDetail,
  fetchArtwork,
  onClose,
  onToggleEnabled,
  onPush,
  onDelete,
  badge,
  deleteConfirmExtra,
}: PlexItemDrawerProps) {
  const [artworkState, setArtworkState] = useState<{ url: string | null; loading: boolean }>({ url: null, loading: true })
  const [detailState, setDetailState] = useState<{ data: PlexItemDrawerItem | null; loading: boolean; error: string | null }>({ data: null, loading: true, error: null })
  const [showConfirm, setShowConfirm] = useState(false)
  const drawerRef = useRef<HTMLDivElement>(null)

  const artworkUrl = artworkState.url
  const isLoadingArtwork = artworkState.loading
  const detail = detailState.data
  const isLoadingDetail = detailState.loading
  const detailError = detailState.error

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setDetailState({ data: null, loading: true, error: null })
    fetchDetail(item.id)
      .then(d => setDetailState({ data: d, loading: false, error: null }))
      .catch(() => setDetailState({ data: null, loading: false, error: 'Failed to load details' }))
  }, [item.id, fetchDetail])

  useEffect(() => {
    if (!item.plex_rating_key) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setArtworkState({ url: null, loading: false })
      return
    }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setArtworkState({ url: null, loading: true })
    let objectUrl: string | null = null
    let cancelled = false
    fetchArtwork(item.id)
      .then(blob => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(blob)
        setArtworkState({ url: objectUrl, loading: false })
      })
      .catch(() => {
        if (!cancelled) setArtworkState({ url: null, loading: false })
      })
    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [item.id, item.plex_rating_key, fetchArtwork])

  useClickOutside(drawerRef, onClose)

  const items = detail?.items ?? []

  return (
    <div
      ref={drawerRef}
      className="w-80 flex-shrink-0 border-l border-edge bg-card flex flex-col overflow-hidden fixed right-0 top-16 h-[calc(100vh-4rem)] z-40"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-edge">
        <h3 className="font-semibold text-body truncate pr-2">
          {item.name}
        </h3>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close drawer"
          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors flex-shrink-0"
        >
          ✕
        </button>
      </div>

      <div className="overflow-y-auto flex-1 p-4 space-y-4">
        {/* Artwork */}
        {isLoadingArtwork ? (
          <div className="w-full h-32 rounded-lg bg-slate-200 dark:bg-slate-700 animate-pulse" />
        ) : artworkUrl ? (
          <img
            src={artworkUrl}
            alt={`${item.name} artwork`}
            className="w-full rounded-lg object-cover"
          />
        ) : (
          <div className="w-full h-32 rounded-lg bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-400 text-sm">
            No artwork
          </div>
        )}

        {/* Metadata */}
        <div className="flex items-center gap-2 flex-wrap text-sm text-hint">
          {badge}
          <span>{items.length} items</span>
          <span>·</span>
          <span>{formatSyncDate(item.last_synced_at)}</span>
        </div>

        {item.description && (
          <p className="text-sm text-hint">{item.description}</p>
        )}

        {/* Controls */}
        <div className="flex items-center justify-between gap-2 p-3 rounded-lg bg-subtle">
          <Checkbox
            label="Enabled"
            checked={item.enabled}
            onChange={checked => onToggleEnabled(item.id, checked)}
          />
          <div className="flex gap-2">
            <Button
              variant="primary"
              size="sm"
              onClick={() => onPush(item.id)}
              disabled={!item.enabled}
            >
              Push to Plex
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => setShowConfirm(true)}
            >
              Delete
            </Button>
          </div>
        </div>

        {/* Items list */}
        <div>
          <h4 className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
            Items ({isLoadingDetail ? '…' : items.length})
          </h4>
          {isLoadingDetail ? (
            <div className="space-y-2">
              {[1, 2, 3].map(n => (
                <div key={n} className="h-10 rounded bg-slate-200 dark:bg-slate-700 animate-pulse" />
              ))}
            </div>
          ) : detailError ? (
            <p className="text-sm text-red-500 dark:text-red-400">{detailError}</p>
          ) : items.length === 0 ? (
            <p className="text-sm text-slate-400 italic">No items</p>
          ) : (
            <div className="rounded-lg border border-slate-200 dark:border-slate-700 divide-y divide-slate-100 dark:divide-slate-700">
              {items.map(i => (
                <div key={i.id} className="flex items-center justify-between px-3 py-2 gap-2">
                  <div className="min-w-0">
                    {i.movie_title ? (
                      <span className="text-sm font-semibold text-slate-800 dark:text-slate-200 truncate block">
                        {i.movie_title}
                      </span>
                    ) : (
                      <span className="text-sm text-slate-400 italic truncate block">—</span>
                    )}
                    <span className="text-xs font-mono text-slate-400">
                      {i.plex_rating_key}
                    </span>
                  </div>
                  {i.movie_title && (
                    <Link
                      to={`/movies/${i.item_id}`}
                      className="text-primary-500 hover:text-primary-700 flex-shrink-0 text-sm"
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
        title={`Delete ${item.name}?`}
        confirmText="Delete"
        isDangerous
        onConfirm={() => { setShowConfirm(false); onDelete() }}
        onCancel={() => setShowConfirm(false)}
      >
        {deleteConfirmExtra}
      </ConfirmDialog>
    </div>
  )
}

export default PlexItemDrawer
