import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockStore = {
  collections: [] as import('../../services/plexCollectionService').PlexCollection[],
  collectionsLoading: false,
  collectionsError: null,
  playlists: [] as import('../../services/plexCollectionService').PlexPlaylist[],
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
  pushAllCollections: vi.fn(),
  pushAllLoading: false,
  pushAllError: null as string | null,
  updatePlaylist: vi.fn(),
  deletePlaylist: vi.fn(),
  pushPlaylist: vi.fn(),
  pullPlaylists: vi.fn(),
  bulkDeletePlaylists: vi.fn(),
  toggleCollectionSet: vi.fn(),
  triggerDiscovery: vi.fn().mockResolvedValue({ message: 'ok', task_id: '1' }),
}

vi.mock('../../stores/plexCollectionStore', () => ({
  usePlexCollectionStore: () => mockStore,
}))

vi.mock('../../components/features/plex/CollectionSetToggles', () => ({
  CollectionSetToggles: () => <div data-testid="set-toggles" />,
}))

vi.mock('../../components/features/plex/CollectionCard', () => ({
  CollectionCard: ({ collection }: { collection: { name: string } }) => (
    <div data-testid="collection-card">{collection.name}</div>
  ),
}))

vi.mock('../../components/features/plex/PlaylistCard', () => ({
  PlaylistCard: () => <div data-testid="playlist-card" />,
}))

vi.mock('../../components/features/plex/CollectionForm', () => ({
  CollectionForm: () => <div data-testid="collection-form" />,
}))

vi.mock('../../components/features/plex/YamlImportModal', () => ({
  YamlImportModal: () => <div data-testid="yaml-import-modal" />,
}))

import { PlexCollectionsPage } from '../PlexCollectionsPage'

const movieCol: import('../../services/plexCollectionService').PlexCollection = {
  id: 1, connection_id: 1, name: 'Action Pack', description: null, sort_title: null,
  builder_type: 'static_items', builder_config: {}, plex_rating_key: null,
  last_synced_at: null, enabled: true, is_default: false, items: [], content_type: 'movie',
}
const tvCol: import('../../services/plexCollectionService').PlexCollection = {
  id: 2, connection_id: 1, name: 'Crime Dramas', description: null, sort_title: null,
  builder_type: 'static_items', builder_config: {}, plex_rating_key: null,
  last_synced_at: null, enabled: true, is_default: false, items: [], content_type: 'tv_show',
}
const nullTypeCol: import('../../services/plexCollectionService').PlexCollection = {
  ...movieCol, id: 3, name: 'Legacy Collection', content_type: null,
}

describe('PlexCollectionsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockStore.collections = []
    mockStore.pushAllLoading = false
    mockStore.pushAllError = null
  })

  it('renders Push All to Plex button', () => {
    render(<PlexCollectionsPage />)
    expect(screen.getByRole('button', { name: /push all to plex/i })).toBeInTheDocument()
  })

  it('Push All button calls pushAllCollections', () => {
    render(<PlexCollectionsPage />)
    fireEvent.click(screen.getByRole('button', { name: /push all to plex/i }))
    expect(mockStore.pushAllCollections).toHaveBeenCalled()
  })

  it('shows Movies section heading when movie or null collections exist', () => {
    mockStore.collections = [movieCol, nullTypeCol]
    render(<PlexCollectionsPage />)
    expect(screen.getByRole('heading', { name: /movies/i })).toBeInTheDocument()
    expect(screen.getByText('Action Pack')).toBeInTheDocument()
    expect(screen.getByText('Legacy Collection')).toBeInTheDocument()
  })

  it('shows TV Shows section only when tv collections exist', () => {
    mockStore.collections = [tvCol]
    render(<PlexCollectionsPage />)
    expect(screen.getByRole('heading', { name: /tv shows/i })).toBeInTheDocument()
    expect(screen.getByText('Crime Dramas')).toBeInTheDocument()
  })

  it('does not render TV Shows section when empty', () => {
    mockStore.collections = [movieCol]
    render(<PlexCollectionsPage />)
    expect(screen.queryByRole('heading', { name: /tv shows/i })).not.toBeInTheDocument()
  })
})
