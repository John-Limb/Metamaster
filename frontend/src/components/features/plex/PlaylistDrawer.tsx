import React, { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import type { PlexPlaylist } from '../../../services/plexCollectionService'
import {
  getPlaylist,
  getPlaylistArtwork,
} from '../../../services/plexCollectionService'
import { Checkbox } from '@/components/common/Checkbox'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { formatSyncDate } from './plexUtils'

interface PlaylistDrawerProps {
  playlist: PlexPlaylist
  onClose: () => void
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number) => void
}

export function PlaylistDrawer({
  playlist,
  onClose,
  onToggleEnabled,
  onPush,
  onDelete,
}: PlaylistDrawerProps) {
  const [artworkUrl, setArtworkUrl] = useState<string | null>(null)
  const [detail, setDetail] = useState<PlexPlaylist | null>(null)
  const [showConfirm, setShowConfirm] = useState(false)
  const drawerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getPlaylist(playlist.id).then(setDetail).catch(() => {})
  }, [playlist.id])

  useEffect(() => {
    if (!playlist.plex_rating_key) return
    let objectUrl: string | null = null
    let cancelled = false
    getPlaylistArtwork(playlist.id)
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
  }, [playlist.id, playlist.plex_rating_key])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

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
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-700">
        <h3 className="font-semibold text-slate-900 dark:text-white truncate pr-2">
          {playlist.name}
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
        {artworkUrl ? (
          <img
            src={artworkUrl}
            alt={`${playlist.name} artwork`}
            className="w-full rounded-lg object-cover"
          />
        ) : (
          <div className="w-full h-32 rounded-lg bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-400 text-sm">
            No artwork
          </div>
        )}

        <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <span>{items.length} items</span>
          <span>·</span>
          <span>{formatSyncDate(playlist.last_synced_at)}</span>
        </div>

        {playlist.description && (
          <p className="text-sm text-slate-500 dark:text-slate-400">{playlist.description}</p>
        )}

        <div className="flex items-center justify-between gap-2 p-3 rounded-lg bg-slate-50 dark:bg-slate-700/50">
          <Checkbox
            label="Enabled"
            checked={playlist.enabled}
            onChange={checked => onToggleEnabled(playlist.id, checked)}
          />
          <div className="flex gap-2">
            <button
              onClick={() => onPush(playlist.id)}
              disabled={!playlist.enabled}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white transition-colors"
            >
              Push to Plex
            </button>
            <button
              onClick={() => setShowConfirm(true)}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              Delete
            </button>
          </div>
        </div>

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
        title={`Delete ${playlist.name}?`}
        confirmText="Delete"
        isDangerous
        onConfirm={() => { setShowConfirm(false); onDelete(playlist.id) }}
        onCancel={() => setShowConfirm(false)}
      />
    </div>
  )
}

export default PlaylistDrawer
