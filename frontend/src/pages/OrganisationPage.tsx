import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { FaChevronDown, FaChevronRight, FaSync } from 'react-icons/fa'
import {
  organisationService,
  type ApplyResult,
  type OrganisationPreset,
  type OrganisationPreview,
  type RenameProposal,
} from '@/services/organisationService'

// ---------------------------------------------------------------------------
// Grouping helpers
// ---------------------------------------------------------------------------

interface SeasonGroup {
  season_number: number
  episodes: RenameProposal[]
}

interface ShowGroup {
  show_title: string
  seasons: SeasonGroup[]
}

function groupEpisodes(episodes: RenameProposal[]): ShowGroup[] {
  const showMap = new Map<string, Map<number, RenameProposal[]>>()
  for (const ep of episodes) {
    const show = ep.show_title ?? 'Unknown Show'
    const season = ep.season_number ?? 0
    if (!showMap.has(show)) showMap.set(show, new Map())
    const seasonMap = showMap.get(show)!
    if (!seasonMap.has(season)) seasonMap.set(season, [])
    seasonMap.get(season)!.push(ep)
  }
  return Array.from(showMap.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([show_title, seasonMap]) => ({
      show_title,
      seasons: Array.from(seasonMap.entries())
        .sort(([a], [b]) => a - b)
        .map(([season_number, eps]) => ({ season_number, episodes: eps })),
    }))
}

// ---------------------------------------------------------------------------
// Indeterminate checkbox
// ---------------------------------------------------------------------------

interface IndeterminateCheckboxProps {
  keys: string[]
  selected: Set<string>
  onChange: () => void
  onClick?: (e: React.MouseEvent<HTMLInputElement>) => void
  className?: string
}

