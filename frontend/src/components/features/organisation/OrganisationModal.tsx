import React, { useEffect, useState } from 'react'
import {
  organisationService,
  type ApplyResult,
  type OrganisationPreset,
  type OrganisationPreview,
  type RenameProposal,
} from '@/services/organisationService'

interface OrganisationModalProps {
  isOpen: boolean
  preset: OrganisationPreset
  onClose: () => void
}

type Tab = 'movies' | 'episodes'

export const OrganisationModal: React.FC<OrganisationModalProps> = ({ isOpen, preset, onClose }) => {
  const [preview, setPreview] = useState<OrganisationPreview | null>(null)
  const [loading, setLoading] = useState(false)
  const [applying, setApplying] = useState(false)
  const [result, setResult] = useState<ApplyResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [activeTab, setActiveTab] = useState<Tab>('movies')

  useEffect(() => {
    if (!isOpen) return
    setPreview(null)
    setResult(null)
    setError(null)
    setLoading(true)
    organisationService.getPreview(preset)
      .then((data) => {
        setPreview(data)
        const allKeys = new Set<string>([
          ...data.movies.map((m) => `movie-${m.file_id}`),
          ...data.episodes.map((e) => `episode-${e.file_id}`),
        ])
        setSelected(allKeys)
        setActiveTab(data.movies.length > 0 ? 'movies' : 'episodes')
      })
      .catch(() => {
        setError('Failed to load preview. Please try again.')
      })
      .finally(() => setLoading(false))
  }, [isOpen, preset])

  useEffect(() => {
    if (!isOpen) return
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEsc)
    return () => document.removeEventListener('keydown', handleEsc)
  }, [isOpen, onClose])

  const toggleItem = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const toggleAll = (items: RenameProposal[], type: 'movie' | 'episode') => {
    const keys = items.map((i) => `${type}-${i.file_id}`)
    setSelected((prev) => {
      const allSelected = keys.every((k) => prev.has(k))
      const next = new Set(prev)
      if (allSelected) keys.forEach((k) => next.delete(k))
      else keys.forEach((k) => next.add(k))
      return next
    })
  }

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
      setPreview((prev) => prev ? {
        movies: prev.movies.filter((m) => !snapshot.has(`movie-${m.file_id}`)),
        episodes: prev.episodes.filter((e) => !snapshot.has(`episode-${e.file_id}`)),
      } : null)
      setSelected(new Set())
    } catch {
      setResult({ success: 0, failed: items.length, errors: ['Request failed'] })
    } finally {
      setApplying(false)
    }
  }

  const selectedCount = selected.size

  const maybeShorten = (path: string) => {
    const parts = path.split('/')
    if (parts.length <= 3) return path
    return `…/${parts.slice(-3).join('/')}`
  }

  if (!isOpen) return null

  const movies = preview?.movies ?? []
  const episodes = preview?.episodes ?? []

  const renderTableBody = () => {
    if (!loading && !preview && error) {
      return (
        <p className="text-center py-12 text-red-500 dark:text-red-400 text-sm">
          {error}
        </p>
      )
    }

    const items = activeTab === 'movies' ? movies : episodes
    const type = activeTab === 'movies' ? 'movie' : 'episode'
    if (items.length === 0) {
      return (
        <p className="text-center py-12 text-slate-400 dark:text-slate-500 text-sm">
          All {activeTab} already match the {preset} format.
        </p>
      )
    }
    return (
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left text-slate-400 dark:text-slate-500">
            <th className="pb-2 pr-3 w-8">
              <input
                type="checkbox"
                checked={items.every((i) => selected.has(`${type}-${i.file_id}`))}
                onChange={() => toggleAll(items, type)}
                className="w-3.5 h-3.5 text-indigo-600 rounded"
              />
            </th>
            <th className="pb-2 pr-4">Current path</th>
            <th className="pb-2">Proposed path</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50">
          {items.map((item) => {
            const key = `${type}-${item.file_id}`
            return (
              <tr key={key} className="hover:bg-slate-50 dark:hover:bg-slate-700/30">
                <td className="py-2 pr-3">
                  <input
                    type="checkbox"
                    checked={selected.has(key)}
                    onChange={() => toggleItem(key)}
                    className="w-3.5 h-3.5 text-indigo-600 rounded"
                  />
                </td>
                <td className="py-2 pr-4 font-mono text-slate-500 dark:text-slate-400">
                  {maybeShorten(item.current_path)}
                </td>
                <td className="py-2 font-mono text-slate-800 dark:text-slate-200">
                  {maybeShorten(item.target_path)}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    )
  }

  return (
    <div
      className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="File Organisation Preview"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Preview & Apply Changes</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5 capitalize">{preset} format</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-200 dark:border-slate-700 px-6">
          {(['movies', 'episodes'] as Tab[]).map((tab) => {
            const count = tab === 'movies' ? movies.length : episodes.length
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-3 px-4 text-sm font-medium border-b-2 -mb-px transition capitalize ${
                  activeTab === tab
                    ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                    : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
              >
                {tab} <span className="ml-1 text-xs text-slate-400">({count})</span>
              </button>
            )
          })}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : renderTableBody()}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between gap-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">
            {selectedCount > 0 ? `${selectedCount} file${selectedCount !== 1 ? 's' : ''} selected` : 'No files selected'}
            {result && (
              <span className="ml-3">
                {result.success > 0 && <span className="text-green-600 dark:text-green-400">✓ {result.success} renamed</span>}
                {result.failed > 0 && <span className="ml-2 text-red-500 dark:text-red-400">✗ {result.failed} failed</span>}
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition"
            >
              Close
            </button>
            <button
              onClick={handleApply}
              disabled={applying || selectedCount === 0}
              className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {applying ? 'Applying…' : `Apply ${selectedCount > 0 ? selectedCount : ''} change${selectedCount !== 1 ? 's' : ''}`}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
