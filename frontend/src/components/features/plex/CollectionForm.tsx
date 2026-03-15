import React, { useState } from 'react'
import type { CollectionCreate, BuilderType } from '../../../services/plexCollectionService'

interface CollectionFormProps {
  onSubmit: (data: CollectionCreate) => void
  onCancel: () => void
}

const BUILDER_OPTIONS: { value: BuilderType; label: string }[] = [
  { value: 'tmdb_collection', label: 'TMDB Collection' },
  { value: 'static_items', label: 'Static Items' },
  { value: 'genre', label: 'Genre' },
  { value: 'decade', label: 'Decade' },
]

function parseBuilderConfig(raw: string): Record<string, unknown> | null {
  try {
    return JSON.parse(raw) as Record<string, unknown>
  } catch {
    return null
  }
}

export function CollectionForm({ onSubmit, onCancel }: CollectionFormProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [builderType, setBuilderType] = useState<BuilderType>('static_items')
  const [builderConfigRaw, setBuilderConfigRaw] = useState('{}')
  const [configError, setConfigError] = useState<string | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const config = parseBuilderConfig(builderConfigRaw)
    if (config === null) {
      setConfigError('Invalid JSON')
      return
    }
    setConfigError(null)
    onSubmit({ name, description: description || undefined, builder_type: builderType, builder_config: config })
  }

  const handleConfigChange = (value: string) => {
    setBuilderConfigRaw(value)
    if (configError && parseBuilderConfig(value) !== null) {
      setConfigError(null)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-xl bg-white dark:bg-slate-800 shadow-xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">New Collection</h2>
          <button
            onClick={onCancel}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
            aria-label="Close"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          <div>
            <label htmlFor="col-name" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Name <span className="text-red-500">*</span>
            </label>
            <input
              id="col-name"
              type="text"
              required
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="My Collection"
            />
          </div>

          <div>
            <label htmlFor="col-desc" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Description
            </label>
            <input
              id="col-desc"
              type="text"
              value={description}
              onChange={e => setDescription(e.target.value)}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Optional description"
            />
          </div>

          <div>
            <label htmlFor="col-builder-type" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Builder Type <span className="text-red-500">*</span>
            </label>
            <select
              id="col-builder-type"
              value={builderType}
              onChange={e => setBuilderType(e.target.value as BuilderType)}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {BUILDER_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="col-builder-config" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
              Builder Config (JSON)
            </label>
            <textarea
              id="col-builder-config"
              rows={4}
              value={builderConfigRaw}
              onChange={e => handleConfigChange(e.target.value)}
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-900 dark:text-white px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            />
            {configError && (
              <p className="mt-1 text-xs text-red-600 dark:text-red-400">{configError}</p>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 rounded-lg text-sm font-medium border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 rounded-lg text-sm font-medium bg-indigo-600 hover:bg-indigo-700 text-white transition-colors"
            >
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CollectionForm
