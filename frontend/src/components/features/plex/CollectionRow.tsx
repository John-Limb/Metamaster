import React, { useState } from 'react'
import type { PlexCollection } from '../../../services/plexCollectionService'
import { Checkbox } from '@/components/common/Checkbox'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { BUILDER_LABELS, formatSyncDate } from './plexUtils'

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
  const [showConfirm, setShowConfirm] = useState(false)
  const [deleteFromPlex, setDeleteFromPlex] = useState(!!collection.plex_rating_key)

  const handleDeleteClick = () => {
    setDeleteFromPlex(!!collection.plex_rating_key)
    setShowConfirm(true)
  }

  return (
    <>
      <tr
        className={`border-l-2 transition-colors ${
          isSelected
            ? 'border-indigo-500 bg-slate-800/50'
            : 'border-transparent hover:bg-slate-800/30'
        }`}
      >
        <td className="py-2 pl-3 pr-2">
          <button
            onClick={() => onSelect(collection.id)}
            className="text-left font-medium text-slate-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 hover:underline transition-colors truncate max-w-xs"
          >
            {collection.name}
          </button>
        </td>
        <td className="py-2 px-2">
          <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400">
            {BUILDER_LABELS[collection.builder_type] ?? collection.builder_type}
          </span>
        </td>
        <td className="py-2 px-2 text-sm text-slate-500 dark:text-slate-400">
          {collection.items.length}
        </td>
        <td className="py-2 px-2 text-sm text-slate-500 dark:text-slate-400 whitespace-nowrap">
          {formatSyncDate(collection.last_synced_at)}
        </td>
        <td className="py-2 pl-2 pr-3">
          <div className="flex items-center justify-end gap-2">
            <Checkbox
              label="Enabled"
              checked={collection.enabled}
              onChange={checked => onToggleEnabled(collection.id, checked)}
            />
            <button
              onClick={() => onPush(collection.id)}
              disabled={!collection.enabled}
              className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors"
            >
              Push
            </button>
            <button
              onClick={handleDeleteClick}
              className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              Delete
            </button>
          </div>
        </td>
      </tr>

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
    </>
  )
}

export default CollectionRow
