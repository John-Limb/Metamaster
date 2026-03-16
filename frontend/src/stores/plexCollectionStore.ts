import { create } from 'zustand'
import type {
  PlexCollection,
  PlexPlaylist,
  PlexCollectionSet,
  SetType,
  CollectionCreate,
  CollectionUpdate,
  PlaylistCreate,
  PlaylistUpdate,
} from '../services/plexCollectionService'
import {
  getCollections,
  createCollection as svcCreateCollection,
  updateCollection as svcUpdateCollection,
  deleteCollection as svcDeleteCollection,
  pushCollection as svcPushCollection,
  pullCollections as svcPullCollections,
  getPlaylists,
  createPlaylist as svcCreatePlaylist,
  updatePlaylist as svcUpdatePlaylist,
  deletePlaylist as svcDeletePlaylist,
  pushPlaylist as svcPushPlaylist,
  pullPlaylists as svcPullPlaylists,
  bulkDeletePlaylists as svcBulkDeletePlaylists,
  getCollectionSets as svcGetCollectionSets,
  updateCollectionSet as svcUpdateCollectionSet,
  triggerDiscovery as svcTriggerDiscovery,
} from '../services/plexCollectionService'

interface PlexCollectionState {
  // Collections
  collections: PlexCollection[]
  collectionsLoading: boolean
  collectionsError: string | null

  // Playlists
  playlists: PlexPlaylist[]
  playlistsLoading: boolean
  playlistsError: string | null

  // Actions — Collections
  fetchCollections: () => Promise<void>
  createCollection: (data: CollectionCreate) => Promise<void>
  updateCollection: (id: number, data: CollectionUpdate) => Promise<void>
  deleteCollection: (id: number) => Promise<void>
  pushCollection: (id: number) => Promise<void>
  pullCollections: () => Promise<void>

  // Actions — Playlists
  fetchPlaylists: () => Promise<void>
  createPlaylist: (data: PlaylistCreate) => Promise<void>
  updatePlaylist: (id: number, data: PlaylistUpdate) => Promise<void>
  deletePlaylist: (id: number) => Promise<void>
  bulkDeletePlaylists: (ids: number[]) => Promise<void>
  pushPlaylist: (id: number) => Promise<void>
  pullPlaylists: () => Promise<void>

  // Collection Sets
  collectionSets: PlexCollectionSet[]
  setsLoading: boolean

  // Actions — Collection Sets
  fetchCollectionSets: () => Promise<void>
  toggleCollectionSet: (setType: SetType, enabled: boolean) => Promise<void>
  triggerDiscovery: () => Promise<{ task_id: string; message: string }>
}

