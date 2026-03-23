import React from 'react'
import type { PlexPlaylist } from '../../../services/plexCollectionService'
import {
  getPlaylist,
  getPlaylistArtwork,
} from '../../../services/plexCollectionService'
import { PlexItemDrawer } from './PlexItemDrawer'
import type { PlexItemDrawerItem } from './PlexItemDrawer'

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
  return (
    <PlexItemDrawer
      item={playlist as PlexItemDrawerItem}
      fetchDetail={id => getPlaylist(id) as Promise<PlexItemDrawerItem>}
      fetchArtwork={getPlaylistArtwork}
      onClose={onClose}
      onToggleEnabled={onToggleEnabled}
      onPush={onPush}
      onDelete={() => onDelete(playlist.id)}
    />
  )
}

export default PlaylistDrawer
