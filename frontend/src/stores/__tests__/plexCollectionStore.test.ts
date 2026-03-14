import { describe, it, expect, vi, beforeEach } from 'vitest'
import { usePlexCollectionStore } from '../plexCollectionStore'
import * as svc from '../../services/plexCollectionService'
import type { PlexCollection, PlexPlaylist } from '../../services/plexCollectionService'

vi.mock('../../services/plexCollectionService')

const makeCollection = (overrides: Partial<PlexCollection> = {}): PlexCollection => ({
  id: 1,
  connection_id: 1,
  name: 'Test Collection',
  description: null,
  sort_title: null,
  builder_type: 'static_items',
  builder_config: {},
  plex_rating_key: null,
  last_synced_at: null,
  enabled: true,
  is_default: false,
  items: [],
  ...overrides,
})

const makePlaylist = (overrides: Partial<PlexPlaylist> = {}): PlexPlaylist => ({
  id: 1,
  connection_id: 1,
  name: 'Test Playlist',
  description: null,
  builder_config: {},
  plex_rating_key: null,
  last_synced_at: null,
  enabled: true,
  items: [],
  ...overrides,
})

describe('plexCollectionStore', () => {
  beforeEach(() => {
    usePlexCollectionStore.setState({
      collections: [],
      collectionsLoading: false,
      collectionsError: null,
      playlists: [],
      playlistsLoading: false,
      playlistsError: null,
    })
    vi.clearAllMocks()
  })

  it('fetchCollections sets collections on success', async () => {
    const cols = [makeCollection({ id: 1 }), makeCollection({ id: 2, name: 'Second' })]
    vi.mocked(svc.getCollections).mockResolvedValue(cols)

    await usePlexCollectionStore.getState().fetchCollections()

    const state = usePlexCollectionStore.getState()
    expect(state.collections).toEqual(cols)
    expect(state.collectionsLoading).toBe(false)
    expect(state.collectionsError).toBeNull()
  })

  it('fetchCollections sets error on failure', async () => {
    vi.mocked(svc.getCollections).mockRejectedValue(new Error('Network error'))

    await usePlexCollectionStore.getState().fetchCollections()

    const state = usePlexCollectionStore.getState()
    expect(state.collectionsError).toBe('Network error')
    expect(state.collectionsLoading).toBe(false)
  })

  it('createCollection calls service then re-fetches collections', async () => {
    const created = makeCollection({ id: 10, name: 'New Collection' })
    vi.mocked(svc.createCollection).mockResolvedValue(created)
    vi.mocked(svc.getCollections).mockResolvedValue([created])

    await usePlexCollectionStore.getState().createCollection({
      name: 'New Collection',
      builder_type: 'static_items',
      builder_config: {},
    })

    expect(svc.createCollection).toHaveBeenCalledWith({
      name: 'New Collection',
      builder_type: 'static_items',
      builder_config: {},
    })
    expect(svc.getCollections).toHaveBeenCalled()
    expect(usePlexCollectionStore.getState().collections).toEqual([created])
  })

  it('updateCollection calls service with id and data then re-fetches', async () => {
    const updated = makeCollection({ id: 1, name: 'Updated' })
    vi.mocked(svc.updateCollection).mockResolvedValue(updated)
    vi.mocked(svc.getCollections).mockResolvedValue([updated])

    await usePlexCollectionStore.getState().updateCollection(1, { name: 'Updated' })

    expect(svc.updateCollection).toHaveBeenCalledWith(1, { name: 'Updated' })
    expect(svc.getCollections).toHaveBeenCalled()
    expect(usePlexCollectionStore.getState().collections[0].name).toBe('Updated')
  })

  it('deleteCollection calls service then re-fetches', async () => {
    vi.mocked(svc.deleteCollection).mockResolvedValue(undefined)
    vi.mocked(svc.getCollections).mockResolvedValue([])

    await usePlexCollectionStore.getState().deleteCollection(1)

    expect(svc.deleteCollection).toHaveBeenCalledWith(1)
    expect(svc.getCollections).toHaveBeenCalled()
    expect(usePlexCollectionStore.getState().collections).toEqual([])
  })

  it('pullCollections calls service then re-fetches', async () => {
    const col = makeCollection({ id: 5, name: 'Pulled' })
    vi.mocked(svc.pullCollections).mockResolvedValue(undefined)
    vi.mocked(svc.getCollections).mockResolvedValue([col])

    await usePlexCollectionStore.getState().pullCollections()

    expect(svc.pullCollections).toHaveBeenCalled()
    expect(svc.getCollections).toHaveBeenCalled()
    expect(usePlexCollectionStore.getState().collections).toEqual([col])
  })

  it('fetchPlaylists sets playlists on success', async () => {
    const lists = [makePlaylist({ id: 1 }), makePlaylist({ id: 2, name: 'Second' })]
    vi.mocked(svc.getPlaylists).mockResolvedValue(lists)

    await usePlexCollectionStore.getState().fetchPlaylists()

    const state = usePlexCollectionStore.getState()
    expect(state.playlists).toEqual(lists)
    expect(state.playlistsLoading).toBe(false)
    expect(state.playlistsError).toBeNull()
  })

  it('createPlaylist calls service then re-fetches playlists', async () => {
    const created = makePlaylist({ id: 20, name: 'New Playlist' })
    vi.mocked(svc.createPlaylist).mockResolvedValue(created)
    vi.mocked(svc.getPlaylists).mockResolvedValue([created])

    await usePlexCollectionStore.getState().createPlaylist({
      name: 'New Playlist',
      builder_config: {},
    })

    expect(svc.createPlaylist).toHaveBeenCalledWith({
      name: 'New Playlist',
      builder_config: {},
    })
    expect(svc.getPlaylists).toHaveBeenCalled()
    expect(usePlexCollectionStore.getState().playlists).toEqual([created])
  })

  it('pullPlaylists calls service then re-fetches', async () => {
    const list = makePlaylist({ id: 7, name: 'Pulled Playlist' })
    vi.mocked(svc.pullPlaylists).mockResolvedValue(undefined)
    vi.mocked(svc.getPlaylists).mockResolvedValue([list])

    await usePlexCollectionStore.getState().pullPlaylists()

    expect(svc.pullPlaylists).toHaveBeenCalled()
    expect(svc.getPlaylists).toHaveBeenCalled()
    expect(usePlexCollectionStore.getState().playlists).toEqual([list])
  })
})
