import { apiClient } from '@/utils/api'

export type BuilderType = 'tmdb_collection' | 'static_items' | 'genre' | 'decade'

export type SetType = 'franchise' | 'genre' | 'decade'

export interface PlexCollectionSet {
  id: number
  connection_id: number
  set_type: SetType
  enabled: boolean
  last_run_at: string | null
}

export interface CollectionItem {
  id: number
  plex_rating_key: string
  item_type: string
  item_id: number
  position: number
  movie_title: string | null
}

export interface PlexCollection {
  id: number
  connection_id: number
  name: string
  description: string | null
  sort_title: string | null
  builder_type: BuilderType
  builder_config: Record<string, unknown>
  plex_rating_key: string | null
  last_synced_at: string | null
  enabled: boolean
  is_default: boolean
  items: CollectionItem[]
  content_type: string | null
}

export interface PlaylistItem {
  id: number
  plex_rating_key: string
  item_type: string
  item_id: number
  position: number
  movie_title: string | null
}

export interface PlexPlaylist {
  id: number
  connection_id: number
  name: string
  description: string | null
  builder_config: Record<string, unknown>
  plex_rating_key: string | null
  last_synced_at: string | null
  enabled: boolean
  items: PlaylistItem[]
}

export interface CollectionCreate {
  name: string
  description?: string
  sort_title?: string
  builder_type: BuilderType
  builder_config: Record<string, unknown>
}

export interface CollectionUpdate {
  name?: string
  description?: string
  sort_title?: string
  builder_config?: Record<string, unknown>
  enabled?: boolean
}

export interface PlaylistCreate {
  name: string
  description?: string
  builder_config: Record<string, unknown>
}

export interface PlaylistUpdate {
  name?: string
  description?: string
  builder_config?: Record<string, unknown>
  enabled?: boolean
}

export interface LocalTmdbCollection {
  tmdb_collection_id: number
  name: string
  movie_count: number
}

export interface TmdbCollectionSearchResult {
  id: number
  name: string
}

// ---------------------------------------------------------------------------
// Collections
// ---------------------------------------------------------------------------

export async function getCollections(): Promise<PlexCollection[]> {
  const { data } = await apiClient.get<PlexCollection[]>('/plex/collections')
  return data
}

export async function getCollection(id: number): Promise<PlexCollection> {
  const { data } = await apiClient.get<PlexCollection>(`/plex/collections/${id}`)
  return data
}

export async function createCollection(payload: CollectionCreate): Promise<PlexCollection> {
  const { data } = await apiClient.post<PlexCollection>('/plex/collections', payload)
  return data
}

export async function updateCollection(
  id: number,
  payload: CollectionUpdate
): Promise<PlexCollection> {
  const { data } = await apiClient.patch<PlexCollection>(`/plex/collections/${id}`, payload)
  return data
}

export async function deleteCollection(id: number, deleteFromPlex = false): Promise<void> {
  const url = deleteFromPlex
    ? `/plex/collections/${id}?delete_from_plex=true`
    : `/plex/collections/${id}`
  await apiClient.delete(url)
}

export async function pushCollection(id: number): Promise<void> {
  await apiClient.post(`/plex/collections/${id}/push`)
}

export async function pullCollections(): Promise<void> {
  await apiClient.post('/plex/collections/pull')
}

export async function pushAllCollections(): Promise<void> {
  await apiClient.post('/plex/collections/push-all')
}

export async function exportCollectionsYaml(): Promise<string> {
  const { data } = await apiClient.post<{ yaml_content: string }>('/plex/collections/export')
  return data.yaml_content
}

export async function importYaml(yamlContent: string): Promise<{
  collections_created: string[]
  playlists_created: string[]
}> {
  const { data } = await apiClient.post<{
    collections_created: string[]
    playlists_created: string[]
  }>('/plex/collections/import', { yaml_content: yamlContent })
  return data
}

// ---------------------------------------------------------------------------
// Playlists
// ---------------------------------------------------------------------------

export async function getPlaylists(): Promise<PlexPlaylist[]> {
  const { data } = await apiClient.get<PlexPlaylist[]>('/plex/playlists')
  return data
}

export async function getPlaylist(id: number): Promise<PlexPlaylist> {
  const { data } = await apiClient.get<PlexPlaylist>(`/plex/playlists/${id}`)
  return data
}

export async function createPlaylist(payload: PlaylistCreate): Promise<PlexPlaylist> {
  const { data } = await apiClient.post<PlexPlaylist>('/plex/playlists', payload)
  return data
}

export async function updatePlaylist(id: number, payload: PlaylistUpdate): Promise<PlexPlaylist> {
  const { data } = await apiClient.patch<PlexPlaylist>(`/plex/playlists/${id}`, payload)
  return data
}

export async function deletePlaylist(id: number): Promise<void> {
  await apiClient.delete(`/plex/playlists/${id}`)
}

export async function pushPlaylist(id: number): Promise<void> {
  await apiClient.post(`/plex/playlists/${id}/push`)
}

export async function pullPlaylists(): Promise<void> {
  await apiClient.post('/plex/playlists/pull')
}

export async function bulkDeletePlaylists(ids: number[]): Promise<void> {
  await apiClient.post('/plex/playlists/bulk-delete', { ids })
}

// ---------------------------------------------------------------------------
// Collection Sets
// ---------------------------------------------------------------------------

export async function getCollectionSets(): Promise<PlexCollectionSet[]> {
  const { data } = await apiClient.get<PlexCollectionSet[]>('/plex/sets')
  return data
}

export async function updateCollectionSet(
  setType: SetType,
  enabled: boolean
): Promise<PlexCollectionSet> {
  const { data } = await apiClient.patch<PlexCollectionSet>(`/plex/sets/${setType}`, { enabled })
  return data
}

export async function triggerDiscovery(): Promise<{ task_id: string; message: string }> {
  const { data } = await apiClient.post<{ task_id: string; message: string }>('/plex/discover')
  return data
}

// ---------------------------------------------------------------------------
// TMDB Collections
// ---------------------------------------------------------------------------

export async function getLocalTmdbCollections(): Promise<LocalTmdbCollection[]> {
  const { data } = await apiClient.get<LocalTmdbCollection[]>('/plex/tmdb-collections/local')
  return data
}

export async function searchTmdbCollections(q: string): Promise<TmdbCollectionSearchResult[]> {
  const { data } = await apiClient.get<TmdbCollectionSearchResult[]>(
    `/plex/tmdb-collections/search?q=${encodeURIComponent(q)}`
  )
  return data
}

export async function getCollectionArtwork(id: number): Promise<Blob> {
  const { data } = await apiClient.get<Blob>(`/plex/collections/${id}/artwork`, { responseType: 'blob' })
  return data
}

export async function getPlaylistArtwork(id: number): Promise<Blob> {
  const { data } = await apiClient.get<Blob>(`/plex/playlists/${id}/artwork`, { responseType: 'blob' })
  return data
}
