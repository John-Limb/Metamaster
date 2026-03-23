import React, { useState, useCallback, useEffect, useMemo } from 'react'
import { Button, Pagination, EmptyState, SkeletonCard, AlertMessage } from '@/components/common'
import { FilterPanel, type FilterSection } from '@/components/features/filter'
import { SortDropdown, type SortOption } from '@/components/features/sort'
import { MediaDetailModal } from '../MediaDetailModal'
import { usePlexStore } from '@/stores/plexStore'
import { useUIStore } from '@/stores/uiStore'
import type { PlexMismatchItem } from '@/services/plexService'

// ─── SVG icon constants ───────────────────────────────────────────────────────

const GRID_ICON = (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" />
    <rect x="14" y="3" width="7" height="7" />
    <rect x="14" y="14" width="7" height="7" />
    <rect x="3" y="14" width="7" height="7" />
  </svg>
)

const LIST_ICON = (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="8" y1="6" x2="21" y2="6" />
    <line x1="8" y1="12" x2="21" y2="12" />
    <line x1="8" y1="18" x2="21" y2="18" />
    <line x1="3" y1="6" x2="3.01" y2="6" />
    <line x1="3" y1="12" x2="3.01" y2="12" />
    <line x1="3" y1="18" x2="3.01" y2="18" />
  </svg>
)

const SEARCH_ICON = (
  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
    fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8" />
    <path d="M21 21l-4.35-4.35" />
  </svg>
)

const ITEMS_PER_PAGE = 12

// ─── Interfaces ───────────────────────────────────────────────────────────────

export interface MediaCollectionStore<TItem> {
  items: TItem[]
  total: number
  currentPage: number
  isLoading: boolean
  error: string | null
  fetchItems: (page?: number, pageSize?: number) => Promise<void>
}

