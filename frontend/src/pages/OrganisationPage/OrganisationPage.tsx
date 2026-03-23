import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { FaSync } from 'react-icons/fa'
import { Button } from '@/components/common'
import {
  organisationService,
  type ApplyResult,
  type OrganisationPreset,
  type OrganisationPreview,
  type RenameProposal,
} from '@/services/organisationService'
import { groupEpisodes } from './helpers'
import { MoviesSection } from './MoviesSection'
import { TVShowsSection } from './TVShowsSection'

export function OrganisationPage() {
  const [preset, setPreset] = useState<OrganisationPreset>('plex')
  const [preview, setPreview] = useState<OrganisationPreview | null>(null)
  const [loading, setLoading] = useState(false)
  const [applying, setApplying] = useState(false)
  const [result, setResult] = useState<ApplyResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())

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

  const toggleSection = (key: string) =>
    setCollapsedSections((prev) => {
      const next = new Set(prev)
      if (next.has(key)) { next.delete(key) } else { next.add(key) }
      return next
    })

  const toggleShow = (key: string) =>
    setCollapsedShows((prev) => {
      const next = new Set(prev)
      if (next.has(key)) { next.delete(key) } else { next.add(key) }
      return next
    })

  const toggleSeason = (key: string) =>
    setCollapsedSeasons((prev) => {
      const next = new Set(prev)
      if (next.has(key)) { next.delete(key) } else { next.add(key) }
      return next
    })

  const collapseAllShows = () =>
    setCollapsedShows(new Set(showGroups.map((g) => g.show_title)))

  const expandAllShows = () => {
    setCollapsedShows(new Set())
    setCollapsedSeasons(new Set())
  }

  const toggleItem = (key: string) =>
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(key)) { next.delete(key) } else { next.add(key) }
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
      if (res.failed === 0) {
        setPreview((prev) =>
          prev
            ? {
                movies: prev.movies.filter((m) => !snapshot.has(`movie-${m.file_id}`)),
                episodes: prev.episodes.filter((e) => !snapshot.has(`episode-${e.file_id}`)),
              }
            : null,
        )
        setSelected(new Set())
      }
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
          <h1 className="text-2xl font-bold text-body">File Organisation</h1>
          <p className="text-sm text-hint mt-1">
            Format:{' '}
            <span className="font-medium capitalize text-dim">{preset}</span>
            {' · '}
            <Link
              to="/settings"
              className="text-primary-600 dark:text-primary-400 hover:underline text-xs"
            >
              change in Settings
            </Link>
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => loadPreview(preset)}
          disabled={loading}
          leftIcon={<FaSync className={loading ? 'animate-spin' : ''} />}
        >
          Refresh
        </Button>
      </div>

      {/* Stats bar */}
      {preview && (
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm text-dim bg-subtle rounded-lg px-4 py-2.5">
          <span>
            {movies.length} movie{movies.length !== 1 ? 's' : ''} need renaming
          </span>
          <span className="text-hint">·</span>
          <span>
            {episodes.length} episode{episodes.length !== 1 ? 's' : ''} need renaming
          </span>
          {showGroups.length > 0 && (
            <>
              <span className="text-hint">·</span>
              <span>
                across {showGroups.length} show{showGroups.length !== 1 ? 's' : ''}
              </span>
            </>
          )}
        </div>
      )}

      {loading && (
        <div className="flex justify-center py-16">
          <div className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {!loading && error && (
        <p className="text-center py-8 text-red-500 dark:text-red-400 text-sm">{error}</p>
      )}

      {result && result.errors.length > 0 && (
        <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 p-4">
          <p className="text-sm font-medium text-red-700 dark:text-red-400 mb-2">
            {result.failed} file{result.failed !== 1 ? 's' : ''} could not be renamed:
          </p>
          <ul className="space-y-1">
            {result.errors.map((err, i) => (
              <li key={i} className="text-xs font-mono text-red-600 dark:text-red-300">
                {err}
              </li>
            ))}
          </ul>
        </div>
      )}

      {!loading && preview && (
        <>
          <MoviesSection
            movies={movies}
            preset={preset}
            collapsedSections={collapsedSections}
            selected={selected}
            onToggleSection={() => toggleSection('movies')}
            onToggleKeys={toggleKeys}
            onToggleItem={toggleItem}
          />
          <TVShowsSection
            showGroups={showGroups}
            episodes={episodes}
            preset={preset}
            selected={selected}
            collapseState={{ collapsedSections, collapsedShows, collapsedSeasons }}
            handlers={{
              onToggleSection: () => toggleSection('tv'),
              onExpandAll: expandAllShows,
              onCollapseAll: collapseAllShows,
              onToggleShow: toggleShow,
              onToggleSeason: toggleSeason,
              onToggleKeys: toggleKeys,
              onToggleItem: toggleItem,
            }}
          />
        </>
      )}

      {/* Sticky footer */}
      <div className="sticky bottom-0 z-10 -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 py-3 bg-page border-t border-edge flex items-center justify-between gap-4">
        <div className="text-sm text-hint">
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
        <Button
          variant="primary"
          onClick={handleApply}
          disabled={applying || selectedCount === 0}
          loading={applying}
        >
          {applying
            ? 'Applying…'
            : `Apply ${selectedCount > 0 ? selectedCount : ''} change${selectedCount !== 1 ? 's' : ''}`}
        </Button>
      </div>
    </div>
  )
}
