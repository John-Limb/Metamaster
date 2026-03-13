import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createMediaStore } from '../createMediaStore'
import type { MediaStoreService } from '../createMediaStore'
import type { PaginatedResponse } from '@/types'

interface TestItem {
  id: string
  title: string
  value?: number
}

const makeItem = (id: string, title = `Item ${id}`): TestItem => ({ id, title })

const makePaginated = (items: TestItem[], total?: number): PaginatedResponse<TestItem> => ({
  items,
  total: total ?? items.length,
  limit: 20,
  offset: 0,
  page: 1,
  pageSize: 20,
  totalPages: 1,
})

const makeService = (overrides: Partial<MediaStoreService<TestItem>> = {}): MediaStoreService<TestItem> => ({
  getItems: vi.fn().mockResolvedValue(makePaginated([])),
  getItemDetails: vi.fn().mockResolvedValue(makeItem('1')),
  searchItems: vi.fn().mockResolvedValue(makePaginated([])),
  getItemsByGenre: vi.fn().mockResolvedValue(makePaginated([])),
  getPopularItems: vi.fn().mockResolvedValue(makePaginated([])),
  getTopRatedItems: vi.fn().mockResolvedValue(makePaginated([])),
  createItem: vi.fn().mockResolvedValue(makeItem('new')),
  updateItem: vi.fn().mockResolvedValue(makeItem('1', 'Updated')),
  deleteItem: vi.fn().mockResolvedValue(undefined),
  ...overrides,
})

describe('createMediaStore', () => {
  let service: MediaStoreService<TestItem>
  let useStore: ReturnType<typeof createMediaStore<TestItem>>

  beforeEach(() => {
    service = makeService()
    useStore = createMediaStore<TestItem>(service, `test-store-${Math.random()}`)
    useStore.setState({
      items: [],
      selectedItem: null,
      total: 0,
      currentPage: 1,
      pageSize: 20,
      isLoading: false,
      error: null,
      genreFilter: null,
      yearFilter: null,
      sortBy: 'title',
      sortOrder: 'asc',
    })
  })

  it('fetchItems populates items and total', async () => {
    vi.mocked(service.getItems).mockResolvedValue(makePaginated([makeItem('1'), makeItem('2')], 5))
    await useStore.getState().fetchItems(1, 20)
    expect(useStore.getState().items).toHaveLength(2)
    expect(useStore.getState().total).toBe(5)
    expect(useStore.getState().currentPage).toBe(1)
    expect(useStore.getState().isLoading).toBe(false)
  })

  it('fetchItemDetails sets selectedItem', async () => {
    const item = makeItem('42', 'Detail Item')
    vi.mocked(service.getItemDetails).mockResolvedValue(item)
    const result = await useStore.getState().fetchItemDetails('42')
    expect(useStore.getState().selectedItem).toEqual(item)
    expect(result).toEqual(item)
  })

  it('searchItems updates items', async () => {
    vi.mocked(service.searchItems).mockResolvedValue(makePaginated([makeItem('3')]))
    await useStore.getState().searchItems('test')
    expect(useStore.getState().items).toHaveLength(1)
    expect(service.searchItems).toHaveBeenCalledWith('test', 1, 20)
  })

  it('fetchItemsByGenre sets genreFilter', async () => {
    vi.mocked(service.getItemsByGenre).mockResolvedValue(makePaginated([makeItem('4')]))
    await useStore.getState().fetchItemsByGenre('Action')
    expect(useStore.getState().genreFilter).toBe('Action')
    expect(useStore.getState().items).toHaveLength(1)
  })

  it('createItem prepends to items and increments total', async () => {
    useStore.setState({ items: [makeItem('1')], total: 1 })
    vi.mocked(service.createItem).mockResolvedValue(makeItem('2'))
    await useStore.getState().createItem({ title: 'New' })
    expect(useStore.getState().items[0].id).toBe('2')
    expect(useStore.getState().total).toBe(2)
  })

  it('updateItem replaces item and updates selectedItem', async () => {
    const original = makeItem('1', 'Original')
    const updated = makeItem('1', 'Updated')
    useStore.setState({ items: [original], selectedItem: original, total: 1 })
    vi.mocked(service.updateItem).mockResolvedValue(updated)
    await useStore.getState().updateItem('1', { title: 'Updated' })
    expect(useStore.getState().items[0].title).toBe('Updated')
    expect(useStore.getState().selectedItem?.title).toBe('Updated')
  })

  it('deleteItem removes item and decrements total', async () => {
    useStore.setState({ items: [makeItem('1'), makeItem('2')], total: 2 })
    await useStore.getState().deleteItem('1')
    expect(useStore.getState().items).toHaveLength(1)
    expect(useStore.getState().items[0].id).toBe('2')
    expect(useStore.getState().total).toBe(1)
  })

  it('deleteItem clears selectedItem when deleted', async () => {
    const item = makeItem('1')
    useStore.setState({ items: [item], selectedItem: item, total: 1 })
    await useStore.getState().deleteItem('1')
    expect(useStore.getState().selectedItem).toBeNull()
  })

  it('sets error on fetchItems failure', async () => {
    vi.mocked(service.getItems).mockRejectedValue(new Error('Network error'))
    await expect(useStore.getState().fetchItems()).rejects.toThrow('Network error')
    expect(useStore.getState().error).toBe('Network error')
    expect(useStore.getState().isLoading).toBe(false)
  })

  it('selectItem and getById work correctly', () => {
    const item = makeItem('5')
    useStore.setState({ items: [item] })
    useStore.getState().selectItem(item)
    expect(useStore.getState().selectedItem).toEqual(item)
    expect(useStore.getState().getById('5')).toEqual(item)
    expect(useStore.getState().getById('999')).toBeUndefined()
  })

  it('filter setters and clearFilters', () => {
    useStore.getState().setGenreFilter('Drama')
    useStore.getState().setYearFilter(2020)
    useStore.getState().setSortBy('rating')
    useStore.getState().setSortOrder('desc')
    expect(useStore.getState().genreFilter).toBe('Drama')
    expect(useStore.getState().yearFilter).toBe(2020)
    expect(useStore.getState().sortBy).toBe('rating')
    expect(useStore.getState().sortOrder).toBe('desc')
    useStore.getState().clearFilters()
    expect(useStore.getState().genreFilter).toBeNull()
    expect(useStore.getState().yearFilter).toBeNull()
  })

  it('addItem, removeItem, updateLocalItem', () => {
    const a = makeItem('a')
    const b = makeItem('b')
    useStore.setState({ items: [a], total: 1 })
    useStore.getState().addItem(b)
    expect(useStore.getState().items).toHaveLength(2)
    expect(useStore.getState().total).toBe(2)
    useStore.getState().removeItem('a')
    expect(useStore.getState().items[0].id).toBe('b')
    expect(useStore.getState().total).toBe(1)
    useStore.getState().updateLocalItem('b', { title: 'Updated B' })
    expect(useStore.getState().items[0].title).toBe('Updated B')
  })
})
