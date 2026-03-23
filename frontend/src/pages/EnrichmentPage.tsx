import React, { useState, useEffect, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { movieService, type EnrichmentStatusGroup, type EnrichmentStats } from '@/services/movieService'
import { tvShowService } from '@/services/tvShowService'
import { EnrichmentBadge, type EnrichmentStatus } from '@/components/features/media/EnrichmentBadge/EnrichmentBadge'
import { Pagination } from '@/components/common'
import { Button } from '@/components/common/Button/Button'
import { usePagination } from '@/hooks/usePagination'
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
  const [isLoading, setIsLoading] = useState(true)
  const [stats, setStats] = useState<EnrichmentStats | null>(null)

  const { page, totalPages, goToPage } = usePagination(1, PAGE_SIZE, total)

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
    goToPage(1)
    setActiveTab('all')
    fetchStats(mediaType)
  }, [mediaType, fetchStats, goToPage])

  useEffect(() => {
    goToPage(1)
    const params: Record<string, string> = {}
    if (mediaType !== 'movies') params.type = mediaType
    if (activeTab !== 'all') params.status = activeTab
    setSearchParams(params, { replace: true })
  }, [activeTab, mediaType, setSearchParams, goToPage])

  useEffect(() => {
    fetchItems(mediaType, activeTab, page)
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-body">Enrichment Status</h1>
        <p className="text-hint mt-1">
          Track metadata enrichment across your media library.
        </p>
      </div>

      {/* Media type switcher */}
      <div className="flex gap-2">
        {(['movies', 'tv-shows'] as MediaType[]).map((type) => (
          <Button
            key={type}
            variant="ghost"
            size="sm"
            onClick={() => setMediaType(type)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              mediaType === type
                ? 'bg-primary-600 text-white'
                : 'bg-slate-100 dark:bg-slate-800 text-dim hover:bg-slate-200 dark:hover:bg-slate-700'
            }`}
          >
            {type === 'movies' ? 'Movies' : 'TV Shows'}
          </Button>
        ))}
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 border-b border-edge">
        {TABS.map((tab) => {
          const count = getTabCount(tab) ?? (tab.key === 'all' ? total : undefined)
          const isActive = activeTab === tab.key
          return (
            <Button
              key={tab.key}
              variant="ghost"
              size="sm"
              onClick={() => setActiveTab(tab.key)}
              className={`
                px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors
                ${isActive
                  ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                  : 'border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}
              `}
            >
              {tab.label}
              {count !== undefined && (
                <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full font-medium
                  ${isActive
                    ? 'bg-primary-100 text-primary-600 dark:bg-primary-900/50 dark:text-primary-400'
                    : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400'}`}>
                  {count}
                </span>
              )}
            </Button>
          )
        })}
      </div>

      {/* Table */}
      <div className="rounded-lg border border-edge overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-subtle">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-dim">Title</th>
              <th className="px-4 py-3 text-left font-medium text-dim w-16">Year</th>
              <th className="px-4 py-3 text-left font-medium text-dim w-36">Status</th>
              <th className="px-4 py-3 text-left font-medium text-dim">Error</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-rule/50">
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
                <td colSpan={4} className="px-4 py-12 text-center text-hint">
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
                  <td className="px-4 py-3 font-medium text-body">
                    {item.title}
                  </td>
                  <td className="px-4 py-3 text-hint">
                    {item.year ?? '—'}
                  </td>
                  <td className="px-4 py-3">
                    <EnrichmentBadge status={item.enrichment_status as EnrichmentStatus} />
                  </td>
                  <td className="px-4 py-3 text-hint text-xs truncate max-w-xs">
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
        <div className="flex items-center justify-between text-sm text-hint">
          <span>{total} total</span>
          <Pagination currentPage={page} totalPages={totalPages} onPageChange={goToPage} />
        </div>
      )}
    </div>
  )
}
