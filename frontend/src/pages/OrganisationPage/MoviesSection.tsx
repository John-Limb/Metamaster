import React from 'react'
import { FaChevronDown, FaChevronRight } from 'react-icons/fa'
import { Button, CheckboxInput } from '@/components/common'
import type { OrganisationPreset, RenameProposal } from '@/services/organisationService'
import { maybeShorten } from './helpers'
import { IndeterminateCheckbox } from './IndeterminateCheckbox'

interface MoviesSectionProps {
  movies: RenameProposal[]
  preset: OrganisationPreset
  collapsedSections: Set<string>
  selected: Set<string>
  onToggleSection: () => void
  onToggleKeys: (keys: string[]) => void
  onToggleItem: (key: string) => void
}

export function MoviesSection({
  movies,
  preset,
  collapsedSections,
  selected,
  onToggleSection,
  onToggleKeys,
  onToggleItem,
}: MoviesSectionProps) {
  const collapsed = collapsedSections.has('movies')
  const movieKeys = movies.map((m) => `movie-${m.file_id}`)
  return (
    <div className="bg-card rounded-xl shadow-sm border border-edge overflow-hidden">
      <div className="flex items-center justify-between">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="flex items-center gap-3 flex-1 px-5 py-3.5 !justify-start hover:bg-subtle"
          onClick={onToggleSection}
        >
          {collapsed ? (
            <FaChevronRight className="w-3.5 h-3.5 text-hint shrink-0" />
          ) : (
            <FaChevronDown className="w-3.5 h-3.5 text-hint shrink-0" />
          )}
          <span className="font-semibold text-body">
            Movies
            <span className="ml-2 text-sm font-normal text-hint">({movies.length})</span>
          </span>
        </Button>
        {movies.length > 0 && !collapsed && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="px-5 text-xs text-primary-600 dark:text-primary-400 hover:underline"
            onClick={() => onToggleKeys(movieKeys)}
          >
            select all
          </Button>
        )}
      </div>

      {!collapsed && (
        movies.length === 0 ? (
          <p className="px-5 py-6 text-sm text-hint border-t border-rule">
            All movies already match the {preset} format.
          </p>
        ) : (
          <table className="w-full text-xs border-t border-edge">
            <thead>
              <tr className="bg-subtle text-hint text-left">
                <th className="px-5 py-2 w-10">
                  <IndeterminateCheckbox
                    keys={movieKeys}
                    selected={selected}
                    onChange={() => onToggleKeys(movieKeys)}
                  />
                </th>
                <th className="py-2 pr-4">Current path</th>
                <th className="py-2 pr-5">Proposed path</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule/50">
              {movies.map((m) => {
                const key = `movie-${m.file_id}`
                return (
                  <tr key={key} className="hover:bg-subtle">
                    <td className="px-5 py-2">
                      <CheckboxInput
                        checked={selected.has(key)}
                        onChange={() => onToggleItem(key)}
                      />
                    </td>
                    <td className="py-2 pr-4 font-mono text-hint">
                      {maybeShorten(m.current_path)}
                    </td>
                    <td className="py-2 pr-5 font-mono text-body">
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
  )
}
