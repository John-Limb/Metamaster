import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { movieService, type EnrichmentStatusGroup, type EnrichmentStats } from '@/services/movieService'
import { tvShowService } from '@/services/tvShowService'
import { EnrichmentBadge } from '@/components/features/media/EnrichmentBadge/EnrichmentBadge'
import type { Movie, TVShow } from '@/types'

type MediaType = 'movies' | 'tv-shows'
type FilterTab = 'all' | EnrichmentStatusGroup

interface Tab {
  key: FilterTab
  label: string
  countKey?: keyof EnrichmentStats
}

const TABS: Tab[] = [
  { key: 'all', label: 'All' },
  { key: 'indexed', label: 'Indexed', countKey: 'indexed' },
  { key: 'pending', label: 'Pending', countKey: 'pending' },
  { key: 'failed', label: 'Failed', countKey: 'failed' },
]

const PAGE_SIZE = 50

type MediaItem = (Movie | TVShow) & {
  enrichment_status?: string | null
  enrichment_error?: string | null
}

export const EnrichmentPage: React.FC = () => {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const initialMediaType = (searchParams.get('type') as MediaType) || 'movies'
  const initialTab = (searchParams.get('status') as FilterTab) || 'all'

  const [mediaType, setMediaType] = useState<MediaType>(initialMediaType)
  const [activeTab, setActiveTab] = useState<FilterTab>(initialTab)
  const [items, setItems] = useState<MediaItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [isLoading, setIsLoading] = useState(true)
  const [stats, setStats] = useState<EnrichmentStats | null>(null)

  const fetchStats = useCallback(async (type: MediaType) => {
    try {
      const data = type === 'movies'
        ? await movieService.getEnrichmentStats()
        : await tvShowService.getEnrichmentStats()
      setStats(data)
    } catch {
      // stats are non-critical; silently ignore
    }
  }, [])

  const fetchItems = useCallback(async (type: MediaType, tab: FilterTab, currentPage: number) => {
    setIsLoading(true)
    try {
      const status = tab === 'all' ? undefined : tab
      const result = type === 'movies'
        ? await movieService.getMovies(currentPage, PAGE_SIZE, status)
        : await tvShowService.getTVShows(currentPage, PAGE_SIZE, status)
      setItems(result?.items ?? [])
      setTotal(result?.total ?? 0)
    } catch {
      setItems([])
      setTotal(0)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    setStats(null)
    setPage(1)
    setActiveTab('all')
    fetchStats(mediaType)
  }, [mediaType, fetchStats])

  useEffect(() => {
    setPage(1)
    fetchItems(mediaType, activeTab, 1)
    const params: Record<string, string> = {}
    if (mediaType !== 'movies') params.type = mediaType
    if (activeTab !== 'all') params.status = activeTab
    setSearchParams(params, { replace: true })
  }, [activeTab, mediaType, fetchItems, setSearchParams])

  useEffect(() => {
    if (page > 1) fetchItems(mediaType, activeTab, page)
  }, [page, activeTab, mediaType, fetchItems])

  const getTabCount = (tab: Tab): number | undefined => {
    if (!stats || !tab.countKey) return undefined
    if (tab.key === 'all') return stats.total
    return stats[tab.countKey]
  }

  const handleRowClick = (item: MediaItem) => {
    if (mediaType === 'movies') {
      navigate(`/movies/${item.id}`)
    } else {
      navigate(`/tv-shows/${item.id}`)
    }
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Enrichment Status</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1">
          Track metadata enrichment across your media library.
        </p>
      </div>

      {/* Media type switcher */}
      <div className="flex gap-2">
        {(['movies', 'tv-shows'] as MediaType[]).map((type) => (
          <button
            key={type}
            onClick={() => setMediaType(type)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              mediaType === type
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            {type === 'movies' ? 'Movies' : 'TV Shows'}
          </button>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 border-b border-slate-200 dark:border-slate-700">
        {TABS.map((tab) => {
          const count = getTabCount(tab) ?? (tab.key === 'all' ? total : undefined)
          const isActive = activeTab === tab.key
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`
                px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors
                ${isActive
                  ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                  : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}
              `}
            >
              {tab.label}
              {count !== undefined && (
                <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full font-medium
                  ${isActive
                    ? 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/50 dark:text-indigo-400'
                    : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'}`}>
                  {count}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Table */}
      <div className="rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 dark:bg-slate-800">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-300">Title</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-300 w-16">Year</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-300 w-36">Status</th>
              <th className="px-4 py-3 text-left font-medium text-slate-600 dark:text-slate-300">Error</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td className="px-4 py-3"><div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-48" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-10" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-24" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-40" /></td>
                </tr>
              ))
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-12 text-center text-slate-500 dark:text-slate-400">
                  No {mediaType === 'movies' ? 'movies' : 'TV shows'} found.
                </td>
              </tr>
            ) : (
              items.map((item) => (
                <tr
                  key={item.id}
                  onClick={() => handleRowClick(item)}
                  className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                >
                  <td className="px-4 py-3 font-medium text-slate-900 dark:text-white">
                    {item.title}
                  </td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">
                    {item.year ?? '—'}
                  </td>
                  <td className="px-4 py-3">
                    <EnrichmentBadge status={item.enrichment_status as any} />
                  </td>
                  <td className="px-4 py-3 text-slate-400 dark:text-slate-500 text-xs truncate max-w-xs">
                    {item.enrichment_error ?? '—'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
          <span>{total} total</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
            >
              Previous
            </button>
            <span className="px-3 py-1">Page {page} of {totalPages}</span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1 rounded border border-slate-200 dark:border-slate-700 disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
