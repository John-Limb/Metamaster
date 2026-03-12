import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  getPlexConnection,
  createPlexConnection,
  triggerPlexSync,
  initiatePlexOAuth,
  getMismatches,
  resolveMismatch,
} from '../plexService'

vi.mock('@/utils/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

import { apiClient } from '@/utils/api'

describe('plexService', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getPlexConnection calls correct endpoint', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { id: 1, server_url: 'http://plex:32400', is_active: true },
    })
    const result = await getPlexConnection()
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/plex/connection')
    expect(result.id).toBe(1)
  })

  it('createPlexConnection posts server_url and token', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: { id: 1 } })
    await createPlexConnection('http://plex:32400', 'my-token')
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/plex/connection', {
      server_url: 'http://plex:32400',
      token: 'my-token',
    })
  })

  it('triggerPlexSync posts to sync endpoint', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: { task_id: 'abc', message: 'ok' },
    })
    const result = await triggerPlexSync()
    expect(result.task_id).toBe('abc')
  })

  it('initiatePlexOAuth returns oauth_url and pin_id', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { oauth_url: 'https://plex.tv', pin_id: 42 },
    })
    const result = await initiatePlexOAuth('http://localhost/callback')
    expect(result.pin_id).toBe(42)
  })
})

describe('getMismatches', () => {
  it('returns mismatch items from the API', async () => {
    const mockData = [
      { id: 10, item_type: 'movie', item_id: 42, plex_rating_key: '77', plex_tmdb_id: '9999' },
    ]
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockData })
    const result = await getMismatches()
    expect(result).toEqual(mockData)
    expect(apiClient.get).toHaveBeenCalledWith('/api/v1/plex/mismatches')
  })
})

describe('resolveMismatch', () => {
  it('posts resolve request to the API', async () => {
    vi.mocked(apiClient.post).mockResolvedValueOnce({ data: { status: 'resolved' } })
    await resolveMismatch(10, 'metamaster')
    expect(apiClient.post).toHaveBeenCalledWith('/api/v1/plex/mismatches/10/resolve', {
      trust: 'metamaster',
    })
  })
})
