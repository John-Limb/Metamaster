import React, { useCallback, useEffect, useState } from 'react'
import { usePlexCollectionStore } from '../stores/plexCollectionStore'
import { CollectionDrawer } from '../components/features/plex/CollectionDrawer'
import { PlaylistDrawer } from '../components/features/plex/PlaylistDrawer'
import { CollectionForm } from '../components/features/plex/CollectionForm'
import { CollectionSetToggles } from '../components/features/plex/CollectionSetToggles'
import { YamlImportModal } from '../components/features/plex/YamlImportModal'
import { CollectionsSection } from '../components/features/plex/CollectionsSection'
import { PlaylistsSection } from '../components/features/plex/PlaylistsSection'
import { Button, AlertMessage } from '@/components/common'
import type { CollectionCreate } from '../services/plexCollectionService'

export function PlexCollectionsPage() {
  const {
    collections, collectionsLoading, collectionsError,
    playlists, playlistsLoading, playlistsError,
    fetchCollections, fetchPlaylists, fetchCollectionSets,
    triggerDiscovery, createCollection, updateCollection, deleteCollection,
    pushCollection, pullCollections, pushAllCollections, pushAllLoading, pushAllError,
    updatePlaylist, deletePlaylist, pushPlaylist, pullPlaylists, bulkDeletePlaylists,
  } = usePlexCollectionStore()

  const [showForm, setShowForm] = useState(false)
  const [showYamlImport, setShowYamlImport] = useState(false)
  const [discoverMessage, setDiscoverMessage] = useState<string | null>(null)
  const [selectedPlaylistIds, setSelectedPlaylistIds] = useState<Set<number>>(new Set())
  const [selectMode, setSelectMode] = useState(false)
  const [selectedCollectionId, setSelectedCollectionId] = useState<number | null>(null)
  const [selectedPlaylistId, setSelectedPlaylistId] = useState<number | null>(null)

  useEffect(() => {
    fetchCollections()
    fetchPlaylists()
    fetchCollectionSets()
  }, [fetchCollections, fetchPlaylists, fetchCollectionSets])

  const handleCloseDrawer = useCallback(() => {
    setSelectedCollectionId(null)
    setSelectedPlaylistId(null)
  }, [])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') handleCloseDrawer() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [handleCloseDrawer])

  const handleSelectCollection = (id: number) => { setSelectedCollectionId(id); setSelectedPlaylistId(null) }
  const handleSelectPlaylist = (id: number) => { setSelectedPlaylistId(id); setSelectedCollectionId(null) }

  const handleDiscover = async () => {
    setDiscoverMessage(null)
    try {
      const result = await triggerDiscovery()
      setDiscoverMessage(result.message)
    } catch {
      setDiscoverMessage('Failed to start discovery.')
    }
  }

  const handleToggleSelect = (id: number, checked: boolean) => {
    setSelectedPlaylistIds(prev => {
      const next = new Set(prev)
      if (checked) next.add(id); else next.delete(id)
      return next
    })
  }

  const handleBulkDelete = async () => {
    const ids = Array.from(selectedPlaylistIds)
    setSelectedPlaylistIds(new Set())
    setSelectMode(false)
    await bulkDeletePlaylists(ids)
  }

  const selectedCollection = selectedCollectionId ? collections.find(c => c.id === selectedCollectionId) ?? null : null
  const selectedPlaylist = selectedPlaylistId ? playlists.find(p => p.id === selectedPlaylistId) ?? null : null
  const drawerOpen = selectedCollection !== null || selectedPlaylist !== null

  return (
    <div className="flex gap-0 min-h-0">
      <div className={`flex-1 min-w-0 space-y-8 transition-all duration-200 ${drawerOpen ? 'pr-80' : ''}`}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-body">Plex Collections</h1>
            <p className="text-hint mt-1">Manage collections and playlists synced to your Plex server.</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => pushAllCollections()} disabled={pushAllLoading}>
              {pushAllLoading ? 'Queuing\u2026' : 'Push All to Plex'}
            </Button>
            <Button variant="primary" size="sm" onClick={handleDiscover}>Discover Collections</Button>
          </div>
        </div>

        {discoverMessage && <AlertMessage variant="success" message={discoverMessage} />}
        {pushAllError && <AlertMessage variant="error" message={pushAllError} />}

        <CollectionSetToggles />

        <CollectionsSection
          collections={collections}
          collectionsLoading={collectionsLoading}
          collectionsError={collectionsError}
          selectedCollectionId={selectedCollectionId}
          onToggleEnabled={(id, enabled) => updateCollection(id, { enabled })}
          onPush={pushCollection}
          onDelete={deleteCollection}
          onSelect={handleSelectCollection}
          onPull={pullCollections}
          onImportYaml={() => setShowYamlImport(true)}
          onNew={() => setShowForm(true)}
        />

        <PlaylistsSection
          playlists={playlists}
          playlistsLoading={playlistsLoading}
          playlistsError={playlistsError}
          selectedPlaylistId={selectedPlaylistId}
          selectMode={selectMode}
          selectedIds={selectedPlaylistIds}
          onToggleEnabled={(id, enabled) => updatePlaylist(id, { enabled })}
          onPush={pushPlaylist}
          onDelete={deletePlaylist}
          onSelect={handleSelectPlaylist}
          onPull={pullPlaylists}
          onToggleSelect={handleToggleSelect}
          onBulkDelete={handleBulkDelete}
          onEnterSelectMode={() => setSelectMode(true)}
          onExitSelectMode={() => { setSelectMode(false); setSelectedPlaylistIds(new Set()) }}
          onSelectAll={() => setSelectedPlaylistIds(new Set(playlists.map(p => p.id)))}
        />
      </div>

      {selectedCollection && (
        <CollectionDrawer
          collection={selectedCollection}
          onClose={handleCloseDrawer}
          onToggleEnabled={(id, enabled) => updateCollection(id, { enabled })}
          onPush={pushCollection}
          onDelete={deleteCollection}
        />
      )}
      {selectedPlaylist && (
        <PlaylistDrawer
          playlist={selectedPlaylist}
          onClose={handleCloseDrawer}
          onToggleEnabled={(id, enabled) => updatePlaylist(id, { enabled })}
          onPush={pushPlaylist}
          onDelete={deletePlaylist}
        />
      )}

      {showForm && (
        <CollectionForm
          onSubmit={async (data: CollectionCreate) => { await createCollection(data); setShowForm(false) }}
          onCancel={() => setShowForm(false)}
        />
      )}
      {showYamlImport && (
        <YamlImportModal
          onClose={() => setShowYamlImport(false)}
          onImported={() => { fetchCollections(); fetchPlaylists() }}
        />
      )}
    </div>
  )
}

export default PlexCollectionsPage
