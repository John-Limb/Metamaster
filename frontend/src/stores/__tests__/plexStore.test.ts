import { describe, it, expect, vi, beforeEach } from 'vitest'
import { usePlexStore } from '../plexStore'
import * as plexService from '../../services/plexService'
import type { PlexConnection } from '../../services/plexService'

vi.mock('../../services/plexService')

const makeConnection = (overrides: Partial<PlexConnection> = {}): PlexConnection => ({
  id: 1,
  server_url: 'http://plex:32400',
  is_active: true,
  movie_library_id: null,
  tv_library_id: null,
  created_at: '2026-03-05T00:00:00',
  last_connected_at: null,
  ...overrides,
})

describe('plexStore', () => {
  beforeEach(() => {
    usePlexStore.setState({ connection: null, isLoading: false, error: null })
    vi.clearAllMocks()
  })

  it('fetchConnection sets connection on success', async () => {
    vi.mocked(plexService.getPlexConnection).mockResolvedValue(makeConnection({ id: 1 }))
    await usePlexStore.getState().fetchConnection()
    expect(usePlexStore.getState().connection?.id).toBe(1)
    expect(usePlexStore.getState().isLoading).toBe(false)
  })

  it('fetchConnection sets null on 404', async () => {
    vi.mocked(plexService.getPlexConnection).mockRejectedValue({ response: { status: 404 } })
    await usePlexStore.getState().fetchConnection()
    expect(usePlexStore.getState().connection).toBeNull()
  })

  it('disconnect calls deletePlexConnection and clears state', async () => {
    vi.mocked(plexService.deletePlexConnection).mockResolvedValue(undefined)
    usePlexStore.setState({ connection: makeConnection({ id: 1 }) })
    await usePlexStore.getState().disconnect()
    expect(usePlexStore.getState().connection).toBeNull()
  })
})
