import React, { useEffect, useState } from 'react'
import { usePlexCollectionStore } from '../stores/plexCollectionStore'
import { CollectionCard } from '../components/features/plex/CollectionCard'
import { PlaylistCard } from '../components/features/plex/PlaylistCard'
import { CollectionForm } from '../components/features/plex/CollectionForm'
import { CollectionSetToggles } from '../components/features/plex/CollectionSetToggles'
import { YamlImportModal } from '../components/features/plex/YamlImportModal'
import type { CollectionCreate } from '../services/plexCollectionService'

export function PlexCollectionsPage() {
  const {
    collections,
    collectionsLoading,
    collectionsError,
    playlists,
    playlistsLoading,
    playlistsError,
    fetchCollections,
    fetchPlaylists,
    fetchCollectionSets,
    triggerDiscovery,
    createCollection,
    updateCollection,
    deleteCollection,
    pushCollection,
    pullCollections,
    updatePlaylist,
    deletePlaylist,
    pushPlaylist,
    pullPlaylists,
  } = usePlexCollectionStore()

  const [showForm, setShowForm] = useState(false)
  const [showYamlImport, setShowYamlImport] = useState(false)
  const [discoverMessage, setDiscoverMessage] = useState<string | null>(null)

  useEffect(() => {
    fetchCollections()
    fetchPlaylists()
    fetchCollectionSets()
  }, [fetchCollections, fetchPlaylists, fetchCollectionSets])

  const handleToggleCollection = (id: number, enabled: boolean) => {
    updateCollection(id, { enabled })
  }

  const handleTogglePlaylist = (id: number, enabled: boolean) => {
    updatePlaylist(id, { enabled })
  }

  const handleCreateCollection = async (data: CollectionCreate) => {
    await createCollection(data)
    setShowForm(false)
  }

  const handleDiscover = async () => {
    setDiscoverMessage(null)
    try {
      const result = await triggerDiscovery()
      setDiscoverMessage(result.message)
    } catch {
      setDiscoverMessage('Failed to start discovery.')
    }
  }

  const handleYamlImported = () => {
    fetchCollections()
    fetchPlaylists()
  }

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Plex Collections</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Manage collections and playlists synced to your Plex server.
          </p>
        </div>
        <button
          onClick={handleDiscover}
          className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 hover:bg-indigo-700 text-white transition-colors shrink-0"
        >
          Discover Collections
        </button>
      </div>

      {discoverMessage && (
        <div className="rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 px-4 py-3 text-sm text-green-700 dark:text-green-400">
          {discoverMessage}
        </div>
      )}

      {/* Collection Sets */}
      <CollectionSetToggles />

      {/* Collections section */}
      <section>
        <div className="flex items-center justify-between gap-4 mb-4">
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Collections</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => pullCollections()}
              disabled={collectionsLoading}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 transition-colors"
            >
              Pull from Plex
            </button>
            <button
              onClick={() => setShowYamlImport(true)}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
            >
              Import YAML
            </button>
            <button
              onClick={() => setShowForm(true)}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium bg-indigo-600 hover:bg-indigo-700 text-white transition-colors"
            >
              New Collection
            </button>
          </div>
        </div>

        {collectionsError && (
          <div className="mb-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">
            {collectionsError}
          </div>
        )}

        {collectionsLoading && collections.length === 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-40 rounded-xl bg-slate-200 dark:bg-slate-700 animate-pulse" />
            ))}
          </div>
        ) : collections.length === 0 ? (
          <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-6 py-12 text-center">
            <p className="text-slate-500 dark:text-slate-400">No collections yet. Create one or pull from Plex.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {collections.map(col => (
              <CollectionCard
                key={col.id}
                collection={col}
                onToggleEnabled={handleToggleCollection}
                onPush={pushCollection}
                onDelete={deleteCollection}
              />
            ))}
          </div>
        )}
      </section>

      {/* Playlists section */}
      <section>
        <div className="flex items-center justify-between gap-4 mb-4">
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200">Playlists</h2>
          <button
            onClick={() => pullPlaylists()}
            disabled={playlistsLoading}
            className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 transition-colors"
          >
            Pull from Plex
          </button>
        </div>

        {playlistsError && (
          <div className="mb-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">
            {playlistsError}
          </div>
        )}

        {playlistsLoading && playlists.length === 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-36 rounded-xl bg-slate-200 dark:bg-slate-700 animate-pulse" />
            ))}
          </div>
        ) : playlists.length === 0 ? (
          <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-6 py-12 text-center">
            <p className="text-slate-500 dark:text-slate-400">No playlists yet. Pull from Plex to import.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {playlists.map(pl => (
              <PlaylistCard
                key={pl.id}
                playlist={pl}
                onToggleEnabled={handleTogglePlaylist}
                onPush={pushPlaylist}
                onDelete={deletePlaylist}
              />
            ))}
          </div>
        )}
      </section>

      {showForm && (
        <CollectionForm
          onSubmit={handleCreateCollection}
          onCancel={() => setShowForm(false)}
        />
      )}

      {showYamlImport && (
        <YamlImportModal
          onClose={() => setShowYamlImport(false)}
          onImported={handleYamlImported}
        />
      )}
    </div>
  )
}

export default PlexCollectionsPage
