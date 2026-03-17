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
    pushAllCollections,
    pushAllLoading,
    pushAllError,
    updatePlaylist,
    deletePlaylist,
    pushPlaylist,
    pullPlaylists,
    bulkDeletePlaylists,
  } = usePlexCollectionStore()

  const [showForm, setShowForm] = useState(false)
  const [showYamlImport, setShowYamlImport] = useState(false)
  const [discoverMessage, setDiscoverMessage] = useState<string | null>(null)
  const [selectedPlaylistIds, setSelectedPlaylistIds] = useState<Set<number>>(new Set())
  const [selectMode, setSelectMode] = useState(false)

  useEffect(() => {
    fetchCollections()
    fetchPlaylists()
    fetchCollectionSets()
  }, [fetchCollections, fetchPlaylists, fetchCollectionSets])

  const handlePushAll = () => {
    pushAllCollections()
  }

  const handleDeleteCollection = (id: number, deleteFromPlex: boolean) => {
    deleteCollection(id, deleteFromPlex)
  }

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

  const handleToggleSelect = (id: number, checked: boolean) => {
    setSelectedPlaylistIds(prev => {
      const next = new Set(prev)
      if (checked) next.add(id)
      else next.delete(id)
      return next
    })
  }

  const handleSelectAll = () => {
    setSelectedPlaylistIds(new Set(playlists.map(p => p.id)))
  }

  const handleBulkDelete = async () => {
    const ids = Array.from(selectedPlaylistIds)
    setSelectedPlaylistIds(new Set())
    setSelectMode(false)
    await bulkDeletePlaylists(ids)
  }

  const exitSelectMode = () => {
    setSelectMode(false)
    setSelectedPlaylistIds(new Set())
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
        <div className="flex items-center gap-2">
          <button
            onClick={handlePushAll}
            disabled={pushAllLoading}
            className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium border border-indigo-300 dark:border-indigo-600 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 disabled:opacity-40 transition-colors shrink-0"
          >
            {pushAllLoading ? 'Queuing…' : 'Push All to Plex'}
          </button>
          <button
            onClick={handleDiscover}
            className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 hover:bg-indigo-700 text-white transition-colors shrink-0"
          >
            Discover Collections
          </button>
        </div>
      </div>

      {discoverMessage && (
        <div className="rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 px-4 py-3 text-sm text-green-700 dark:text-green-400">
          {discoverMessage}
        </div>
      )}

      {pushAllError && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">
          {pushAllError}
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

        {(() => {
          const movieCollections = collections.filter(
            c => c.content_type === 'movie' || c.content_type === null
          )
          const tvCollections = collections.filter(c => c.content_type === 'tv_show')

          if (collectionsLoading && collections.length === 0) {
            return (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-40 rounded-xl bg-slate-200 dark:bg-slate-700 animate-pulse" />
                ))}
              </div>
            )
          }

          if (collections.length === 0) {
            return (
              <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 px-6 py-12 text-center">
                <p className="text-slate-500 dark:text-slate-400">No collections yet. Create one or pull from Plex.</p>
              </div>
            )
          }

          return (
            <>
              {movieCollections.length > 0 && (
                <div className="space-y-3">
                  <h2 className="text-base font-semibold text-slate-800 dark:text-slate-200">Movies</h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {movieCollections.map(col => (
                      <CollectionCard
                        key={col.id}
                        collection={col}
                        onToggleEnabled={handleToggleCollection}
                        onPush={pushCollection}
                        onDelete={handleDeleteCollection}
                      />
                    ))}
                  </div>
                </div>
              )}
              {tvCollections.length > 0 && (
                <div className="space-y-3">
                  <h2 className="text-base font-semibold text-slate-800 dark:text-slate-200">TV Shows</h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {tvCollections.map(col => (
                      <CollectionCard
                        key={col.id}
                        collection={col}
                        onToggleEnabled={handleToggleCollection}
                        onPush={pushCollection}
                        onDelete={handleDeleteCollection}
                      />
                    ))}
                  </div>
                </div>
              )}
            </>
          )
        })()}
      </section>

      {/* Playlists section */}
      <section>
        <div className="flex items-center justify-between gap-4 mb-4">
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-200">
            Playlists {playlists.length > 0 && <span className="text-slate-400 font-normal text-sm">({playlists.length})</span>}
          </h2>
          <div className="flex items-center gap-2">
            {selectMode ? (
              <>
                <button
                  onClick={handleSelectAll}
                  className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                >
                  Select All
                </button>
                {selectedPlaylistIds.size > 0 && (
                  <button
                    onClick={handleBulkDelete}
                    disabled={playlistsLoading}
                    className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium bg-red-600 hover:bg-red-700 disabled:opacity-40 text-white transition-colors"
                  >
                    Delete Selected ({selectedPlaylistIds.size})
                  </button>
                )}
                <button
                  onClick={exitSelectMode}
                  className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                >
                  Cancel
                </button>
              </>
            ) : (
              <>
                {playlists.length > 0 && (
                  <button
                    onClick={() => setSelectMode(true)}
                    className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                  >
                    Select
                  </button>
                )}
                <button
                  onClick={() => pullPlaylists()}
                  disabled={playlistsLoading}
                  className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 transition-colors"
                >
                  Pull from Plex
                </button>
              </>
            )}
          </div>
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
                selectable={selectMode}
                selected={selectedPlaylistIds.has(pl.id)}
                onSelect={handleToggleSelect}
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