export interface MediaCollectionConfig<TItem extends { id: string }> {
  title: string
  mediaType: 'movie' | 'tv_show'
  cssPrefix: string
  useStore: () => MediaCollectionStore<TItem>
  onScanDirectory: () => Promise<{ files_synced: number; items_created: number }>
  formatScanResult: (result: { files_synced: number; items_created: number }) => string
  renderCard: (item: TItem, mismatch: PlexMismatchItem | undefined) => React.ReactNode
  filterSections: FilterSection[]
  sortOptions: SortOption[]
  defaultSort: string
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

export function pageSubtitle(isLoading: boolean, total: number, noun: string): string {
  if (isLoading) return 'Loading...'
  if (total > 0) return `${total} ${noun}${total !== 1 ? 's' : ''} in your library`
  return `No ${noun}s found`
}

// ─── GridBody sub-component ───────────────────────────────────────────────────

interface GridBodyProps<TItem extends { id: string }> {
  isLoading: boolean
  items: TItem[]
  viewMode: 'grid' | 'list'
  cssPrefix: string
  currentPage: number
  totalPages: number
  mismatchMap: Map<number, PlexMismatchItem>
  renderCard: (item: TItem, mismatch: PlexMismatchItem | undefined) => React.ReactNode
  onItemClick: (id: string) => void
  onClearFilters: () => void
  onPageChange: (page: number) => void
}

function GridBody<TItem extends { id: string }>({
  isLoading,
  items,
  viewMode,
  cssPrefix,
  currentPage,
  totalPages,
  mismatchMap,
  renderCard,
  onItemClick,
  onClearFilters,
  onPageChange,
}: GridBodyProps<TItem>) {
  const gridClass = `${cssPrefix}__grid ${cssPrefix}__grid--${viewMode}`

  if (isLoading) {
    return (
      <div className={gridClass}>
        {Array.from({ length: ITEMS_PER_PAGE }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  if (items.length === 0) {
    return (
      <EmptyState
        variant="empty"
        title="No items found"
        description="Your library will appear here once media files are synced."
        action={{ label: 'Clear filters', onClick: onClearFilters }}
      />
    )
  }

  return (
    <>
      <div className={gridClass}>
        {items.map((item) => {
          const mismatch = mismatchMap.get(Number(item.id))
          return (
            <div key={item.id} onClick={() => onItemClick(item.id)}>
              {renderCard(item, mismatch)}
            </div>
          )
        })}
      </div>
      {totalPages > 1 && (
        <div className={`${cssPrefix}__pagination`}>
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={onPageChange}
          />
        </div>
      )}
    </>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

interface MediaCollectionPageProps<TItem extends { id: string }> {
  config: MediaCollectionConfig<TItem>
}

export function MediaCollectionPage<TItem extends { id: string }>({
  config,
}: MediaCollectionPageProps<TItem>) {
  const {
    title,
    mediaType,
    cssPrefix,
    useStore,
    onScanDirectory,
    formatScanResult,
    renderCard,
    filterSections,
    sortOptions,
    defaultSort,
  } = config

  const { items, total, currentPage, isLoading, error, fetchItems } = useStore()
  const { mismatches } = usePlexStore()
  const mismatchMap = useMemo(
    () => new Map(mismatches.map((m) => [m.item_id, m])),
    [mismatches]
  )
  const { addToast } = useUIStore()

  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>({})
  const [sortValue, setSortValue] = useState(defaultSort)
  const [isScanning, setIsScanning] = useState(false)
  const [modalItemId, setModalItemId] = useState<string | null>(null)

  useEffect(() => {
    fetchItems(1, ITEMS_PER_PAGE)
  }, [fetchItems])

  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  const handleFilterChange = useCallback((sectionId: string, values: string[]) => {
    setSelectedFilters((prev) => ({ ...prev, [sectionId]: values }))
  }, [])

  const handleClearFilters = useCallback(() => {
    setSelectedFilters({})
  }, [])

  const handlePageChange = useCallback((page: number) => {
    fetchItems(page, ITEMS_PER_PAGE)
  }, [fetchItems])

  const handleScanDirectory = useCallback(async () => {
    setIsScanning(true)
    try {
      const result = await onScanDirectory()
      addToast({ type: 'success', message: formatScanResult(result), duration: 5000 })
    } catch {
      addToast({ type: 'error', message: 'Scan failed. Check the server logs for details.', duration: 5000 })
    } finally {
      setIsScanning(false)
    }
  }, [onScanDirectory, formatScanResult, addToast])

  const noun = mediaType === 'movie' ? 'movie' : 'show'
  const subtitle = pageSubtitle(isLoading, total, noun)

  return (
    <div className={cssPrefix}>
      <header className={`${cssPrefix}__header`}>
        <div className={`${cssPrefix}__title-section`}>
          <h1 className={`${cssPrefix}__title`}>{title}</h1>
          <p className={`${cssPrefix}__subtitle`}>{subtitle}</p>
        </div>
        <div className={`${cssPrefix}__search`}>
          <span className={`${cssPrefix}__search-icon`}>{SEARCH_ICON}</span>
          <input
            type="text"
            placeholder={`Search ${title.toLowerCase()}...`}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className={`${cssPrefix}__search-input`}
          />
        </div>
      </header>

      <div className={`${cssPrefix}__toolbar`}>
        <div className={`${cssPrefix}__toolbar-left`}>
          <FilterPanel
            sections={filterSections}
            selectedFilters={selectedFilters}
            onFilterChange={handleFilterChange}
            onClearAll={handleClearFilters}
            isOpen={isFilterOpen}
            onToggle={() => setIsFilterOpen(!isFilterOpen)}
          />
          <SortDropdown options={sortOptions} value={sortValue} onChange={setSortValue} />
        </div>
        <div className={`${cssPrefix}__toolbar-right`}>
          <Button variant="secondary" size="sm" onClick={handleScanDirectory} disabled={isScanning}>
            {isScanning ? 'Scanning...' : 'Scan Now'}
          </Button>
          <div className={`${cssPrefix}__view-toggle`} role="group" aria-label="View mode">
            <Button
              variant={viewMode === 'grid' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setViewMode('grid')}
              aria-pressed={viewMode === 'grid'}
            >
              {GRID_ICON}
            </Button>
            <Button
              variant={viewMode === 'list' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => setViewMode('list')}
              aria-pressed={viewMode === 'list'}
            >
              {LIST_ICON}
            </Button>
          </div>
        </div>
      </div>

      <main className={`${cssPrefix}__content`}>
        {error && (
          <AlertMessage
            variant="error"
            message={
              <>
                <p>{error}</p>
                <button
                  onClick={() => fetchItems(currentPage, ITEMS_PER_PAGE)}
                  className="mt-2 text-sm underline hover:no-underline"
                >
                  Try again
                </button>
              </>
            }
            className="mb-4"
          />
        )}
        <GridBody
          isLoading={isLoading}
          items={items}
          viewMode={viewMode}
          cssPrefix={cssPrefix}
          currentPage={currentPage}
          totalPages={totalPages}
          mismatchMap={mismatchMap}
          renderCard={renderCard}
          onItemClick={setModalItemId}
          onClearFilters={handleClearFilters}
          onPageChange={handlePageChange}
        />
      </main>

      <MediaDetailModal
        isOpen={modalItemId !== null}
        mediaType={mediaType}
        mediaId={modalItemId ?? ''}
        onClose={() => setModalItemId(null)}
        onMetadataSynced={() => fetchItems(currentPage, ITEMS_PER_PAGE)}
      />
    </div>
  )
}
