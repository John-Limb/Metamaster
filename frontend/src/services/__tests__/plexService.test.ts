import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import {
  getPlexConnection,
  createPlexConnection,
  triggerPlexSync,
  initiatePlexOAuth,
} from '../plexService'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('plexService', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getPlexConnection calls correct endpoint', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({
      data: { id: 1, server_url: 'http://plex:32400', is_active: true },
    })
    const result = await getPlexConnection()
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/plex/connection')
    expect(result.id).toBe(1)
  })

  it('createPlexConnection posts server_url and token', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({ data: { id: 1 } })
    await createPlexConnection('http://plex:32400', 'my-token')
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/plex/connection', {
      server_url: 'http://plex:32400',
      token: 'my-token',
    })
  })

  it('triggerPlexSync posts to sync endpoint', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({ data: { task_id: 'abc', message: 'ok' } })
    const result = await triggerPlexSync()
    expect(result.task_id).toBe('abc')
  })

  it('initiatePlexOAuth returns oauth_url and pin_id', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({
      data: { oauth_url: 'https://plex.tv', pin_id: 42 },
    })
    const result = await initiatePlexOAuth('http://localhost/callback')
    expect(result.pin_id).toBe(42)
  })
})
