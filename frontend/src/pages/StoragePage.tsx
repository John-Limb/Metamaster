import React, { useState, useEffect, useCallback } from 'react'
import { storageService, type StorageFileItem, type StorageSummary } from '@/services/storageService'

// ── Codec display names ────────────────────────────────────────────────────
const CODEC_LABEL: Record<string, string> = {
  h264: 'H.264',
  hevc: 'H.265',
  av1: 'AV1',
  vp9: 'VP9',
  mpeg2video: 'MPEG-2',
  vc1: 'VC-1',
  wmv3: 'WMV',
}

function formatCodec(codec: string | null): string {
  if (!codec) return '—'
  return CODEC_LABEL[codec.toLowerCase()] ?? codec.toUpperCase()
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return '—'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

function formatBytes(bytes: number): string {
  if (bytes >= 1e12) return `${(bytes / 1e12).toFixed(1)} TB`
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(1)} GB`
  if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(0)} MB`
  return `${bytes} B`
}

// ── Efficiency badge ───────────────────────────────────────────────────────
const TIER_CONFIG = {
  efficient: { label: 'Efficient', className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' },
  moderate: { label: 'Moderate', className: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' },
  large: { label: 'Large', className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
  unknown: { label: 'Pending', className: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400' },
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
      <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Total Library</p>
        <p className="text-2xl font-bold text-slate-900 dark:text-white">{formatBytes(libraryTotal)}</p>
      </div>
      <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Disk Available</p>
        <p className="text-2xl font-bold text-slate-900 dark:text-white">{formatBytes(summary.disk.available_bytes)}</p>
        <p className="text-xs text-slate-400 mt-1">{diskPct}% used of {formatBytes(summary.disk.total_bytes)}</p>
      </div>
      <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Potential Savings</p>
        <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
          ~{formatBytes(summary.potential_savings_bytes)}
        </p>
        <p className="text-xs text-slate-400 mt-1">if re-encoded to H.265</p>
      </div>
      <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-4">
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Files Analyzed</p>
        <p className="text-2xl font-bold text-slate-900 dark:text-white">
          {summary.files_analyzed} <span className="text-base font-normal text-slate-400">/ {totalFiles}</span>
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
      className="px-4 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide cursor-pointer hover:text-slate-900 dark:hover:text-white select-none whitespace-nowrap"
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

// ── Main page ──────────────────────────────────────────────────────────────
export function StoragePage() {
  const [summary, setSummary] = useState<StorageSummary | null>(null)
  const [items, setItems] = useState<StorageFileItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('size_bytes')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [filterMediaType, setFilterMediaType] = useState('')
  const [filterEfficiency, setFilterEfficiency] = useState('')
  const [filterWatchedStatus, setFilterWatchedStatus] = useState('')

  const PAGE_SIZE = 50

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
      // Give the worker a moment then reload so updated counts show
      setTimeout(() => { load(); setScanning(false) }, 3000)
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
    setPage(1)
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Storage Analytics</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            File efficiency analysis — MB/min, codec, and estimated re-encode savings.
          </p>
        </div>
        <button
          onClick={handleAnalyseNow}
          disabled={scanning}
          className="shrink-0 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white text-sm font-medium transition-colors"
        >
          {scanning ? (
            <>
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 100 16v-4l-3 3 3 3v-4a8 8 0 01-8-8z" />
              </svg>
              Analysing…
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" />
              </svg>
              Analyse Now
            </>
          )}
        </button>
      </div>

      {/* Summary cards */}
      {loading && !summary ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 rounded-xl bg-slate-200 dark:bg-slate-700 animate-pulse" />
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

      {/* Filters */}
      <div className="flex gap-3 flex-wrap items-center">
        <select
          value={filterMediaType}
          onChange={e => { setFilterMediaType(e.target.value); setPage(1) }}
          className="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-1.5"
        >
          <option value="">All Types</option>
          <option value="movie">Movies</option>
          <option value="tv">TV Shows</option>
        </select>
        <select
          value={filterEfficiency}
          onChange={e => { setFilterEfficiency(e.target.value); setPage(1) }}
          className="text-sm rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-1.5"
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
          onChange={e => { setFilterWatchedStatus(e.target.value); setPage(1) }}
          className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-sm px-3 py-2"
        >
          <option value="">All</option>
          <option value="unwatched">Unwatched</option>
          <option value="watched">Watched</option>
        </select>
        <span className="text-sm text-slate-500 dark:text-slate-400">
          {total} file{total !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Recoverable space banner */}
      {filterWatchedStatus === 'unwatched' && summary && (
        <div className="rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 px-4 py-3 text-sm text-amber-800 dark:text-amber-200">
          <span className="font-semibold">
            {formatBytes(summary.unwatched_movie_size_bytes + summary.unwatched_tv_size_bytes)}
          </span>{' '}
          potentially recoverable from unwatched files.
        </div>
      )}

      {/* File table */}
      <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-200 dark:border-slate-700">
              <tr>
                <SortHeader label="File" field="name" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Type</th>
                <SortHeader label="Size" field="size_bytes" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                <SortHeader label="Duration" field="duration_seconds" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                <SortHeader label="MB/min" field="mb_per_min" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Codec</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Resolution</th>
                <SortHeader label="Est. Savings" field="estimated_savings_bytes" sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Tier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {loading ? (
                [...Array(10)].map((_, i) => (
                  <tr key={i}>
                    {[...Array(9)].map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 rounded bg-slate-200 dark:bg-slate-700 animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-12 text-center text-slate-500 dark:text-slate-400">
                    No files found.
                  </td>
                </tr>
              ) : groupItemsWithShowHeaders(items, filterWatchedStatus === 'unwatched').map((row, idx) => {
                if ('_groupHeader' in row) {
                  return (
                    <tr key={`group-${row.show_title}`} className="bg-slate-50 dark:bg-slate-800/50">
                      <td colSpan={9} className="px-4 py-2">
                        <span className="font-semibold text-slate-700 dark:text-slate-200 text-sm">{row.show_title}</span>
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
                  <tr key={`${item.id}-${idx}`} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                    <td className="px-4 py-3 max-w-xs truncate font-medium text-slate-900 dark:text-white" title={item.name}>
                      {item.name}
                    </td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400 capitalize">{item.media_type}</td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-300 whitespace-nowrap">{formatBytes(item.size_bytes)}</td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400 whitespace-nowrap">{formatDuration(item.duration_seconds)}</td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-300">{item.mb_per_min != null ? item.mb_per_min.toFixed(1) : '—'}</td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{formatCodec(item.video_codec)}</td>
                    <td className="px-4 py-3 text-slate-500 dark:text-slate-400 uppercase text-xs">{item.resolution_tier === 'unknown' ? '—' : item.resolution_tier}</td>
                    <td className="px-4 py-3 text-slate-700 dark:text-slate-300 whitespace-nowrap">
                      {item.estimated_savings_bytes > 0 ? `~${formatBytes(item.estimated_savings_bytes)}` : '—'}
                    </td>
                    <td className="px-4 py-3"><TierBadge tier={item.efficiency_tier} /></td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200 dark:border-slate-700">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="text-sm px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-800"
            >
              Previous
            </button>
            <span className="text-sm text-slate-500 dark:text-slate-400">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="text-sm px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-800"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default StoragePage
