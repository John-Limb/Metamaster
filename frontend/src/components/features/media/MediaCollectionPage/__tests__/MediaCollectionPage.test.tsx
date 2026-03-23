import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  MediaCollectionPage,
  type MediaCollectionConfig,
  type MediaCollectionStore,
} from '../MediaCollectionPage'

vi.mock('@/stores/plexStore', () => ({
  usePlexStore: () => ({ mismatches: [], resolveMismatch: vi.fn() }),
}))

vi.mock('@/stores/uiStore', () => ({
  useUIStore: () => ({ addToast: vi.fn() }),
}))

function makeStore<T>(overrides: Partial<MediaCollectionStore<T>> = {}): MediaCollectionStore<T> {
  return {
    items: [],
    total: 0,
    currentPage: 1,
    isLoading: false,
    error: null,
    fetchItems: vi.fn().mockResolvedValue(undefined),
    ...overrides,
  }
}

const baseConfig: MediaCollectionConfig<{ id: string }> = {
  title: 'Test Library',
  mediaType: 'movie',
  cssPrefix: 'test-page',
  useStore: () => makeStore(),
  onScanDirectory: vi.fn().mockResolvedValue({ files_synced: 2, items_created: 1 }),
  formatScanResult: (r) => `${r.files_synced} synced`,
  renderCard: (item) => <div>{item.id}</div>,
  filterSections: [],
  sortOptions: [],
  defaultSort: 'name-asc',
}

function renderPage(config: MediaCollectionConfig<{ id: string }> = baseConfig) {
  return render(
    <MemoryRouter>
      <MediaCollectionPage config={config} />
    </MemoryRouter>
  )
}

describe('MediaCollectionPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the page title', () => {
    renderPage()
    expect(screen.getByText('Test Library')).toBeInTheDocument()
  })

  it('calls fetchItems on mount with (1, 12)', () => {
    const fetchItems = vi.fn().mockResolvedValue(undefined)
    const config = {
      ...baseConfig,
      useStore: () => makeStore({ fetchItems }),
    }
    renderPage(config)
    expect(fetchItems).toHaveBeenCalledWith(1, 12)
  })

  it('shows error AlertMessage when error is set', () => {
    const config = {
      ...baseConfig,
      useStore: () => makeStore({ error: 'Something went wrong' }),
    }
    renderPage(config)
    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Try again')).toBeInTheDocument()
  })

  it('scan button triggers onScanDirectory', async () => {
    const onScanDirectory = vi.fn().mockResolvedValue({ files_synced: 2, items_created: 1 })
    const config = {
      ...baseConfig,
      onScanDirectory,
    }
    renderPage(config)
    const scanBtn = screen.getByRole('button', { name: /scan now/i })
    fireEvent.click(scanBtn)
    await waitFor(() => {
      expect(onScanDirectory).toHaveBeenCalledTimes(1)
    })
  })
})
