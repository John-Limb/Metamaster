import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PlexCollectionsPage } from '../PlexCollectionsPage'

vi.mock('../../stores/plexCollectionStore')

import { usePlexCollectionStore } from '../../stores/plexCollectionStore'

const mockStore = {
  collections: [],
  collectionsLoading: false,
  collectionsError: null,
  playlists: [],
  playlistsLoading: false,
  playlistsError: null,
  collectionSets: [],
  setsLoading: false,
  fetchCollections: vi.fn(),
  fetchPlaylists: vi.fn(),
  fetchCollectionSets: vi.fn(),
  createCollection: vi.fn(),
  updateCollection: vi.fn(),
  deleteCollection: vi.fn(),
  pushCollection: vi.fn(),
  pullCollections: vi.fn(),
  createPlaylist: vi.fn(),
  updatePlaylist: vi.fn(),
  deletePlaylist: vi.fn(),
  pushPlaylist: vi.fn(),
  pullPlaylists: vi.fn(),
  toggleCollectionSet: vi.fn(),
  triggerDiscovery: vi.fn(),
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(usePlexCollectionStore).mockReturnValue(mockStore)
})

describe('PlexCollectionsPage', () => {
  it('renders the Collections heading', () => {
    render(<PlexCollectionsPage />)
    expect(screen.getByRole('heading', { name: /plex collections/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /^collections$/i })).toBeInTheDocument()
  })

  it('shows loading skeleton when collectionsLoading is true and no collections', () => {
    vi.mocked(usePlexCollectionStore).mockReturnValue({
      ...mockStore,
      collectionsLoading: true,
    })
    render(<PlexCollectionsPage />)
    // The loading skeletons are animate-pulse divs; check the page still renders
    expect(screen.getByRole('heading', { name: /^collections$/i })).toBeInTheDocument()
    // The empty state message should NOT appear during loading
    expect(screen.queryByText(/no collections yet/i)).not.toBeInTheDocument()
  })

  it('shows empty state when there are no collections and not loading', () => {
    render(<PlexCollectionsPage />)
    expect(screen.getByText(/no collections yet/i)).toBeInTheDocument()
  })

  it('renders collection cards when collections are present', () => {
    vi.mocked(usePlexCollectionStore).mockReturnValue({
      ...mockStore,
      collections: [
        {
          id: 1,
          connection_id: 1,
          name: 'Marvel Movies',
          description: null,
          sort_title: null,
          builder_type: 'tmdb_collection',
          builder_config: {},
          plex_rating_key: null,
          last_synced_at: null,
          enabled: true,
          is_default: false,
          items: [],
        },
      ],
    })
    render(<PlexCollectionsPage />)
    expect(screen.getByText('Marvel Movies')).toBeInTheDocument()
  })

  it('shows error banner when collectionsError is set', () => {
    vi.mocked(usePlexCollectionStore).mockReturnValue({
      ...mockStore,
      collectionsError: 'Failed to fetch collections',
    })
    render(<PlexCollectionsPage />)
    expect(screen.getByText(/failed to fetch collections/i)).toBeInTheDocument()
  })
})
