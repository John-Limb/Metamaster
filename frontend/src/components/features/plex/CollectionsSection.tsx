import React from 'react'
import type { PlexCollection } from '../../../services/plexCollectionService'
import { Button, AlertMessage } from '@/components/common'
import { EmptyState } from '@/components/common/EmptyState'
import { SkeletonTable } from '@/components/common/Skeleton'
import { CollectionRow } from './CollectionRow'

const TABLE_HEADERS = (
  <tr className="border-b border-edge">
    <th className="py-2 pl-3 pr-2 text-left text-xs font-medium text-hint uppercase tracking-wider">Name</th>
    <th className="py-2 px-2 text-left text-xs font-medium text-hint uppercase tracking-wider">Type</th>
    <th className="py-2 px-2 text-left text-xs font-medium text-hint uppercase tracking-wider">Items</th>
    <th className="py-2 px-2 text-left text-xs font-medium text-hint uppercase tracking-wider">Last Synced</th>
    <th className="py-2 pl-2 pr-3 text-right text-xs font-medium text-hint uppercase tracking-wider">Actions</th>
  </tr>
)

interface CollectionsSectionProps {
  collections: PlexCollection[]
  collectionsLoading: boolean
  collectionsError: string | null
  selectedCollectionId: number | null
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number, deleteFromPlex: boolean) => void
  onSelect: (id: number) => void
  onPull: () => void
  onImportYaml: () => void
  onNew: () => void
}

function CollectionTable({
  rows,
  selectedCollectionId,
  onToggleEnabled,
  onPush,
  onDelete,
  onSelect,
}: {
  rows: PlexCollection[]
  selectedCollectionId: number | null
  onToggleEnabled: (id: number, enabled: boolean) => void
  onPush: (id: number) => void
  onDelete: (id: number, deleteFromPlex: boolean) => void
  onSelect: (id: number) => void
}) {
  return (
    <table className="w-full">
      <thead>{TABLE_HEADERS}</thead>
      <tbody className="divide-y divide-rule">
        {rows.map(col => (
          <CollectionRow
            key={col.id}
            collection={col}
            onToggleEnabled={onToggleEnabled}
            onPush={onPush}
            onDelete={onDelete}
            onSelect={onSelect}
            isSelected={selectedCollectionId === col.id}
          />
        ))}
      </tbody>
    </table>
  )
}

export function CollectionsSection({
  collections,
  collectionsLoading,
  collectionsError,
  selectedCollectionId,
  onToggleEnabled,
  onPush,
  onDelete,
  onSelect,
  onPull,
  onImportYaml,
  onNew,
}: CollectionsSectionProps) {
  const movieCollections = collections.filter(
    c => c.content_type === 'movie' || c.content_type === null
  )
  const tvCollections = collections.filter(c => c.content_type === 'tv_show')
  const rowProps = { selectedCollectionId, onToggleEnabled, onPush, onDelete, onSelect }
  const hasBoth = movieCollections.length > 0 && tvCollections.length > 0

  return (
    <section>
      <div className="flex items-center justify-between gap-4 mb-4">
        <h2 className="text-lg font-semibold text-body">Collections</h2>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onPull} disabled={collectionsLoading}>Pull from Plex</Button>
          <Button variant="outline" size="sm" onClick={onImportYaml}>Import YAML</Button>
          <Button variant="primary" size="sm" onClick={onNew}>New Collection</Button>
        </div>
      </div>

      {collectionsError && (
        <AlertMessage variant="error" message={collectionsError} className="mb-4" />
      )}

      {collectionsLoading && collections.length === 0 ? (
        <SkeletonTable columns={5} rows={5} showHeader={false} />
      ) : collections.length === 0 ? (
        <EmptyState variant="noData" title="No collections yet" description="Create one or pull from Plex." action={{ label: 'Pull from Plex', onClick: onPull, disabled: collectionsLoading }} />
      ) : (
        <div className="rounded-xl border border-edge bg-card overflow-hidden">
          {movieCollections.length > 0 && (
            <>
              {hasBoth && <div className="px-3 py-1.5 bg-subtle text-xs font-semibold text-hint uppercase tracking-wider">Movies</div>}
              <CollectionTable rows={movieCollections} {...rowProps} />
            </>
          )}
          {tvCollections.length > 0 && (
            <>
              <div className="px-3 py-1.5 bg-subtle text-xs font-semibold text-hint uppercase tracking-wider border-t border-rule">TV Shows</div>
              <CollectionTable rows={tvCollections} {...rowProps} />
            </>
          )}
        </div>
      )}
    </section>
  )
}

export default CollectionsSection
