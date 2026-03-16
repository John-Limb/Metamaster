import { useEffect, useState } from 'react'
import { usePlexCollectionStore } from '../stores/plexCollectionStore'
import { PlaylistCard } from '../components/features/plex/PlaylistCard'
import { Button } from '@/components/common/Button'
import { EmptyState } from '@/components/common/EmptyState'
import { SkeletonCard } from '@/components/common/Skeleton'

export function PlexPlaylistsPage() {
  const {
    playlists,
    playlistsLoading,
    playlistsError,
    fetchPlaylists,
    updatePlaylist,
    deletePlaylist,
    pushPlaylist,
    pullPlaylists,
    bulkDeletePlaylists,
  } = usePlexCollectionStore()

  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [selectMode, setSelectMode] = useState(false)

  useEffect(() => {
    fetchPlaylists()
  }, [fetchPlaylists])

  const handleTogglePlaylist = (id: number, enabled: boolean) => {
    updatePlaylist(id, { enabled })
  }

  const handleToggleSelect = (id: number, checked: boolean) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (checked) next.add(id)
      else next.delete(id)
      return next
    })
  }

  const handleSelectAll = () => {
    setSelectedIds(new Set(playlists.map(p => p.id)))
  }

  const handleBulkDelete = async () => {
    const ids = Array.from(selectedIds)
    setSelectedIds(new Set())
    setSelectMode(false)
    await bulkDeletePlaylists(ids)
  }

  const exitSelectMode = () => {
    setSelectMode(false)
    setSelectedIds(new Set())
  }

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
            Plex Playlists{playlists.length > 0 && <span className="text-slate-400 font-normal text-lg ml-2">({playlists.length})</span>}
          </h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Manage playlists synced to your Plex server.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {selectMode ? (
            <>
              <Button variant="outline" size="sm" onClick={handleSelectAll}>
                Select All
              </Button>
              {selectedIds.size > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  disabled={playlistsLoading}
                  onClick={handleBulkDelete}
                  className="border-red-300 text-red-600 hover:bg-red-50 dark:border-red-700 dark:text-red-400 dark:hover:bg-red-900/20"
                >
                  Delete Selected ({selectedIds.size})
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={exitSelectMode}>
                Cancel
              </Button>
            </>
          ) : (
            <>
              {playlists.length > 0 && (
                <Button variant="outline" size="sm" onClick={() => setSelectMode(true)}>
                  Select
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                disabled={playlistsLoading}
                onClick={() => pullPlaylists()}
              >
                Pull from Plex
              </Button>
            </>
          )}
        </div>
      </div>

      {playlistsError && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">
          {playlistsError}
        </div>
      )}

      {playlistsLoading && playlists.length === 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : playlists.length === 0 ? (
        <EmptyState
          variant="noData"
          title="No playlists yet"
          description="Pull from Plex to import your playlists."
          action={{
            label: 'Pull from Plex',
            onClick: pullPlaylists,
            disabled: playlistsLoading,
          }}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {playlists.map(pl => (
            <PlaylistCard
              key={pl.id}
              playlist={pl}
              onToggleEnabled={handleTogglePlaylist}
              onPush={pushPlaylist}
              onDelete={deletePlaylist}
              selectable={selectMode}
              selected={selectedIds.has(pl.id)}
              onSelect={handleToggleSelect}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default PlexPlaylistsPage
