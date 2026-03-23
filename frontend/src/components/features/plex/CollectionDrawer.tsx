import React, { useState } from 'react'
import type { PlexCollection } from '../../../services/plexCollectionService'
import {
  getCollection,
  getCollectionArtwork,
} from '../../../services/plexCollectionService'
import { Checkbox } from '@/components/common/Checkbox'
import { BUILDER_LABELS } from './plexUtils'
import { PlexItemDrawer } from './PlexItemDrawer'
import type { PlexItemDrawerItem } from './PlexItemDrawer'

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
  const [deleteFromPlex, setDeleteFromPlex] = useState(!!collection.plex_rating_key)

  const badge = (
    <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">
      {BUILDER_LABELS[collection.builder_type] ?? collection.builder_type}
    </span>
  )

  const deleteConfirmExtra = collection.plex_rating_key ? (
    <Checkbox
      label="Also delete from Plex"
      checked={deleteFromPlex}
      onChange={setDeleteFromPlex}
    />
  ) : undefined

  return (
    <PlexItemDrawer
      item={collection as PlexItemDrawerItem}
      fetchDetail={id => getCollection(id) as Promise<PlexItemDrawerItem>}
      fetchArtwork={getCollectionArtwork}
      onClose={onClose}
      onToggleEnabled={onToggleEnabled}
      onPush={onPush}
      onDelete={() => onDelete(collection.id, deleteFromPlex)}
      badge={badge}
      deleteConfirmExtra={deleteConfirmExtra}
    />
  )
}

export default CollectionDrawer
