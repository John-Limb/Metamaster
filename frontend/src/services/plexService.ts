import { apiClient } from '@/utils/api'

export interface PlexConnection {
  id: number
  server_url: string
  is_active: boolean
  movie_library_id: string | null
  tv_library_id: string | null
  created_at: string
  last_connected_at: string | null
}

export interface PlexSyncResponse {
  task_id: string
  message: string
}

export interface PlexOAuthInitResponse {
  oauth_url: string
  pin_id: number
}

export async function getPlexConnection(): Promise<PlexConnection> {
  const { data } = await apiClient.get<PlexConnection>('/api/v1/plex/connection')
  return data
}

export async function createPlexConnection(
  serverUrl: string,
  token: string
): Promise<PlexConnection> {
  const { data } = await apiClient.post<PlexConnection>('/api/v1/plex/connection', {
    server_url: serverUrl,
    token,
  })
  return data
}

export async function deletePlexConnection(): Promise<void> {
  await apiClient.delete('/api/v1/plex/connection')
}

export async function triggerPlexSync(): Promise<PlexSyncResponse> {
  const { data } = await apiClient.post<PlexSyncResponse>('/api/v1/plex/sync')
  return data
}

export async function initiatePlexOAuth(redirectUri: string): Promise<PlexOAuthInitResponse> {
  const { data } = await apiClient.get<PlexOAuthInitResponse>('/api/v1/plex/oauth/initiate', {
    params: { redirect_uri: redirectUri },
  })
  return data
}

/** Returns the new connection when authorised, or null when the pin is still pending. */
export async function pollPlexOAuthCallback(
  pinId: number,
  serverUrl: string
): Promise<PlexConnection | null> {
  const { data } = await apiClient.get<{ status: string } & Partial<PlexConnection>>(
    '/api/v1/plex/oauth/callback',
    { params: { pin_id: pinId, server_url: serverUrl } }
  )
  if (data.status === 'pending') return null
  return data as PlexConnection
}

export interface PlexHealthResponse {
  connected: boolean
  not_found_count: number
  not_found_items: Array<{
    id: number
    item_type: string
    item_id: number
    last_error: string | null
  }>
}

export async function getPlexHealth(): Promise<PlexHealthResponse> {
  const { data } = await apiClient.get<PlexHealthResponse>('/api/v1/plex/health')
  return data
}

export async function resyncPlexItem(syncRecordId: number): Promise<void> {
  await apiClient.post(`/api/v1/plex/sync/${syncRecordId}`)
}

export interface PlexMismatchItem {
  id: number
  item_type: string
  item_id: number
  plex_rating_key: string
  plex_tmdb_id: string
}

export async function getMismatches(): Promise<PlexMismatchItem[]> {
  const { data } = await apiClient.get<PlexMismatchItem[]>('/api/v1/plex/mismatches')
  return data
}

export async function resolveMismatch(
  recordId: number,
  trust: 'metamaster' | 'plex'
): Promise<void> {
  await apiClient.post(`/api/v1/plex/mismatches/${recordId}/resolve`, { trust })
}
