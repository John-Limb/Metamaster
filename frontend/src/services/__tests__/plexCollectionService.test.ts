import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  getCollections,
  getCollection,
  createCollection,
  updateCollection,
  deleteCollection,
  pushCollection,
  pullCollections,
  pushAllCollections,
  exportCollectionsYaml,
  getPlaylists,
  getPlaylist,
  createPlaylist,
  updatePlaylist,
  deletePlaylist,
  pushPlaylist,
  pullPlaylists,
} from '../plexCollectionService'

vi.mock('@/utils/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

import { apiClient } from '@/utils/api'

const mockCollection = {
  id: 1,
  connection_id: 1,
  name: 'Marvel',
  description: null,
  sort_title: null,
  builder_type: 'tmdb_collection' as const,
  builder_config: { tmdb_collection_id: 131296 },
  plex_rating_key: null,
  last_synced_at: null,
  enabled: false,
  is_default: false,
  items: [],
  content_type: null,
}

const mockPlaylist = {
  id: 2,
  connection_id: 1,
  name: 'My Playlist',
  description: null,
  builder_config: { items: [] },
  plex_rating_key: null,
  last_synced_at: null,
  enabled: false,
  items: [],
}

describe('plexCollectionService — collections', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getCollections returns array of collections', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: [mockCollection] })
    const result = await getCollections()
    expect(apiClient.get).toHaveBeenCalledWith('/plex/collections')
    expect(result).toHaveLength(1)
    expect(result[0].name).toBe('Marvel')
  })

  it('getCollection returns single collection by id', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockCollection })
    const result = await getCollection(1)
    expect(apiClient.get).toHaveBeenCalledWith('/plex/collections/1')
    expect(result.id).toBe(1)
  })

  it('createCollection posts payload and returns created collection', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockCollection })
    const payload = {
      name: 'Marvel',
      builder_type: 'tmdb_collection' as const,
      builder_config: { tmdb_collection_id: 131296 },
    }
    const result = await createCollection(payload)
    expect(apiClient.post).toHaveBeenCalledWith('/plex/collections', payload)
    expect(result.name).toBe('Marvel')
  })

  it('updateCollection patches and returns updated collection', async () => {
    const updated = { ...mockCollection, enabled: true }
    vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: updated })
    const result = await updateCollection(1, { enabled: true })
    expect(apiClient.patch).toHaveBeenCalledWith('/plex/collections/1', { enabled: true })
    expect(result.enabled).toBe(true)
  })

  it('deleteCollection calls delete on correct URL', async () => {
    vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: null })
    await deleteCollection(1)
    expect(apiClient.delete).toHaveBeenCalledWith('/plex/collections/1')
  })

  it('deleteCollection DELETEs without query param by default', async () => {
    vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: null })
    await deleteCollection(42)
    expect(apiClient.delete).toHaveBeenCalledWith('/plex/collections/42')
  })

  it('deleteCollection appends ?delete_from_plex=true when flag is set', async () => {
    vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: null })
    await deleteCollection(42, true)
    expect(apiClient.delete).toHaveBeenCalledWith('/plex/collections/42?delete_from_plex=true')
  })

  it('pushCollection posts to push endpoint', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: { status: 'ok' } })
    await pushCollection(1)
    expect(apiClient.post).toHaveBeenCalledWith('/plex/collections/1/push')
  })

  it('pushAllCollections POSTs to /plex/collections/push-all', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: { status: 'queued' } })
    await pushAllCollections()
    expect(apiClient.post).toHaveBeenCalledWith('/plex/collections/push-all')
  })

  it('pullCollections posts to /pull', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: { status: 'ok' } })
    await pullCollections()
    expect(apiClient.post).toHaveBeenCalledWith('/plex/collections/pull')
  })

  it('exportCollectionsYaml returns yaml_content string', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: { yaml_content: 'collections:\n  Marvel: {}' },
    })
    const result = await exportCollectionsYaml()
    expect(apiClient.post).toHaveBeenCalledWith('/plex/collections/export')
    expect(result).toBe('collections:\n  Marvel: {}')
  })

  it('PlexCollection interface includes content_type field', () => {
    // Compile-time check — if TypeScript is happy, runtime is fine too
    const col: import('../plexCollectionService').PlexCollection = {
      id: 1,
      connection_id: 1,
      name: 'Test',
      description: null,
      sort_title: null,
      builder_type: 'static_items',
      builder_config: {},
      plex_rating_key: null,
      last_synced_at: null,
      enabled: false,
      is_default: false,
      items: [],
      content_type: null,
    }
    expect(col.content_type).toBeNull()
  })
})

describe('plexCollectionService — playlists', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getPlaylists returns array of playlists', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: [mockPlaylist] })
    const result = await getPlaylists()
    expect(apiClient.get).toHaveBeenCalledWith('/plex/playlists')
    expect(result).toHaveLength(1)
    expect(result[0].name).toBe('My Playlist')
  })

  it('getPlaylist returns single playlist by id', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockPlaylist })
    const result = await getPlaylist(2)
    expect(apiClient.get).toHaveBeenCalledWith('/plex/playlists/2')
    expect(result.id).toBe(2)
  })

  it('createPlaylist posts payload and returns created playlist', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: mockPlaylist })
    const payload = { name: 'My Playlist', builder_config: { items: [] } }
    const result = await createPlaylist(payload)
    expect(apiClient.post).toHaveBeenCalledWith('/plex/playlists', payload)
    expect(result.name).toBe('My Playlist')
  })

  it('updatePlaylist patches and returns updated playlist', async () => {
    const updated = { ...mockPlaylist, enabled: true }
    vi.mocked(apiClient.patch).mockResolvedValueOnce({ data: updated })
    const result = await updatePlaylist(2, { enabled: true })
    expect(apiClient.patch).toHaveBeenCalledWith('/plex/playlists/2', { enabled: true })
    expect(result.enabled).toBe(true)
  })

  it('deletePlaylist calls delete on correct URL', async () => {
    vi.mocked(apiClient.delete).mockResolvedValueOnce({ data: null })
    await deletePlaylist(2)
    expect(apiClient.delete).toHaveBeenCalledWith('/plex/playlists/2')
  })

  it('pushPlaylist posts to push endpoint', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: { status: 'ok' } })
    await pushPlaylist(2)
    expect(apiClient.post).toHaveBeenCalledWith('/plex/playlists/2/push')
  })

  it('pullPlaylists posts to /pull', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: { status: 'ok' } })
    await pullPlaylists()
    expect(apiClient.post).toHaveBeenCalledWith('/plex/playlists/pull')
  })
})
