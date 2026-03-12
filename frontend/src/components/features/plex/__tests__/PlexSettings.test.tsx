import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PlexSettings } from '../PlexSettings'
import { usePlexStore } from '../../../../stores/plexStore'
import type { PlexConnection, PlexMismatchItem } from '../../../../services/plexService'

vi.mock('../../../../stores/plexStore')

interface MockPlexState {
  connection: PlexConnection | null
  isLoading: boolean
  error: string | null
  mismatches: PlexMismatchItem[]
  fetchConnection: ReturnType<typeof vi.fn>
  disconnect: ReturnType<typeof vi.fn>
  sync: ReturnType<typeof vi.fn>
  fetchMismatches: ReturnType<typeof vi.fn>
  resolveMismatch: ReturnType<typeof vi.fn>
}

const makeMockState = (overrides: Partial<MockPlexState> = {}): MockPlexState => ({
  connection: null,
  isLoading: false,
  error: null,
  mismatches: [],
  fetchConnection: vi.fn(),
  disconnect: vi.fn(),
  sync: vi.fn(),
  fetchMismatches: vi.fn(),
  resolveMismatch: vi.fn(),
  ...overrides,
})

describe('PlexSettings', () => {
  beforeEach(() => vi.clearAllMocks())

  it('shows "Not connected" when no connection', () => {
    vi.mocked(usePlexStore).mockReturnValue(makeMockState())
    render(<PlexSettings />)
    expect(screen.getByText(/not connected/i)).toBeInTheDocument()
  })

  it('shows server URL and disconnect button when connected', () => {
    const connection: PlexConnection = {
      id: 1,
      server_url: 'http://plex:32400',
      is_active: true,
      movie_library_id: null,
      tv_library_id: null,
      created_at: '2026-03-05T00:00:00',
      last_connected_at: null,
    }
    vi.mocked(usePlexStore).mockReturnValue(makeMockState({ connection }))
    render(<PlexSettings />)
    expect(screen.getByText('http://plex:32400')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /disconnect/i })).toBeInTheDocument()
  })

  it('shows manual token form when Manual Token tab is selected', () => {
    vi.mocked(usePlexStore).mockReturnValue(makeMockState())
    render(<PlexSettings />)
    fireEvent.click(screen.getByRole('tab', { name: /manual token/i }))
    expect(screen.getByLabelText(/plex token/i)).toBeInTheDocument()
  })
})
