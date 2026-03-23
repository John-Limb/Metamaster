import React, { useState } from 'react'
import { Checkbox, CheckboxInput, Button } from '@/components/common'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { formatSyncDate } from './plexUtils'

interface PlexItemRowProps {
  item: {
    id: number
    name: string
    plex_rating_key: string | null
    last_synced_at: string | null
    enabled: boolean
    items: unknown[]
  }
  isSelected: boolean
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => Promise<void> | void
  // CollectionRow passes a nullary closure here; the id arg is intentionally ignored (TS callback contravariance)
  onDelete: (id: number) => void
  onSelect: (id: number) => void
  badge?: React.ReactNode    // must be a <td> element
  deleteConfirmExtra?: React.ReactNode
  onDeleteConfirm?: () => void  // if provided, overrides the default onDelete(item.id) call
  selectable?: boolean
  bulkSelected?: boolean
  onBulkSelect?: (id: number, checked: boolean) => void
}

export function PlexItemRow({
  item,
  isSelected,
  onToggleEnabled,
  onPush,
  onDelete,
  onSelect,
  badge,
  deleteConfirmExtra,
  onDeleteConfirm,
  selectable,
  bulkSelected,
  onBulkSelect,
}: PlexItemRowProps) {
  const [showConfirm, setShowConfirm] = useState(false)
  const [isPushing, setIsPushing] = useState(false)

  const handleDeleteConfirm = () => {
    setShowConfirm(false)
    if (onDeleteConfirm) {
      onDeleteConfirm()
    } else {
      onDelete(item.id)
    }
  }

  return (
    <>
      <tr
        className={`border-l-4 transition-colors ${
          isSelected
            ? 'border-primary-500 bg-primary-500/10 dark:bg-primary-500/15'
            : 'border-transparent hover:bg-subtle'
        }`}
      >
        <td className="py-2 pl-3 pr-2">
          <div className="flex items-center gap-2">
            {selectable && (
              <CheckboxInput
                checked={!!bulkSelected}
                onChange={checked => onBulkSelect?.(item.id, checked)}
                aria-label={`Select ${item.name}`}
              />
            )}
            <button
              type="button"
              onClick={() => onSelect(item.id)}
              className="text-left font-medium text-body hover:text-primary-600 dark:hover:text-primary-400 hover:underline transition-colors truncate max-w-xs"
            >
              {item.name}
            </button>
          </div>
        </td>
        {badge}
        <td className="py-2 px-2 text-sm text-hint">
          {item.items.length}
        </td>
        <td className="py-2 px-2 text-sm text-hint whitespace-nowrap">
          {formatSyncDate(item.last_synced_at)}
        </td>
        <td className="py-2 pl-2 pr-3">
          <div className="flex items-center justify-end gap-2">
            <Checkbox
              label="Enabled"
              checked={item.enabled}
              onChange={checked => onToggleEnabled(item.id, checked)}
            />
            <Button
              variant="primary"
              size="sm"
              onClick={async () => {
                setIsPushing(true)
                try {
                  await onPush(item.id)
                } finally {
                  setIsPushing(false)
                }
              }}
              disabled={!item.enabled || isPushing}
              loading={isPushing}
            >
              Push
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => setShowConfirm(true)}
            >
              Delete
            </Button>
          </div>
        </td>
      </tr>

      <ConfirmDialog
        isOpen={showConfirm}
        title={`Delete ${item.name}?`}
        confirmText="Delete"
        isDangerous
        onConfirm={handleDeleteConfirm}
        onCancel={() => setShowConfirm(false)}
      >
        {deleteConfirmExtra}
      </ConfirmDialog>
    </>
  )
}

export default PlexItemRow