export const usePlexCollectionStore = create<PlexCollectionState>((set, get) => ({
  collections: [],
  collectionsLoading: false,
  collectionsError: null,

  playlists: [],
  playlistsLoading: false,
  playlistsError: null,

  collectionSets: [],
  setsLoading: false,

  fetchCollections: async () => {
    set({ collectionsLoading: true, collectionsError: null })
    try {
      const collections = await getCollections()
      set({ collections, collectionsLoading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch collections'
      set({ collectionsError: msg, collectionsLoading: false })
    }
  },

  createCollection: async (data) => {
    set({ collectionsLoading: true, collectionsError: null })
    try {
      await svcCreateCollection(data)
      set({ collectionsLoading: false })
      await get().fetchCollections()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create collection'
      set({ collectionsError: msg, collectionsLoading: false })
    }
  },

  updateCollection: async (id, data) => {
    set({ collectionsLoading: true, collectionsError: null })
    try {
      await svcUpdateCollection(id, data)
      set({ collectionsLoading: false })
      await get().fetchCollections()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update collection'
      set({ collectionsError: msg, collectionsLoading: false })
    }
  },

  deleteCollection: async (id) => {
    set({ collectionsLoading: true, collectionsError: null })
    try {
      await svcDeleteCollection(id)
      set({ collectionsLoading: false })
      await get().fetchCollections()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete collection'
      set({ collectionsError: msg, collectionsLoading: false })
    }
  },

  pushCollection: async (id) => {
    set({ collectionsLoading: true, collectionsError: null })
    try {
      await svcPushCollection(id)
      set({ collectionsLoading: false })
      await get().fetchCollections()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to push collection'
      set({ collectionsError: msg, collectionsLoading: false })
    }
  },

  pullCollections: async () => {
    set({ collectionsLoading: true, collectionsError: null })
    try {
      await svcPullCollections()
      set({ collectionsLoading: false })
      await get().fetchCollections()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to pull collections'
      set({ collectionsError: msg, collectionsLoading: false })
    }
  },

  fetchPlaylists: async () => {
    set({ playlistsLoading: true, playlistsError: null })
    try {
      const playlists = await getPlaylists()
      set({ playlists, playlistsLoading: false })
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch playlists'
      set({ playlistsError: msg, playlistsLoading: false })
    }
  },

  createPlaylist: async (data) => {
    set({ playlistsLoading: true, playlistsError: null })
    try {
      await svcCreatePlaylist(data)
      set({ playlistsLoading: false })
      await get().fetchPlaylists()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create playlist'
      set({ playlistsError: msg, playlistsLoading: false })
    }
  },

  updatePlaylist: async (id, data) => {
    set({ playlistsLoading: true, playlistsError: null })
    try {
      await svcUpdatePlaylist(id, data)
      set({ playlistsLoading: false })
      await get().fetchPlaylists()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update playlist'
      set({ playlistsError: msg, playlistsLoading: false })
    }
  },

  deletePlaylist: async (id) => {
    set({ playlistsLoading: true, playlistsError: null })
    try {
      await svcDeletePlaylist(id)
    } catch (err: unknown) {
      // 404 means it was already deleted — treat as success
      if ((err as { code?: string }).code !== '404') {
        const msg = err instanceof Error ? err.message : 'Failed to delete playlist'
        set({ playlistsError: msg, playlistsLoading: false })
        return
      }
    }
    set({ playlistsLoading: false })
    await get().fetchPlaylists()
  },

  bulkDeletePlaylists: async (ids) => {
    set({ playlistsLoading: true, playlistsError: null })
    try {
      await svcBulkDeletePlaylists(ids)
      set({ playlistsLoading: false })
      await get().fetchPlaylists()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to delete playlists'
      set({ playlistsError: msg, playlistsLoading: false })
    }
  },

  pushPlaylist: async (id) => {
    set({ playlistsLoading: true, playlistsError: null })
    try {
      await svcPushPlaylist(id)
      set({ playlistsLoading: false })
      await get().fetchPlaylists()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to push playlist'
      set({ playlistsError: msg, playlistsLoading: false })
    }
  },

  pullPlaylists: async () => {
    set({ playlistsLoading: true, playlistsError: null })
    try {
      await svcPullPlaylists()
      set({ playlistsLoading: false })
      await get().fetchPlaylists()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to pull playlists'
      set({ playlistsError: msg, playlistsLoading: false })
    }
  },

  fetchCollectionSets: async () => {
    set({ setsLoading: true })
    try {
      const collectionSets = await svcGetCollectionSets()
      set({ collectionSets, setsLoading: false })
    } catch {
      set({ setsLoading: false })
    }
  },

  toggleCollectionSet: async (setType, enabled) => {
    set({ setsLoading: true })
    try {
      const updated = await svcUpdateCollectionSet(setType, enabled)
      set(state => ({
        setsLoading: false,
        collectionSets: state.collectionSets.map(s =>
          s.set_type === setType ? updated : s
        ),
      }))
    } catch {
      set({ setsLoading: false })
    }
  },

  triggerDiscovery: async () => {
    return svcTriggerDiscovery()
  },
}))
