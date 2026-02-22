import React, { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Badge, EmptyState } from '@/components/common'
import { tvShowService } from '@/services/tvShowService'
import { enrichmentService } from '@/services/enrichmentService'
import { EnrichmentBadge } from '@/components/features/media/EnrichmentBadge/EnrichmentBadge'
import { Button } from '@/components/common/Button'
import type { TVShow, Season, Episode } from '@/types'

const TVShowDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [show, setShow] = useState<TVShow | null>(null)
  const [seasons, setSeasons] = useState<Season[]>([])
  const [episodeMap, setEpisodeMap] = useState<Record<number, Episode[]>>({})
  const [loadingSeasons, setLoadingSeasons] = useState<Set<number>>(new Set())
  const [expandedSeasonId, setExpandedSeasonId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [externalIdInput, setExternalIdInput] = useState('')
  const [enriching, setEnriching] = useState(false)

  useEffect(() => {
    if (!id) return
    setIsLoading(true)
    setError(null)

    Promise.all([
      tvShowService.getTVShowDetails(id),
      tvShowService.getSeasons(id),
    ])
      .then(([showData, seasonsData]) => {
        setShow(showData as unknown as TVShow)
        setSeasons(seasonsData?.items ?? [])
      })
      .catch(() => setError('Failed to load TV show details.'))
      .finally(() => setIsLoading(false))
  }, [id])

  const handleToggleSeason = useCallback(async (season: Season) => {
    if (expandedSeasonId === season.id) {
      setExpandedSeasonId(null)
      return
    }
    setExpandedSeasonId(season.id)

    if (episodeMap[season.id]) return // already loaded

    setLoadingSeasons((prev) => new Set(prev).add(season.id))
    try {
      const data = await tvShowService.getEpisodes(id!, season.id)
      setEpisodeMap((prev) => ({ ...prev, [season.id]: data?.items ?? [] }))
    } catch {
      setEpisodeMap((prev) => ({ ...prev, [season.id]: [] }))
    } finally {
      setLoadingSeasons((prev) => {
        const next = new Set(prev)
        next.delete(season.id)
        return next
      })
    }
  }, [expandedSeasonId, episodeMap, id])

  const getStatusVariant = (status?: string) => {
    if (status === 'continuing') return 'success'
    if (status === 'ended') return 'secondary'
    return 'secondary'
  }

  const formatAirDate = (date?: string | null) => {
    if (!date) return null
    try {
      return new Date(date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
    } catch {
      return date
    }
  }

  const parseGenres = (genres?: string | string[] | null): string[] => {
    if (!genres) return []
    if (Array.isArray(genres)) return genres
    try { return JSON.parse(genres) } catch { return [genres] }
  }

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-6 w-32 bg-slate-200 dark:bg-slate-700 rounded" />
        <div className="flex gap-6">
          <div className="w-40 h-56 bg-slate-200 dark:bg-slate-700 rounded-lg flex-shrink-0" />
          <div className="flex-1 space-y-3">
            <div className="h-8 w-64 bg-slate-200 dark:bg-slate-700 rounded" />
            <div className="h-4 w-40 bg-slate-200 dark:bg-slate-700 rounded" />
            <div className="h-4 w-full bg-slate-200 dark:bg-slate-700 rounded" />
            <div className="h-4 w-3/4 bg-slate-200 dark:bg-slate-700 rounded" />
          </div>
        </div>
      </div>
    )
  }

  if (error || !show) {
    return (
      <EmptyState
        variant="not-found"
        title="TV show not found"
        description={error ?? 'The TV show you\'re looking for doesn\'t exist.'}
        action={{ label: 'Back to TV Shows', onClick: () => navigate('/tv-shows') }}
      />
    )
  }

  const genres = parseGenres(show.genres ?? show.genre)

  return (
    <div className="space-y-8">
      {/* Back */}
      <button
        onClick={() => navigate('/tv-shows')}
        className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        Back to TV Shows
      </button>

      {/* Header */}
      <div className="flex gap-6">
        {/* Poster */}
        <div className="flex-shrink-0 w-36 sm:w-44">
          {show.poster_url ? (
            <img
              src={show.poster_url}
              alt={show.title}
              className="w-full rounded-lg shadow-md object-cover aspect-[2/3]"
            />
          ) : (
            <div className="w-full aspect-[2/3] rounded-lg bg-slate-200 dark:bg-slate-700 flex items-center justify-center">
              <svg className="w-10 h-10 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.894L15 14M3 8a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
              </svg>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0 space-y-3">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{show.title}</h1>

          <div className="flex flex-wrap items-center gap-2">
            {show.status && (
              <Badge variant={getStatusVariant(show.status)}>
                {show.status.charAt(0).toUpperCase() + show.status.slice(1)}
              </Badge>
            )}
            {show.rating != null && (
              <span className="text-sm text-amber-500 font-medium">★ {show.rating.toFixed(1)}</span>
            )}
            {seasons.length > 0 && (
              <span className="text-sm text-slate-500 dark:text-slate-400">
                {seasons.length} {seasons.length === 1 ? 'season' : 'seasons'}
              </span>
            )}
          </div>

          {genres.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {genres.map((g) => (
                <Badge key={g} variant="secondary">{g}</Badge>
              ))}
            </div>
          )}

          {show.plot && (
            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed max-w-2xl">
              {show.plot}
            </p>
          )}
        </div>
      </div>

      {/* Seasons & Episodes */}
      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Seasons & Episodes</h2>

        {seasons.length === 0 ? (
          <div className="rounded-lg border border-slate-200 dark:border-slate-700 px-4 py-10 text-center text-slate-500 dark:text-slate-400 text-sm">
            No season data available yet.
          </div>
        ) : (
          <div className="rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden divide-y divide-slate-200 dark:divide-slate-700">
            {seasons
              .slice()
              .sort((a, b) => a.season_number - b.season_number)
              .map((season) => {
                const isExpanded = expandedSeasonId === season.id
                const isLoadingEpisodes = loadingSeasons.has(season.id)
                const episodes = episodeMap[season.id] ?? []

                return (
                  <div key={season.id}>
                    {/* Season row */}
                    <button
                      className="w-full flex items-center justify-between px-4 py-3 text-left
                        bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700/50
                        transition-colors focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
                      onClick={() => handleToggleSeason(season)}
                    >
                      <div className="flex items-center gap-3">
                        <span className="font-medium text-slate-900 dark:text-white">
                          Season {season.season_number}
                        </span>
                        {season.episode_count != null && (
                          <span className="text-xs text-slate-500 dark:text-slate-400">
                            {season.episode_count} {season.episode_count === 1 ? 'episode' : 'episodes'}
                          </span>
                        )}
                      </div>
                      <svg
                        className={`w-5 h-5 text-slate-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                        fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>

                    {/* Episode list */}
                    {isExpanded && (
                      <div className="bg-slate-50 dark:bg-slate-900/50">
                        {isLoadingEpisodes ? (
                          <div className="flex items-center justify-center py-8">
                            <div className="w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                          </div>
                        ) : episodes.length === 0 ? (
                          <p className="px-6 py-6 text-sm text-slate-500 dark:text-slate-400 text-center">
                            No episodes found for this season.
                          </p>
                        ) : (
                          <div className="divide-y divide-slate-200 dark:divide-slate-700/50">
                            {episodes
                              .slice()
                              .sort((a, b) => a.episode_number - b.episode_number)
                              .map((ep) => (
                                <div
                                  key={ep.id}
                                  className="flex items-start gap-4 px-6 py-3"
                                >
                                  {/* Episode number */}
                                  <span className="flex-shrink-0 w-8 text-sm font-mono text-slate-400 dark:text-slate-500 pt-0.5">
                                    {String(ep.episode_number).padStart(2, '0')}
                                  </span>

                                  {/* Title + plot */}
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-slate-900 dark:text-white">
                                      {ep.title ?? `Episode ${ep.episode_number}`}
                                    </p>
                                    {ep.plot && (
                                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">
                                        {ep.plot}
                                      </p>
                                    )}
                                  </div>

                                  {/* Meta */}
                                  <div className="flex-shrink-0 text-right space-y-0.5">
                                    {ep.air_date && (
                                      <p className="text-xs text-slate-400 dark:text-slate-500">
                                        {formatAirDate(ep.air_date)}
                                      </p>
                                    )}
                                    {ep.rating != null && (
                                      <p className="text-xs text-amber-500 font-medium">
                                        ★ {ep.rating.toFixed(1)}
                                      </p>
                                    )}
                                  </div>
                                </div>
                              ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
          </div>
        )}
      </section>

      {/* Enrichment */}
      <section className="rounded-lg border border-slate-200 dark:border-slate-700 p-4 space-y-3">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Enrichment Status</h3>
        <div className="flex items-center gap-2">
          <EnrichmentBadge status={(show as any).enrichment_status} />
          <span className="text-sm text-slate-500 dark:text-slate-400">
            {(show as any).enrichment_status ?? 'unknown'}
          </span>
        </div>
        {(show as any).enrichment_error && (
          <p className="text-xs text-red-500 dark:text-red-400">
            {(show as any).enrichment_error}
          </p>
        )}
        {(show as any).detected_external_id && (
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Detected from filename: <code className="font-mono">{(show as any).detected_external_id}</code>
          </p>
        )}
        <div className="flex gap-2 items-center">
          <input
            type="text"
            placeholder="TMDB ID (e.g. 1396)"
            value={externalIdInput}
            onChange={(e) => setExternalIdInput(e.target.value)}
            className="flex-1 min-w-0 text-sm px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <Button
            variant="primary"
            size="sm"
            disabled={enriching || !externalIdInput.trim()}
            onClick={async () => {
              if (!externalIdInput.trim() || !id) return
              setEnriching(true)
              try {
                await enrichmentService.setTvShowExternalId(Number(id), externalIdInput.trim())
                window.location.reload()
              } finally {
                setEnriching(false)
              }
            }}
          >
            {enriching ? 'Saving…' : 'Save & Enrich'}
          </Button>
          <Button
            variant="secondary"
            size="sm"
            disabled={enriching}
            onClick={async () => {
              if (!id) return
              setEnriching(true)
              try {
                await enrichmentService.triggerTvShowEnrich(Number(id))
                window.location.reload()
              } finally {
                setEnriching(false)
              }
            }}
          >
            {enriching ? '…' : 'Re-Enrich'}
          </Button>
        </div>
      </section>
    </div>
  )
}

export default TVShowDetailPage
