import React, { useState } from 'react'
import { FaTimes } from 'react-icons/fa'
import type { CollectionCreate, BuilderType } from '../../../services/plexCollectionService'
import { TextInput } from '@/components/common/TextInput'
import { Select } from '@/components/common/Select'
import { Button } from '@/components/common/Button'
import { DecadeBuilder } from './DecadeBuilder'
import { GenreBuilder } from './GenreBuilder'
import { CustomBuilder, type SelectedMovie } from './CustomBuilder'
import { TmdbCollectionBuilder, type SelectedTmdbCollection } from './TmdbCollectionBuilder'

interface CollectionFormProps {
  onSubmit: (data: CollectionCreate) => void
  onCancel: () => void
}

const CATEGORY_OPTIONS = [
  { value: 'static_items', label: 'Custom' },
  { value: 'tmdb_collection', label: 'TMDB Collection' },
  { value: 'genre', label: 'Genre' },
  { value: 'decade', label: 'Decade' },
]

const AUTO_NAME_BANNERS: Partial<Record<BuilderType, string>> = {
  tmdb_collection:
    'Name and description will be pulled automatically from the TMDB collection you select.',
  genre: 'This collection will be named after the genre you pick, e.g. "Action". Movies only.',
  decade:
    'This collection will be named after the decade you pick, e.g. "2010s Movies". Movies only.',
}

function InfoBanner({ text }: { text: string }) {
  return (
    <div className="flex gap-2 items-start bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg px-3 py-2.5">
      <svg
        className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <p className="text-xs text-blue-700 dark:text-blue-300 leading-relaxed">{text}</p>
    </div>
  )
}

function isValid(
  category: BuilderType,
  name: string,
  selectedMovies: SelectedMovie[],
  selectedGenre: string | null,
  selectedDecade: number | null,
  selectedTmdb: SelectedTmdbCollection | null,
): boolean {
  if (category === 'static_items') return name.trim().length > 0 && selectedMovies.length > 0
  if (category === 'genre') return selectedGenre !== null
  if (category === 'decade') return selectedDecade !== null
  if (category === 'tmdb_collection') return selectedTmdb !== null
  return false
}

function buildPayload(
  category: BuilderType,
  name: string,
  description: string,
  selectedMovies: SelectedMovie[],
  selectedGenre: string | null,
  selectedDecade: number | null,
  selectedTmdb: SelectedTmdbCollection | null,
): CollectionCreate {
  if (category === 'static_items') {
    return {
      name: name.trim(),
      description: description.trim() || undefined,
      builder_type: 'static_items',
      builder_config: {
        items: selectedMovies.map((m) => ({ tmdb_id: m.tmdb_id, item_type: 'movie' })),
      },
    }
  }
  if (category === 'genre' && selectedGenre) {
    return {
      name: selectedGenre,
      builder_type: 'genre',
      builder_config: { genre: selectedGenre },
    }
  }
  if (category === 'decade' && selectedDecade !== null) {
    return {
      name: `${selectedDecade}s Movies`,
      builder_type: 'decade',
      builder_config: { decade: selectedDecade },
    }
  }
  // tmdb_collection
  return {
    name: selectedTmdb?.name ?? '',
    description: selectedTmdb?.description || undefined,
    builder_type: 'tmdb_collection',
    builder_config: { tmdb_collection_id: selectedTmdb?.id },
  }
}

export function CollectionForm({ onSubmit, onCancel }: CollectionFormProps) {
  const [category, setCategory] = useState<BuilderType>('static_items')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [selectedMovies, setSelectedMovies] = useState<SelectedMovie[]>([])
  const [selectedGenre, setSelectedGenre] = useState<string | null>(null)
  const [selectedDecade, setSelectedDecade] = useState<number | null>(null)
  const [selectedTmdb, setSelectedTmdb] = useState<SelectedTmdbCollection | null>(null)

  const handleCategoryChange = (val: string) => {
    setCategory(val as BuilderType)
    setSelectedMovies([])
    setSelectedGenre(null)
    setSelectedDecade(null)
    setSelectedTmdb(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(
      buildPayload(
        category,
        name,
        description,
        selectedMovies,
        selectedGenre,
        selectedDecade,
        selectedTmdb,
      ),
    )
  }

  const valid = isValid(category, name, selectedMovies, selectedGenre, selectedDecade, selectedTmdb)
  const bannerText = AUTO_NAME_BANNERS[category]
  const isCustom = category === 'static_items'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-xl rounded-xl bg-white dark:bg-slate-800 shadow-xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex-shrink-0">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">New Collection</h2>
          <button
            type="button"
            onClick={onCancel}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
            aria-label="Close"
          >
            <FaTimes className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable body */}
        <form onSubmit={handleSubmit} className="flex flex-col flex-1 min-h-0">
          <div className="px-6 py-4 space-y-4 overflow-y-auto max-h-[70vh]">
            {/* Category dropdown - always shown first */}
            <Select
              label="Category"
              options={CATEGORY_OPTIONS}
              value={category}
              onChange={handleCategoryChange}
            />

            {/* Auto-name info banner */}
            {bannerText && <InfoBanner text={bannerText} />}

            {/* Name + Description — only for Custom */}
            {isCustom && (
              <>
                <TextInput
                  label="Name"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="My Collection"
                />
                <TextInput
                  label="Description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Optional description"
                />
              </>
            )}

            {/* Per-category builder */}
            {category === 'static_items' && (
              <CustomBuilder
                selected={selectedMovies}
                onAdd={(m) => setSelectedMovies((prev) => [...prev, m])}
                onRemove={(id) => setSelectedMovies((prev) => prev.filter((m) => m.tmdb_id !== id))}
              />
            )}
            {category === 'tmdb_collection' && (
              <TmdbCollectionBuilder
                selected={selectedTmdb}
                onSelect={setSelectedTmdb}
                onRemove={() => setSelectedTmdb(null)}
              />
            )}
            {category === 'genre' && (
              <GenreBuilder selected={selectedGenre} onSelect={setSelectedGenre} />
            )}
            {category === 'decade' && (
              <DecadeBuilder selected={selectedDecade} onSelect={setSelectedDecade} />
            )}
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 px-6 py-4 border-t border-slate-200 dark:border-slate-700 flex-shrink-0">
            <Button type="button" variant="secondary" onClick={onCancel}>
              Cancel
            </Button>
            <Button type="submit" disabled={!valid}>
              Create Collection
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CollectionForm
