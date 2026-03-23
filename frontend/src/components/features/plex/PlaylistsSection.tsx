import React from 'react'
import type { PlexPlaylist } from '../../../services/plexCollectionService'
import { Button, AlertMessage } from '@/components/common'
import { EmptyState } from '@/components/common/EmptyState'
import { SkeletonTable } from '@/components/common/Skeleton'
import { PlexItemRow } from './PlexItemRow'

const TABLE_HEADERS = (
  <tr className="border-b border-edge">
    <th className="py-2 pl-3 pr-2 text-left text-xs font-medium text-hint uppercase tracking-wider">Name</th>
    <th className="py-2 px-2 text-left text-xs font-medium text-hint uppercase tracking-wider">Items</th>
    <th className="py-2 px-2 text-left text-xs font-medium text-hint uppercase tracking-wider">Last Synced</th>
    <th className="py-2 pl-2 pr-3 text-right text-xs font-medium text-hint uppercase tracking-wider">Actions</th>
  </tr>
)

interface PlaylistsSectionProps {
  playlists: PlexPlaylist[]
  playlistsLoading: boolean
  playlistsError: string | null
  selectedPlaylistId: number | null
  selectMode: boolean
  selectedIds: Set<number>
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number) => void
  onSelect: (id: number) => void
  onPull: () => void
  onToggleSelect: (id: number, checked: boolean) => void
  onBulkDelete: () => void
  onEnterSelectMode: () => void
  onExitSelectMode: () => void
  onSelectAll: () => void
}

export function PlaylistsSection({
  playlists,
  playlistsLoading,
  playlistsError,
  selectedPlaylistId,
  selectMode,
  selectedIds,
  onToggleEnabled,
  onPush,
  onDelete,
  onSelect,
  onPull,
  onToggleSelect,
  onBulkDelete,
  onEnterSelectMode,
  onExitSelectMode,
  onSelectAll,
}: PlaylistsSectionProps) {
  return (
    <section>
      <div className="flex items-center justify-between gap-4 mb-4">
        <h2 className="text-lg font-semibold text-body">
          Playlists {playlists.length > 0 && <span className="text-hint font-normal text-sm">({playlists.length})</span>}
        </h2>
        <div className="flex items-center gap-2">
          {selectMode ? (
            <>
              <Button variant="outline" size="sm" onClick={onSelectAll}>Select All</Button>
              {selectedIds.size > 0 && (
                <Button variant="danger" size="sm" disabled={playlistsLoading} onClick={onBulkDelete}>
                  Delete Selected ({selectedIds.size})
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={onExitSelectMode}>Cancel</Button>
            </>
          ) : (
            <>
              {playlists.length > 0 && <Button variant="outline" size="sm" onClick={onEnterSelectMode}>Select</Button>}
              <Button variant="outline" size="sm" disabled={playlistsLoading} onClick={onPull}>Pull from Plex</Button>
            </>
          )}
        </div>
      </div>

      {playlistsError && (
        <AlertMessage variant="error" message={playlistsError} className="mb-4" />
      )}

      {playlistsLoading && playlists.length === 0 ? (
        <SkeletonTable columns={4} rows={5} showHeader={false} />
      ) : playlists.length === 0 ? (
        <EmptyState variant="noData" title="No playlists yet" description="Pull from Plex to import your playlists." action={{ label: 'Pull from Plex', onClick: onPull, disabled: playlistsLoading }} />
      ) : (
        <div className="rounded-xl border border-edge bg-card overflow-hidden">
          <table className="w-full">
            <thead>{TABLE_HEADERS}</thead>
            <tbody className="divide-y divide-rule">
              {playlists.map(pl => (
                <PlexItemRow
                  key={pl.id}
                  item={pl}
                  onToggleEnabled={onToggleEnabled}
                  onPush={onPush}
                  onDelete={onDelete}
                  onSelect={onSelect}
                  isSelected={selectedPlaylistId === pl.id}
                  selectable={selectMode}
                  bulkSelected={selectedIds.has(pl.id)}
                  onBulkSelect={onToggleSelect}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default PlaylistsSection
