import React, { useState } from 'react'
import type { PlexPlaylist } from '../../../services/plexCollectionService'
import { Checkbox, CheckboxInput } from '@/components/common/Checkbox'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { formatSyncDate } from './plexUtils'

interface PlaylistRowProps {
  playlist: PlexPlaylist
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number) => void
  onSelect: (id: number) => void
  isSelected: boolean
  selectable?: boolean
  bulkSelected?: boolean
  onBulkSelect?: (id: number, selected: boolean) => void
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
  const [showConfirm, setShowConfirm] = useState(false)

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
          <div className="flex items-center gap-2">
            {selectable && (
              <CheckboxInput
                checked={!!bulkSelected}
                onChange={checked => onBulkSelect?.(playlist.id, checked)}
                aria-label={`Select ${playlist.name}`}
              />
            )}
            <button
              onClick={() => onSelect(playlist.id)}
              className="text-left font-medium text-slate-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 hover:underline transition-colors truncate max-w-xs"
            >
              {playlist.name}
            </button>
          </div>
        </td>
        <td className="py-2 px-2 text-sm text-slate-500 dark:text-slate-400">
          {playlist.items.length}
        </td>
        <td className="py-2 px-2 text-sm text-slate-500 dark:text-slate-400 whitespace-nowrap">
          {formatSyncDate(playlist.last_synced_at)}
        </td>
        <td className="py-2 pl-2 pr-3">
          <div className="flex items-center justify-end gap-2">
            <Checkbox
              label="Enabled"
              checked={playlist.enabled}
              onChange={checked => onToggleEnabled(playlist.id, checked)}
            />
            <button
              onClick={() => onPush(playlist.id)}
              disabled={!playlist.enabled}
              className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors"
            >
              Push
            </button>
            <button
              onClick={() => setShowConfirm(true)}
              className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            >
              Delete
            </button>
          </div>
        </td>
      </tr>

      <ConfirmDialog
        isOpen={showConfirm}
        title={`Delete ${playlist.name}?`}
        confirmText="Delete"
        isDangerous
        onConfirm={() => { setShowConfirm(false); onDelete(playlist.id) }}
        onCancel={() => setShowConfirm(false)}
      />
    </>
  )
}

export default PlaylistRow