function IndeterminateCheckbox({ keys, selected, onChange, onClick, className }: IndeterminateCheckboxProps) {
  const count = keys.filter((k) => selected.has(k)).length
  const checked = keys.length > 0 && count === keys.length
  const indeterminate = count > 0 && count < keys.length
  const ref = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (ref.current) ref.current.indeterminate = indeterminate
  }, [indeterminate])

  return (
    <input
      ref={ref}
      type="checkbox"
      checked={checked}
      onChange={onChange}
      onClick={onClick}
      className={className ?? 'w-3.5 h-3.5 text-indigo-600 rounded'}
    />
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

function maybeShorten(path: string): string {
  const parts = path.split('/')
  return parts.length <= 3 ? path : `…/${parts.slice(-3).join('/')}`
}

export function OrganisationPage() {
  const [preset, setPreset] = useState<OrganisationPreset>('plex')
  const [preview, setPreview] = useState<OrganisationPreview | null>(null)
  const [loading, setLoading] = useState(false)
  const [applying, setApplying] = useState(false)
  const [result, setResult] = useState<ApplyResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())

  // Collapse state — item in set = collapsed
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set())
  const [collapsedShows, setCollapsedShows] = useState<Set<string>>(new Set())
  const [collapsedSeasons, setCollapsedSeasons] = useState<Set<string>>(new Set())

  const showGroups = useMemo(
    () => groupEpisodes(preview?.episodes ?? []),
    [preview?.episodes],
  )

  const loadPreview = useCallback((p: OrganisationPreset) => {
    setLoading(true)
    setError(null)
    setResult(null)
    organisationService
      .getPreview(p)
      .then((data) => {
        setPreview(data)
        setSelected(
          new Set([
            ...data.movies.map((m) => `movie-${m.file_id}`),
            ...data.episodes.map((e) => `episode-${e.file_id}`),
          ]),
        )
      })
      .catch(() => setError('Failed to load preview. Please try again.'))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    organisationService
      .getSettings()
      .then(({ preset: p }) => {
        setPreset(p)
        loadPreview(p)
      })
      .catch(() => loadPreview('plex'))
  }, [loadPreview])

  // ---- Collapse helpers ----

  const toggleSection = (key: string) =>
    setCollapsedSections((prev) => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })

  const toggleShow = (key: string) =>
    setCollapsedShows((prev) => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })

  const toggleSeason = (key: string) =>
    setCollapsedSeasons((prev) => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })

  const collapseAllShows = () =>
    setCollapsedShows(new Set(showGroups.map((g) => g.show_title)))

  const expandAllShows = () => {
    setCollapsedShows(new Set())
    setCollapsedSeasons(new Set())
  }

  // ---- Selection helpers ----

  const toggleItem = (key: string) =>
    setSelected((prev) => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })

  const toggleKeys = (keys: string[]) =>
    setSelected((prev) => {
      const allSelected = keys.every((k) => prev.has(k))
      const next = new Set(prev)
      if (allSelected) keys.forEach((k) => next.delete(k))
      else keys.forEach((k) => next.add(k))
      return next
    })

  const movieKeys = (preview?.movies ?? []).map((m) => `movie-${m.file_id}`)

  const showKeys = (group: ShowGroup) =>
    group.seasons.flatMap((s) => s.episodes.map((e) => `episode-${e.file_id}`))

  const seasonKeys = (season: SeasonGroup) =>
    season.episodes.map((e) => `episode-${e.file_id}`)

  // ---- Apply ----

  const handleApply = async () => {
    if (!preview) return
    const snapshot = new Set(selected)
    setApplying(true)
    setResult(null)

    const items: RenameProposal[] = [
      ...preview.movies
        .filter((m) => snapshot.has(`movie-${m.file_id}`))
        .map((m) => ({ ...m, file_type: 'movie' as const })),
      ...preview.episodes
        .filter((e) => snapshot.has(`episode-${e.file_id}`))
        .map((e) => ({ ...e, file_type: 'episode' as const })),
    ]

    try {
      const res = await organisationService.applyRenames(items)
      setResult(res)
      setPreview((prev) =>
        prev
          ? {
              movies: prev.movies.filter((m) => !snapshot.has(`movie-${m.file_id}`)),
              episodes: prev.episodes.filter((e) => !snapshot.has(`episode-${e.file_id}`)),
            }
          : null,
      )
      setSelected(new Set())
    } catch {
      setResult({ success: 0, failed: items.length, errors: ['Request failed'] })
    } finally {
      setApplying(false)
    }
  }

  const selectedCount = selected.size
  const movies = preview?.movies ?? []
  const episodes = preview?.episodes ?? []

  return (
    <div className="space-y-6 pb-20">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">File Organisation</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Format:{' '}
            <span className="font-medium capitalize text-gray-700 dark:text-gray-200">{preset}</span>
            {' · '}
            <Link
              to="/settings"
              className="text-indigo-600 dark:text-indigo-400 hover:underline text-xs"
            >
              change in Settings
            </Link>
          </p>
        </div>
        <button
          onClick={() => loadPreview(preset)}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition disabled:opacity-50"
        >
          <FaSync className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats bar */}
      {preview && (
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/50 rounded-lg px-4 py-2.5">
          <span>
            {movies.length} movie{movies.length !== 1 ? 's' : ''} need renaming
          </span>
          <span className="text-gray-300 dark:text-gray-600">·</span>
          <span>
            {episodes.length} episode{episodes.length !== 1 ? 's' : ''} need renaming
          </span>
          {showGroups.length > 0 && (
            <>
              <span className="text-gray-300 dark:text-gray-600">·</span>
              <span>
                across {showGroups.length} show{showGroups.length !== 1 ? 's' : ''}
              </span>
            </>
          )}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-16">
          <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <p className="text-center py-8 text-red-500 dark:text-red-400 text-sm">{error}</p>
      )}

      {/* Content */}
      {!loading && preview && (
        <>
          {/* ---- Movies section ---- */}
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
            {/* Section header */}
            <div className="flex items-center justify-between">
              <button
                className="flex items-center gap-3 flex-1 px-5 py-3.5 text-left hover:bg-slate-50 dark:hover:bg-slate-700/30 transition"
                onClick={() => toggleSection('movies')}
              >
                {collapsedSections.has('movies') ? (
                  <FaChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                ) : (
                  <FaChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                )}
                <span className="font-semibold text-slate-800 dark:text-slate-100">
                  Movies
                  <span className="ml-2 text-sm font-normal text-slate-400">({movies.length})</span>
                </span>
              </button>
              {movies.length > 0 && !collapsedSections.has('movies') && (
                <button
                  className="px-5 text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
                  onClick={() => toggleKeys(movieKeys)}
                >
                  select all
                </button>
              )}
            </div>

            {/* Movies body */}
            {!collapsedSections.has('movies') && (
              movies.length === 0 ? (
                <p className="px-5 py-6 text-sm text-slate-400 dark:text-slate-500 border-t border-slate-100 dark:border-slate-700">
                  All movies already match the {preset} format.
                </p>
              ) : (
                <table className="w-full text-xs border-t border-slate-200 dark:border-slate-700">
                  <thead>
                    <tr className="bg-slate-50 dark:bg-slate-700/30 text-slate-400 dark:text-slate-500 text-left">
                      <th className="px-5 py-2 w-10">
                        <IndeterminateCheckbox
                          keys={movieKeys}
                          selected={selected}
                          onChange={() => toggleKeys(movieKeys)}
                        />
                      </th>
                      <th className="py-2 pr-4">Current path</th>
                      <th className="py-2 pr-5">Proposed path</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
                    {movies.map((m) => {
                      const key = `movie-${m.file_id}`
                      return (
                        <tr key={key} className="hover:bg-slate-50 dark:hover:bg-slate-700/20">
                          <td className="px-5 py-2">
                            <input
                              type="checkbox"
                              checked={selected.has(key)}
                              onChange={() => toggleItem(key)}
                              className="w-3.5 h-3.5 text-indigo-600 rounded"
                            />
                          </td>
                          <td className="py-2 pr-4 font-mono text-slate-500 dark:text-slate-400">
                            {maybeShorten(m.current_path)}
                          </td>
                          <td className="py-2 pr-5 font-mono text-slate-800 dark:text-slate-200">
                            {maybeShorten(m.target_path)}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )
            )}
          </div>

          {/* ---- TV Shows section ---- */}
          <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden">
            {/* Section header */}
            <div className="flex items-center justify-between px-5 py-3.5 border-b border-slate-200 dark:border-slate-700">
              <button
                className="flex items-center gap-3 flex-1 text-left hover:text-slate-600 dark:hover:text-slate-300 transition"
                onClick={() => toggleSection('tv')}
              >
                {collapsedSections.has('tv') ? (
                  <FaChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                ) : (
                  <FaChevronDown className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                )}
                <span className="font-semibold text-slate-800 dark:text-slate-100">
                  TV Shows
                  <span className="ml-2 text-sm font-normal text-slate-400">
                    ({episodes.length} episode{episodes.length !== 1 ? 's' : ''},{' '}
                    {showGroups.length} show{showGroups.length !== 1 ? 's' : ''})
                  </span>
                </span>
              </button>
              {showGroups.length > 0 && !collapsedSections.has('tv') && (
                <div className="flex gap-3 text-xs text-indigo-600 dark:text-indigo-400 shrink-0">
                  <button onClick={expandAllShows} className="hover:underline">
                    expand all
                  </button>
                  <button onClick={collapseAllShows} className="hover:underline">
                    collapse all
                  </button>
                </div>
              )}
            </div>

            {!collapsedSections.has('tv') && (
              showGroups.length === 0 ? (
                <p className="px-5 py-6 text-sm text-slate-400 dark:text-slate-500">
                  All episodes already match the {preset} format.
                </p>
              ) : (
                showGroups.map((group) => {
                  const isShowCollapsed = collapsedShows.has(group.show_title)
                  const allShowKeys = showKeys(group)

                  return (
                    <div
                      key={group.show_title}
                      className="border-b border-slate-100 dark:border-slate-700/50 last:border-b-0"
                    >
                      {/* Show header */}
                      <div className="flex items-center justify-between px-5 py-2.5 bg-slate-50/50 dark:bg-slate-700/20">
                        <button
                          className="flex items-center gap-2 flex-1 text-left min-w-0"
                          onClick={() => toggleShow(group.show_title)}
                        >
                          {isShowCollapsed ? (
                            <FaChevronRight className="w-3 h-3 text-slate-400 shrink-0" />
                          ) : (
                            <FaChevronDown className="w-3 h-3 text-slate-400 shrink-0" />
                          )}
                          <IndeterminateCheckbox
                            keys={allShowKeys}
                            selected={selected}
                            onChange={() => toggleKeys(allShowKeys)}
                            onClick={(e) => e.stopPropagation()}
                          />
                          <span className="text-sm font-medium text-slate-700 dark:text-slate-200 ml-1 truncate">
                            {group.show_title}
                            <span className="ml-2 text-xs font-normal text-slate-400">
                              ({allShowKeys.length})
                            </span>
                          </span>
                        </button>
                        <button
                          className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline shrink-0 ml-3"
                          onClick={() => toggleKeys(allShowKeys)}
                        >
                          select all
                        </button>
                      </div>

                      {/* Seasons */}
                      {!isShowCollapsed &&
                        group.seasons.map((season) => {
                          const seasonKey = `${group.show_title}::S${season.season_number}`
                          const isSeasonCollapsed = collapsedSeasons.has(seasonKey)
                          const sKeys = seasonKeys(season)

                          return (
                            <div key={seasonKey}>
                              {/* Season header */}
                              <div className="flex items-center justify-between pl-10 pr-5 py-2 border-t border-slate-100 dark:border-slate-700/30">
                                <button
                                  className="flex items-center gap-2 flex-1 text-left min-w-0"
                                  onClick={() => toggleSeason(seasonKey)}
                                >
                                  {isSeasonCollapsed ? (
                                    <FaChevronRight className="w-3 h-3 text-slate-400 shrink-0" />
                                  ) : (
                                    <FaChevronDown className="w-3 h-3 text-slate-400 shrink-0" />
                                  )}
                                  <IndeterminateCheckbox
                                    keys={sKeys}
                                    selected={selected}
                                    onChange={() => toggleKeys(sKeys)}
                                    onClick={(e) => e.stopPropagation()}
                                  />
                                  <span className="text-xs font-medium text-slate-600 dark:text-slate-300 ml-1">
                                    Season {String(season.season_number).padStart(2, '0')}
                                    <span className="ml-2 font-normal text-slate-400">
                                      ({season.episodes.length})
                                    </span>
                                  </span>
                                </button>
                                <button
                                  className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline shrink-0 ml-3"
                                  onClick={() => toggleKeys(sKeys)}
                                >
                                  select all
                                </button>
                              </div>

                              {/* Episode rows */}
                              {!isSeasonCollapsed && (
                                <table className="w-full text-xs">
                                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700/30">
                                    {season.episodes.map((ep) => {
                                      const key = `episode-${ep.file_id}`
                                      return (
                                        <tr
                                          key={key}
                                          className="hover:bg-slate-50 dark:hover:bg-slate-700/20"
                                        >
                                          <td className="pl-16 pr-3 py-1.5 w-16">
                                            <input
                                              type="checkbox"
                                              checked={selected.has(key)}
                                              onChange={() => toggleItem(key)}
                                              className="w-3.5 h-3.5 text-indigo-600 rounded"
                                            />
                                          </td>
                                          <td className="py-1.5 pr-4 font-mono text-slate-500 dark:text-slate-400">
                                            {maybeShorten(ep.current_path)}
                                          </td>
                                          <td className="py-1.5 pr-5 font-mono text-slate-700 dark:text-slate-300">
                                            {maybeShorten(ep.target_path)}
                                          </td>
                                        </tr>
                                      )
                                    })}
                                  </tbody>
                                </table>
                              )}
                            </div>
                          )
                        })}
                    </div>
                  )
                })
              )
            )}
          </div>
        </>
      )}

      {/* Sticky footer */}
      <div className="sticky bottom-0 z-10 -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 py-3 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between gap-4">
        <div className="text-sm text-slate-500 dark:text-slate-400">
          {selectedCount > 0
            ? `${selectedCount} file${selectedCount !== 1 ? 's' : ''} selected`
            : 'No files selected'}
          {result && (
            <span className="ml-4">
              {result.success > 0 && (
                <span className="text-green-600 dark:text-green-400">✓ {result.success} renamed</span>
              )}
              {result.failed > 0 && (
                <span className="ml-2 text-red-500 dark:text-red-400">✗ {result.failed} failed</span>
              )}
            </span>
          )}
        </div>
        <button
          onClick={handleApply}
          disabled={applying || selectedCount === 0}
          className="px-5 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition font-medium"
        >
          {applying
            ? 'Applying…'
            : `Apply ${selectedCount > 0 ? selectedCount : ''} change${selectedCount !== 1 ? 's' : ''}`}
        </button>
      </div>
    </div>
  )
}
