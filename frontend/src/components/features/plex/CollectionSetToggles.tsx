import React from 'react'
import { usePlexCollectionStore } from '../../../stores/plexCollectionStore'
import type { SetType } from '../../../services/plexCollectionService'
import { Checkbox } from '@/components/common/Checkbox'

const SET_LABELS: Record<SetType, string> = {
  franchise: 'Franchise',
  genre: 'Genre',
  decade: 'Decade',
}

function formatRunDate(dateStr: string | null): string {
  if (!dateStr) return 'Never run'
  return new Date(dateStr).toLocaleString()
}

export function CollectionSetToggles() {
  const { collectionSets, setsLoading, toggleCollectionSet } = usePlexCollectionStore()

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
      <h2 className="text-base font-semibold text-slate-800 dark:text-slate-200 mb-3">
        Default Collection Sets
      </h2>
      <div className="divide-y divide-slate-100 dark:divide-slate-700">
        {collectionSets.map(set => (
          <div key={set.set_type} className="flex items-center justify-between py-3 gap-4">
            <div>
              <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
                {SET_LABELS[set.set_type]}
              </p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {formatRunDate(set.last_run_at)}
              </p>
            </div>
            <Checkbox
              label="Enabled"
              checked={set.enabled}
              disabled={setsLoading}
              onChange={checked => toggleCollectionSet(set.set_type, checked)}
            />
          </div>
        ))}
        {collectionSets.length === 0 && !setsLoading && (
          <p className="py-3 text-sm text-slate-500 dark:text-slate-400">
            No collection sets available.
          </p>
        )}
      </div>
    </div>
  )
}

export default CollectionSetToggles
