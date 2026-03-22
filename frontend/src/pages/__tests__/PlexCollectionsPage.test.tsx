import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'

const baseCollection = {
  id: 1, connection_id: 1, name: 'Action Films', description: null, sort_title: null,
  builder_type: 'genre' as const, builder_config: {}, plex_rating_key: null,
  last_synced_at: null, enabled: false, is_default: false, items: [], content_type: 'movie',
}
const basePlaylist = {
  id: 2, connection_id: 1, name: 'My Playlist', description: null, builder_config: {},
  plex_rating_key: null, last_synced_at: null, enabled: false, items: [],
}

const mockStore = {
  collections: [baseCollection],
  collectionsLoading: false,
  collectionsError: null,
  playlists: [basePlaylist],
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
vi.mock('../../components/features/plex/CollectionRow', () => ({
  CollectionRow: ({ collection, onSelect }: { collection: { name: string; id: number }; onSelect: (id: number) => void }) => (
    <tr><td><button onClick={() => onSelect(collection.id)}>{collection.name}</button></td></tr>
  ),
}))
vi.mock('../../components/features/plex/PlaylistRow', () => ({
  PlaylistRow: ({ playlist, onSelect }: { playlist: { name: string; id: number }; onSelect: (id: number) => void }) => (
    <tr><td><button onClick={() => onSelect(playlist.id)}>{playlist.name}</button></td></tr>
  ),
}))
vi.mock('../../components/features/plex/CollectionDrawer', () => ({
  CollectionDrawer: ({ collection, onClose }: { collection: { name: string }; onClose: () => void }) => (
    <div data-testid="collection-drawer">
      {collection.name}
      <button onClick={onClose}>Close</button>
    </div>
  ),
}))
vi.mock('../../components/features/plex/PlaylistDrawer', () => ({
  PlaylistDrawer: ({ playlist, onClose }: { playlist: { name: string }; onClose: () => void }) => (
    <div data-testid="playlist-drawer">
      {playlist.name}
      <button onClick={onClose}>Close</button>
    </div>
  ),
}))
vi.mock('../../components/features/plex/CollectionForm', () => ({
  CollectionForm: () => <div data-testid="collection-form" />,
}))
vi.mock('../../components/features/plex/YamlImportModal', () => ({
  YamlImportModal: () => <div data-testid="yaml-import-modal" />,
}))

import { PlexCollectionsPage } from '../PlexCollectionsPage'

function renderPage() {
  return render(
    <MemoryRouter>
      <PlexCollectionsPage />
    </MemoryRouter>
  )
}

describe('PlexCollectionsPage', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('renders collection and playlist names', () => {
    renderPage()
    expect(screen.getByText('Action Films')).toBeInTheDocument()
    expect(screen.getByText('My Playlist')).toBeInTheDocument()
  })

  it('opens collection drawer when name is clicked', () => {
    renderPage()
    fireEvent.click(screen.getByText('Action Films'))
    expect(screen.getByTestId('collection-drawer')).toBeInTheDocument()
    expect(screen.queryByTestId('playlist-drawer')).not.toBeInTheDocument()
  })

  it('opens playlist drawer when name is clicked', () => {
    renderPage()
    fireEvent.click(screen.getByText('My Playlist'))
    expect(screen.getByTestId('playlist-drawer')).toBeInTheDocument()
    expect(screen.queryByTestId('collection-drawer')).not.toBeInTheDocument()
  })

  it('opening collection drawer clears playlist drawer', () => {
    renderPage()
    fireEvent.click(screen.getByText('My Playlist'))
    expect(screen.getByTestId('playlist-drawer')).toBeInTheDocument()
    fireEvent.click(screen.getByText('Action Films'))
    expect(screen.queryByTestId('playlist-drawer')).not.toBeInTheDocument()
    expect(screen.getByTestId('collection-drawer')).toBeInTheDocument()
  })

  it('closes drawer when close button clicked', () => {
    renderPage()
    fireEvent.click(screen.getByText('Action Films'))
    fireEvent.click(screen.getByText('Close'))
    expect(screen.queryByTestId('collection-drawer')).not.toBeInTheDocument()
  })

  it('closes drawer on Escape key', () => {
    renderPage()
    fireEvent.click(screen.getByText('Action Films'))
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByTestId('collection-drawer')).not.toBeInTheDocument()
  })
})
