import React, { useState, useEffect, useCallback, useMemo } from 'react'
import { storageService, type StorageFileItem, type StorageSummary } from '@/services/storageService'
import { Button, Pagination } from '@/components/common'
import { usePagination } from '@/hooks/usePagination'
import { formatBytes, formatDuration, formatCodec } from '@/utils/formatting'

// ── Efficiency badge ───────────────────────────────────────────────────────
const TIER_CONFIG = {
  efficient: { label: 'Efficient', className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
  moderate: { label: 'Moderate', className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
  large: { label: 'Large', className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
  unknown: { label: 'Pending', className: 'bg-subtle text-hint' },
} as const

function TierBadge({ tier }: { tier: StorageFileItem['efficiency_tier'] }) {
  const cfg = TIER_CONFIG[tier] ?? TIER_CONFIG.unknown
  return (
    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${cfg.className}`}>
      {cfg.label}
    </span>
  )
}

// ── Summary cards ──────────────────────────────────────────────────────────
function SummaryCards({ summary }: { summary: StorageSummary }) {
  const libraryTotal = summary.library.movies_bytes + summary.library.tv_bytes + summary.library.other_bytes
  const diskPct = summary.disk.total_bytes > 0
    ? Math.round(summary.disk.used_bytes / summary.disk.total_bytes * 100)
    : 0
  const totalFiles = summary.files_analyzed + summary.files_pending_analysis

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="rounded-xl border border-edge bg-card p-4">
        <p className="text-sm text-hint mb-1">Total Library</p>
        <p className="text-2xl font-bold text-body">{formatBytes(libraryTotal)}</p>
      </div>
      <div className="rounded-xl border border-edge bg-card p-4">
        <p className="text-sm text-hint mb-1">Disk Available</p>
        <p className="text-2xl font-bold text-body">{formatBytes(summary.disk.available_bytes)}</p>
        <p className="text-xs text-hint mt-1">{diskPct}% used of {formatBytes(summary.disk.total_bytes)}</p>
      </div>
      <div className="rounded-xl border border-edge bg-card p-4">
        <p className="text-sm text-hint mb-1">Potential Savings</p>
        <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
          ~{formatBytes(summary.potential_savings_bytes)}
        </p>
        <p className="text-xs text-hint mt-1">if re-encoded to H.265</p>
      </div>
      <div className="rounded-xl border border-edge bg-card p-4">
        <p className="text-sm text-hint mb-1">Files Analyzed</p>
        <p className="text-2xl font-bold text-body">
          {summary.files_analyzed} <span className="text-base font-normal text-hint">/ {totalFiles}</span>
        </p>
      </div>
    </div>
  )
}

// ── Column header with sort ────────────────────────────────────────────────
function SortHeader({
  label, field, sortBy, sortDir, onSort,
}: {
  label: string
  field: string
  sortBy: string
  sortDir: 'asc' | 'desc'
  onSort: (field: string) => void
}) {
  const active = sortBy === field
  return (
    <th
      className="px-4 py-3 text-left text-xs font-semibold text-hint uppercase tracking-wide cursor-pointer hover:text-body select-none whitespace-nowrap"
      onClick={() => onSort(field)}
    >
      {label}
      {active && <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>}
    </th>
  )
}

// ── TV show grouping ───────────────────────────────────────────────────────
type GroupHeader = { _groupHeader: true; show_title: string; show_fully_unwatched: boolean }
type GroupedRow = StorageFileItem | GroupHeader

function groupItemsWithShowHeaders(items: StorageFileItem[], showGrouping: boolean): GroupedRow[] {
  if (!showGrouping) return items
  const result: GroupedRow[] = []
  let lastShow: string | null = null
  const sorted = [...items].sort((a, b) => {
    if (a.show_title && b.show_title) return a.show_title.localeCompare(b.show_title)
    if (a.show_title) return 1
    if (b.show_title) return -1
    return 0
  })
  for (const item of sorted) {
    if (item.show_title && item.show_title !== lastShow) {
      result.push({
        _groupHeader: true,
        show_title: item.show_title,
        show_fully_unwatched: item.show_fully_unwatched ?? false,
      })
      lastShow = item.show_title
    }
    result.push(item)
  }
  return result
}

// ── Filter bar ─────────────────────────────────────────────────────────────
interface StorageFilterBarProps {
  filterMediaType: string
  filterEfficiency: string
  filterWatchedStatus: string
  total: number
  onMediaTypeChange: (v: string) => void
  onEfficiencyChange: (v: string) => void
  onWatchedStatusChange: (v: string) => void
}

function StorageFilterBar({
  filterMediaType,
  filterEfficiency,
  filterWatchedStatus,
  total,
  onMediaTypeChange,
  onEfficiencyChange,
  onWatchedStatusChange,
}: StorageFilterBarProps) {
  return (
    <div className="flex gap-3 flex-wrap items-center">
      <select
        value={filterMediaType}
        onChange={e => onMediaTypeChange(e.target.value)}
        className="text-sm rounded-lg border border-edge bg-card text-body px-3 py-1.5"
      >
        <option value="">All Types</option>
        <option value="movie">Movies</option>
        <option value="tv">TV Shows</option>
      </select>
      <select
        value={filterEfficiency}
        onChange={e => onEfficiencyChange(e.target.value)}
        className="text-sm rounded-lg border border-edge bg-card text-body px-3 py-1.5"
      >
        <option value="">All Tiers</option>
        <option value="large">Large</option>
        <option value="moderate">Moderate</option>
        <option value="efficient">Efficient</option>
        <option value="unknown">Pending</option>
      </select>
      <label htmlFor="filter-watched" className="sr-only">Watched Status</label>
      <select
        id="filter-watched"
        aria-label="Watched Status"
        value={filterWatchedStatus}
        onChange={e => onWatchedStatusChange(e.target.value)}
        className="rounded-lg border border-edge bg-card text-body text-sm px-3 py-2"
      >
        <option value="">All</option>
        <option value="unwatched">Unwatched</option>
        <option value="watched">Watched</option>
      </select>
      <span className="text-sm text-hint">
        {total} file{total !== 1 ? 's' : ''}
      </span>
    </div>
  )
}

// ── File table ─────────────────────────────────────────────────────────────
interface StorageFileTableProps {
  items: StorageFileItem[]
  loading: boolean
  page: number
  totalPages: number
  sortBy: string
  sortDir: 'asc' | 'desc'
  showGrouping: boolean
  onSort: (field: string) => void
  onPageChange: (p: number) => void
}

function StorageFileTable({
  items,
  loading,
  page,
  totalPages,
  sortBy,
  sortDir,
  showGrouping,
  onSort,
  onPageChange,
}: StorageFileTableProps) {
  const groupedRows = useMemo(
    () => groupItemsWithShowHeaders(items, showGrouping),
    [items, showGrouping]
  )
  return (
    <div className="rounded-xl border border-edge bg-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="border-b border-edge">
            <tr>
              <SortHeader label="File" field="name" sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
              <th className="px-4 py-3 text-left text-xs font-semibold text-hint uppercase tracking-wide">Type</th>
              <SortHeader label="Size" field="size_bytes" sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
              <SortHeader label="Duration" field="duration_seconds" sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
              <SortHeader label="MB/min" field="mb_per_min" sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
              <th className="px-4 py-3 text-left text-xs font-semibold text-hint uppercase tracking-wide">Codec</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-hint uppercase tracking-wide">Resolution</th>
              <SortHeader label="Est. Savings" field="estimated_savings_bytes" sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
              <th className="px-4 py-3 text-left text-xs font-semibold text-hint uppercase tracking-wide">Tier</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-edge">
            {loading ? (
              [...Array(10)].map((_, i) => (
                <tr key={i}>
                  {[...Array(9)].map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 rounded bg-subtle animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={9} className="px-4 py-12 text-center text-hint">
                  No files found.
                </td>
              </tr>
            ) : groupedRows.map((row, idx) => {
              if ('_groupHeader' in row) {
                return (
                  <tr key={`group-${row.show_title}`} className="bg-subtle">
                    <td colSpan={9} className="px-4 py-2">
                      <span className="font-semibold text-body text-sm">{row.show_title}</span>
                      <span className={`ml-2 text-xs px-1.5 py-0.5 rounded ${
                        row.show_fully_unwatched
                          ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                          : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                      }`}>
                        {row.show_fully_unwatched ? 'Never watched' : 'Partially watched'}
                      </span>
                    </td>
                  </tr>
                )
              }
              const item = row
              return (
                <tr key={`${item.id}-${idx}`} className="hover:bg-subtle transition-colors">
                  <td className="px-4 py-3 max-w-xs truncate font-medium text-body" title={item.name}>
                    {item.name}
                  </td>
                  <td className="px-4 py-3 text-hint capitalize">{item.media_type}</td>
                  <td className="px-4 py-3 text-dim whitespace-nowrap">{formatBytes(item.size_bytes)}</td>
                  <td className="px-4 py-3 text-hint whitespace-nowrap">{formatDuration(item.duration_seconds)}</td>
                  <td className="px-4 py-3 text-dim">{item.mb_per_min != null ? item.mb_per_min.toFixed(1) : '—'}</td>
                  <td className="px-4 py-3 text-hint">{formatCodec(item.video_codec)}</td>
                  <td className="px-4 py-3 text-hint uppercase text-xs">{item.resolution_tier === 'unknown' ? '—' : item.resolution_tier}</td>
                  <td className="px-4 py-3 text-dim whitespace-nowrap">
                    {item.estimated_savings_bytes > 0 ? `~${formatBytes(item.estimated_savings_bytes)}` : '—'}
                  </td>
                  <td className="px-4 py-3"><TierBadge tier={item.efficiency_tier} /></td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center px-4 py-3 border-t border-edge">
          <Pagination currentPage={page} totalPages={totalPages} onPageChange={onPageChange} />
        </div>
      )}
    </div>
  )
}

// ── Constants ──────────────────────────────────────────────────────────────
const PAGE_SIZE = 50
// allow scan task to enqueue before reloading
const SCAN_POLL_DELAY_MS = 3000

// ── Main page ──────────────────────────────────────────────────────────────
export function StoragePage() {
  const [summary, setSummary] = useState<StorageSummary | null>(null)
  const [items, setItems] = useState<StorageFileItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)
  const [sortBy, setSortBy] = useState('size_bytes')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [filterMediaType, setFilterMediaType] = useState('')
  const [filterEfficiency, setFilterEfficiency] = useState('')
  const [filterWatchedStatus, setFilterWatchedStatus] = useState('')

  const { page, totalPages, goToPage } = usePagination(1, PAGE_SIZE, total)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [summaryData, filesData] = await Promise.all([
        storageService.getSummary(),
        storageService.getFiles({
          page,
          pageSize: PAGE_SIZE,
          sortBy,
          sortDir,
          mediaType: filterMediaType || undefined,
          efficiencyTier: filterEfficiency || undefined,
          watchedStatus: (filterWatchedStatus as 'watched' | 'unwatched') || undefined,
        }),
      ])
      setSummary(summaryData)
      setItems(filesData.items)
      setTotal(filesData.total)
    } catch (err) {
      console.error('StoragePage: failed to load', err)
    } finally {
      setLoading(false)
    }
  }, [page, sortBy, sortDir, filterMediaType, filterEfficiency, filterWatchedStatus])

  useEffect(() => { load() }, [load])

  const handleAnalyseNow = async () => {
    setScanning(true)
    try {
      await storageService.triggerScan()
      setTimeout(() => { load(); setScanning(false) }, SCAN_POLL_DELAY_MS)
    } catch (err) {
      console.error('StoragePage: scan trigger failed', err)
      setScanning(false)
    }
  }

  const handleSort = (field: string) => {
    if (field === sortBy) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(field)
      setSortDir('desc')
    }
    goToPage(1)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-body">Storage Analytics</h1>
          <p className="text-hint mt-1">
            File efficiency analysis — MB/min, codec, and estimated re-encode savings.
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={handleAnalyseNow}
          disabled={scanning}
          loading={scanning}
        >
          {scanning ? 'Analysing…' : 'Analyse Now'}
        </Button>
      </div>

      {/* Summary cards */}
      {loading && !summary ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 rounded-xl bg-subtle animate-pulse" />
          ))}
        </div>
      ) : summary ? (
        <SummaryCards summary={summary} />
      ) : null}

      {/* Pending banner */}
      {summary && summary.files_pending_analysis > 0 && (
        <div className="rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 px-4 py-3 text-sm text-amber-800 dark:text-amber-300">
          Technical metadata is being gathered for <strong>{summary.files_pending_analysis}</strong> files — refresh to update.
        </div>
      )}

      <StorageFilterBar
        filterMediaType={filterMediaType}
        filterEfficiency={filterEfficiency}
        filterWatchedStatus={filterWatchedStatus}
        total={total}
        onMediaTypeChange={v => { setFilterMediaType(v); goToPage(1) }}
        onEfficiencyChange={v => { setFilterEfficiency(v); goToPage(1) }}
        onWatchedStatusChange={v => { setFilterWatchedStatus(v); goToPage(1) }}
      />

      {/* Recoverable space banner */}
      {filterWatchedStatus === 'unwatched' && summary && (
        <div className="rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 px-4 py-3 text-sm text-amber-800 dark:text-amber-200">
          <span className="font-semibold">
            {formatBytes(summary.unwatched_movie_size_bytes + summary.unwatched_tv_size_bytes)}
          </span>{' '}
          potentially recoverable from unwatched files.
        </div>
      )}

      <StorageFileTable
        items={items}
        loading={loading}
        page={page}
        totalPages={totalPages}
        sortBy={sortBy}
        sortDir={sortDir}
        showGrouping={filterWatchedStatus === 'unwatched'}
        onSort={handleSort}
        onPageChange={goToPage}
      />
    </div>
  )
}

export default StoragePage
