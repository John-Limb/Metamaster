import React, { useState } from 'react'
import type { PlexCollection } from '../../../services/plexCollectionService'
import { Checkbox } from '@/components/common/Checkbox'
import { BUILDER_LABELS } from './plexUtils'
import { PlexItemRow } from './PlexItemRow'

interface CollectionRowProps {
  collection: PlexCollection
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number, deleteFromPlex: boolean) => void
  onSelect: (id: number) => void
  isSelected: boolean
}

export function CollectionRow({
  collection,
  onToggleEnabled,
  onPush,
  onDelete,
  onSelect,
  isSelected,
}: CollectionRowProps) {
  const [deleteFromPlex, setDeleteFromPlex] = useState(!!collection.plex_rating_key)

  const badge = (
    <td className="py-2 px-2">
      <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">
        {BUILDER_LABELS[collection.builder_type] ?? collection.builder_type}
      </span>
    </td>
  )

  const deleteConfirmExtra = collection.plex_rating_key ? (
    <Checkbox
      label="Also delete from Plex"
      checked={deleteFromPlex}
      onChange={setDeleteFromPlex}
    />
  ) : undefined

  return (
    <PlexItemRow
      item={collection}
      isSelected={isSelected}
      onToggleEnabled={onToggleEnabled}
      onPush={onPush}
      onDelete={() => onDelete(collection.id, deleteFromPlex)}
      onSelect={onSelect}
      badge={badge}
      deleteConfirmExtra={deleteConfirmExtra}
    />
  )
}

export default CollectionRow
