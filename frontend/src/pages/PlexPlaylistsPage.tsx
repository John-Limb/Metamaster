import React, { useCallback, useEffect, useState } from 'react'
import { useEscapeKey } from '@/hooks'
import { usePlexCollectionStore } from '../stores/plexCollectionStore'
import { PlexItemRow } from '../components/features/plex/PlexItemRow'
import { PlaylistDrawer } from '../components/features/plex/PlaylistDrawer'
import { Button, AlertMessage } from '@/components/common'
import { EmptyState } from '@/components/common/EmptyState'
import { SkeletonTable } from '@/components/common/Skeleton'

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
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<number | null>(null)

  useEffect(() => {
    fetchPlaylists()
  }, [fetchPlaylists])

  const handleCloseDrawer = useCallback(() => {
    setSelectedPlaylistId(null)
  }, [])

  useEscapeKey(handleCloseDrawer, selectedPlaylistId !== null)

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

  const selectedPlaylist = selectedPlaylistId
    ? playlists.find(p => p.id === selectedPlaylistId) ?? null
    : null

  const tableHeaders = (
    <tr className="border-b border-edge">
      <th className="py-2 pl-3 pr-2 text-left text-xs font-medium text-hint uppercase tracking-wider">Name</th>
      <th className="py-2 px-2 text-left text-xs font-medium text-hint uppercase tracking-wider">Items</th>
      <th className="py-2 px-2 text-left text-xs font-medium text-hint uppercase tracking-wider">Last Synced</th>
      <th className="py-2 pl-2 pr-3 text-right text-xs font-medium text-hint uppercase tracking-wider">Actions</th>
    </tr>
  )


  return (
    <div className="flex gap-0 min-h-0">
      <div className={`flex-1 min-w-0 space-y-8 ${selectedPlaylist ? 'overflow-hidden' : ''}`}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-body">
              Plex Playlists{playlists.length > 0 && <span className="text-hint font-normal text-lg ml-2">({playlists.length})</span>}
            </h1>
            <p className="text-hint mt-1">
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

        {playlistsError && <AlertMessage variant="error" message={playlistsError} />}

        {playlistsLoading && playlists.length === 0 ? (
          <SkeletonTable columns={4} rows={5} showHeader={false} />
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
          <div className="rounded-xl border border-edge bg-card overflow-hidden">
            <table className="w-full">
              <thead>{tableHeaders}</thead>
              <tbody className="divide-y divide-rule">
                {playlists.map(pl => (
                  <PlexItemRow
                    key={pl.id}
                    item={pl}
                    onToggleEnabled={(id, enabled) => updatePlaylist(id, { enabled })}
                    onPush={pushPlaylist}
                    onDelete={deletePlaylist}
                    onSelect={setSelectedPlaylistId}
                    isSelected={selectedPlaylistId === pl.id}
                    selectable={selectMode}
                    bulkSelected={selectedIds.has(pl.id)}
                    onBulkSelect={handleToggleSelect}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedPlaylist && (
        <PlaylistDrawer
          playlist={selectedPlaylist}
          onClose={handleCloseDrawer}
          onToggleEnabled={(id, enabled) => updatePlaylist(id, { enabled })}
          onPush={pushPlaylist}
          onDelete={deletePlaylist}
        />
      )}
    </div>
  )
}

export default PlexPlaylistsPage
