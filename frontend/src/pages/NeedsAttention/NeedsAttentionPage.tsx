import React, { useState, useEffect, useCallback } from 'react'
import { EnrichmentBadge, type EnrichmentStatus } from '@/components/features/media/EnrichmentBadge/EnrichmentBadge'
import { enrichmentService } from '@/services/enrichmentService'
import type { PendingEnrichmentItem, PendingEnrichmentResponse } from '@/services/enrichmentService'

const MANUAL_NEEDED_STATUSES = ['not_found']
const FAILED_STATUSES = ['external_failed']
const PENDING_STATUSES = ['local_only', 'pending_local', 'pending_external']

export const NeedsAttentionPage: React.FC = () => {
  const [data, setData] = useState<PendingEnrichmentResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [externalIdInputs, setExternalIdInputs] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState<Record<string, boolean>>({})

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      const result = await enrichmentService.getPending()
      setData(result)
    } catch {
      setError('Failed to load pending enrichment data.')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const getInputKey = (type: 'movie' | 'tv_show', id: number) => `${type}-${id}`

  const handleExternalIdChange = (type: 'movie' | 'tv_show', id: number, value: string) => {
    setExternalIdInputs((prev) => ({ ...prev, [getInputKey(type, id)]: value }))
  }

  const handleSaveAndEnrich = async (type: 'movie' | 'tv_show', item: PendingEnrichmentItem) => {
    const key = getInputKey(type, item.id)
    const externalId = externalIdInputs[key] || item.detected_external_id || ''
    if (!externalId.trim()) return

    setSubmitting((prev) => ({ ...prev, [key]: true }))
    try {
      if (type === 'movie') {
        await enrichmentService.setMovieExternalId(item.id, externalId.trim())
        await enrichmentService.triggerMovieEnrich(item.id)
      } else {
        await enrichmentService.setTvShowExternalId(item.id, externalId.trim())
        await enrichmentService.triggerTvShowEnrich(item.id)
      }
      await fetchData()
    } catch {
      // silently fail — user can retry
    } finally {
      setSubmitting((prev) => ({ ...prev, [key]: false }))
    }
  }

  const handleRetry = async (type: 'movie' | 'tv_show', item: PendingEnrichmentItem) => {
    const key = getInputKey(type, item.id)
    setSubmitting((prev) => ({ ...prev, [key]: true }))
    try {
      if (type === 'movie') {
        await enrichmentService.triggerMovieEnrich(item.id)
      } else {
        await enrichmentService.triggerTvShowEnrich(item.id)
      }
      await fetchData()
    } catch {
      // silently fail
    } finally {
      setSubmitting((prev) => ({ ...prev, [key]: false }))
    }
  }

  const handleRetryAll = async (items: Array<{ type: 'movie' | 'tv_show'; item: PendingEnrichmentItem }>) => {
    await Promise.allSettled(
      items.map(({ type, item }) => {
        if (type === 'movie') return enrichmentService.triggerMovieEnrich(item.id)
        return enrichmentService.triggerTvShowEnrich(item.id)
      })
    )
    await fetchData()
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="w-8 h-8 border-4 border-edge border-t-primary-500 rounded-full animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-body">Needs Attention</h1>
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-700 dark:text-red-400">{error}</p>
          <button
            onClick={fetchData}
            className="mt-2 text-sm text-red-600 dark:text-red-400 underline hover:no-underline"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }

  if (!data || data.total === 0) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold text-body">Needs Attention</h1>
        <div className="flex items-center gap-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
          <span className="text-green-600 dark:text-green-400 text-xl font-semibold">
            All media is fully enriched ✓
          </span>
        </div>
      </div>
    )
  }

  const allMovies = data.movies
  const allTvShows = data.tv_shows

  const manualNeededMovies = allMovies.filter((m) => MANUAL_NEEDED_STATUSES.includes(m.enrichment_status))
  const manualNeededShows = allTvShows.filter((s) => MANUAL_NEEDED_STATUSES.includes(s.enrichment_status))

  const failedMovies = allMovies.filter((m) => FAILED_STATUSES.includes(m.enrichment_status))
  const failedShows = allTvShows.filter((s) => FAILED_STATUSES.includes(s.enrichment_status))

  const pendingMovies = allMovies.filter((m) => PENDING_STATUSES.includes(m.enrichment_status))
  const pendingShows = allTvShows.filter((s) => PENDING_STATUSES.includes(s.enrichment_status))

  const failedItems = [
    ...failedMovies.map((item) => ({ type: 'movie' as const, item })),
    ...failedShows.map((item) => ({ type: 'tv_show' as const, item })),
  ]

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-body mb-2">Needs Attention</h1>
        <p className="text-dim">
          {data.total} item{data.total !== 1 ? 's' : ''} require attention
        </p>
      </div>

      {/* Section 1: Manual needed (not_found) */}
      {(manualNeededMovies.length > 0 || manualNeededShows.length > 0) && (
        <section>
          <h2 className="text-xl font-semibold text-body mb-4">
            Manual needed
          </h2>
          <div className="space-y-3">
            {[
              ...manualNeededMovies.map((item) => ({ type: 'movie' as const, item })),
              ...manualNeededShows.map((item) => ({ type: 'tv_show' as const, item })),
            ].map(({ type, item }) => {
              const key = getInputKey(type, item.id)
              const inputValue = externalIdInputs[key] ?? item.detected_external_id ?? ''
              const isSubmitting = submitting[key] ?? false

              return (
                <div
                  key={key}
                  className="bg-card border border-edge rounded-lg p-4"
                >
                  <div className="flex items-start justify-between gap-4 flex-wrap">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-body">
                          {item.title}
                        </span>
                        {item.year && (
                          <span className="text-sm text-hint">
                            ({item.year})
                          </span>
                        )}
                        <EnrichmentBadge status="not_found" />
                        <span className="text-xs text-hint capitalize">
                          {type === 'tv_show' ? 'TV Show' : 'Movie'}
                        </span>
                      </div>
                      {item.enrichment_error && (
                        <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                          {item.enrichment_error}
                        </p>
                      )}
                      {item.detected_external_id && (
                        <p className="mt-1 text-xs text-hint">
                          Detected from filename:{' '}
                          <span className="font-mono font-medium text-dim">
                            {item.detected_external_id}
                          </span>
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="mt-3 flex items-center gap-2">
                    <input
                      type="text"
                      value={inputValue}
                      onChange={(e) => handleExternalIdChange(type, item.id, e.target.value)}
                      placeholder={type === 'movie' ? 'Enter TMDB ID (e.g. 278)' : 'Enter TMDB ID (e.g. 1396)'}
                      className="flex-1 px-3 py-1.5 text-sm border border-edge rounded-lg bg-card text-body focus:outline-none focus:ring-2 focus:ring-primary-500"
                    />
                    <button
                      onClick={() => handleSaveAndEnrich(type, item)}
                      disabled={isSubmitting || !inputValue.trim()}
                      className="px-3 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition whitespace-nowrap"
                    >
                      {isSubmitting ? 'Saving...' : 'Save & Enrich'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* Section 2: Failed (external_failed) */}
      {failedItems.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-body">Failed</h2>
            <button
              onClick={() => handleRetryAll(failedItems)}
              className="px-4 py-1.5 text-sm bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition"
            >
              Retry all failed
            </button>
          </div>
          <div className="space-y-3">
            {failedItems.map(({ type, item }) => {
              const key = getInputKey(type, item.id)
              const isSubmitting = submitting[key] ?? false

              return (
                <div
                  key={key}
                  className="bg-card border border-edge rounded-lg p-4 flex items-start justify-between gap-4"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-body">
                        {item.title}
                      </span>
                      {item.year && (
                        <span className="text-sm text-hint">
                          ({item.year})
                        </span>
                      )}
                      <EnrichmentBadge status="local_only" />
                      <span className="text-xs text-hint capitalize">
                        {type === 'tv_show' ? 'TV Show' : 'Movie'}
                      </span>
                    </div>
                    {item.enrichment_error && (
                      <p className="mt-1 text-sm text-amber-600 dark:text-amber-400">
                        {item.enrichment_error}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => handleRetry(type, item)}
                    disabled={isSubmitting}
                    className="px-3 py-1.5 text-sm bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-700 rounded-lg hover:bg-amber-200 dark:hover:bg-amber-900/50 disabled:opacity-50 disabled:cursor-not-allowed transition whitespace-nowrap"
                  >
                    {isSubmitting ? 'Retrying...' : 'Retry'}
                  </button>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* Section 3: Pending (local_only / pending_local / pending_external) */}
      {(pendingMovies.length > 0 || pendingShows.length > 0) && (
        <section>
          <h2 className="text-xl font-semibold text-body mb-4">
            Pending enrichment
          </h2>
          <p className="text-sm text-hint mb-3">
            These items are queued for automatic enrichment — no action needed.
          </p>
          <div className="space-y-2">
            {[
              ...pendingMovies.map((item) => ({ type: 'movie' as const, item })),
              ...pendingShows.map((item) => ({ type: 'tv_show' as const, item })),
            ].map(({ type, item }) => (
              <div
                key={getInputKey(type, item.id)}
                className="bg-card border border-edge rounded-lg px-4 py-3 flex items-center gap-3"
              >
                <EnrichmentBadge status={item.enrichment_status as EnrichmentStatus} />
                <span className="font-medium text-body">{item.title}</span>
                {item.year && (
                  <span className="text-sm text-hint">({item.year})</span>
                )}
                <span className="ml-auto text-xs text-hint capitalize">
                  {item.enrichment_status.replace(/_/g, ' ')}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

export default NeedsAttentionPage
