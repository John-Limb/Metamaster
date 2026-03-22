import React from 'react'
import type { PlexPlaylist } from '../../../services/plexCollectionService'
import { PlexItemRow } from './PlexItemRow'

interface PlaylistRowProps {
  playlist: PlexPlaylist
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number) => void
  onSelect: (id: number) => void
  isSelected: boolean
  selectable?: boolean
  bulkSelected?: boolean
  onBulkSelect?: (id: number, checked: boolean) => void
}

export function PlaylistRow({
  playlist,
  onToggleEnabled,
  onPush,
  onDelete,
  onSelect,
  isSelected,
  selectable,
  bulkSelected,
  onBulkSelect,
}: PlaylistRowProps) {
  return (
    <PlexItemRow
      item={playlist}
      isSelected={isSelected}
      onToggleEnabled={onToggleEnabled}
      onPush={onPush}
      onDelete={onDelete}
      onSelect={onSelect}
      selectable={selectable}
      bulkSelected={bulkSelected}
      onBulkSelect={onBulkSelect}
    />
  )
}

export default PlaylistRow
