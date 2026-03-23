import React from 'react'
import { FaChevronDown, FaChevronRight } from 'react-icons/fa'
import { Button, CheckboxInput } from '@/components/common'
import type { OrganisationPreset, RenameProposal } from '@/services/organisationService'
import { maybeShorten } from './helpers'
import type { ShowGroup } from './helpers'
import { IndeterminateCheckbox } from './IndeterminateCheckbox'

// ---------------------------------------------------------------------------
// CollapseState / CollapseHandlers
// ---------------------------------------------------------------------------

export interface CollapseState {
  collapsedSections: Set<string>
  collapsedShows: Set<string>
  collapsedSeasons: Set<string>
}

export interface CollapseHandlers {
  onToggleSection: () => void
  onExpandAll: () => void
  onCollapseAll: () => void
  onToggleShow: (id: string) => void
  onToggleSeason: (id: string) => void
  onToggleKeys: (keys: string[]) => void
  onToggleItem: (key: string) => void
}

// ---------------------------------------------------------------------------
// ShowGroupItem
// ---------------------------------------------------------------------------

interface ShowGroupItemProps {
  group: ShowGroup
  collapsedShows: Set<string>
  collapsedSeasons: Set<string>
  selected: Set<string>
  onToggleShow: (key: string) => void
  onToggleSeason: (key: string) => void
  onToggleKeys: (keys: string[]) => void
  onToggleItem: (key: string) => void
}

function ShowGroupItem({
  group,
  collapsedShows,
  collapsedSeasons,
  selected,
  onToggleShow,
  onToggleSeason,
  onToggleKeys,
  onToggleItem,
}: ShowGroupItemProps) {
  const isShowCollapsed = collapsedShows.has(group.show_title)
  const allShowKeys = group.seasons.flatMap((s) => s.episodes.map((e) => `episode-${e.file_id}`))

  return (
    <div className="border-b border-rule/50 last:border-b-0">
      <div className="flex items-center justify-between px-5 py-2.5 bg-subtle/50">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="flex items-center gap-2 flex-1 min-w-0 !justify-start"
          onClick={() => onToggleShow(group.show_title)}
        >
          {isShowCollapsed ? (
            <FaChevronRight className="w-3 h-3 text-hint shrink-0" />
          ) : (
            <FaChevronDown className="w-3 h-3 text-hint shrink-0" />
          )}
          <IndeterminateCheckbox
            keys={allShowKeys}
            selected={selected}
            onChange={() => onToggleKeys(allShowKeys)}
            onClick={(e) => e.stopPropagation()}
          />
          <span className="text-sm font-medium text-dim ml-1 truncate">
            {group.show_title}
            <span className="ml-2 text-xs font-normal text-hint">
              ({allShowKeys.length})
            </span>
          </span>
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="text-xs text-primary-600 dark:text-primary-400 hover:underline shrink-0 ml-3"
          onClick={() => onToggleKeys(allShowKeys)}
        >
          select all
        </Button>
      </div>

      {!isShowCollapsed &&
        group.seasons.map((season) => {
          const seasonKey = `${group.show_title}::S${season.season_number}`
          const isSeasonCollapsed = collapsedSeasons.has(seasonKey)
          const sKeys = season.episodes.map((e) => `episode-${e.file_id}`)

          return (
            <div key={seasonKey}>
              <div className="flex items-center justify-between pl-10 pr-5 py-2 border-t border-rule/30">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="flex items-center gap-2 flex-1 min-w-0 !justify-start"
                  onClick={() => onToggleSeason(seasonKey)}
                >
                  {isSeasonCollapsed ? (
                    <FaChevronRight className="w-3 h-3 text-hint shrink-0" />
                  ) : (
                    <FaChevronDown className="w-3 h-3 text-hint shrink-0" />
                  )}
                  <IndeterminateCheckbox
                    keys={sKeys}
                    selected={selected}
                    onChange={() => onToggleKeys(sKeys)}
                    onClick={(e) => e.stopPropagation()}
                  />
                  <span className="text-xs font-medium text-dim ml-1">
                    Season {String(season.season_number).padStart(2, '0')}
                    <span className="ml-2 font-normal text-hint">
                      ({season.episodes.length})
                    </span>
                  </span>
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="text-xs text-primary-600 dark:text-primary-400 hover:underline shrink-0 ml-3"
                  onClick={() => onToggleKeys(sKeys)}
                >
                  select all
                </Button>
              </div>

              {!isSeasonCollapsed && (
                <table className="w-full text-xs">
                  <tbody className="divide-y divide-rule/30">
                    {season.episodes.map((ep) => {
                      const key = `episode-${ep.file_id}`
                      return (
                        <tr key={key} className="hover:bg-subtle">
                          <td className="pl-16 pr-3 py-1.5 w-16">
                            <CheckboxInput
                              checked={selected.has(key)}
                              onChange={() => onToggleItem(key)}
                            />
                          </td>
                          <td className="py-1.5 pr-4 font-mono text-hint">
                            {maybeShorten(ep.current_path)}
                          </td>
                          <td className="py-1.5 pr-5 font-mono text-dim">
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
}

// ---------------------------------------------------------------------------
// TVShowsSection
// ---------------------------------------------------------------------------

interface TVShowsSectionProps {
  showGroups: ShowGroup[]
  episodes: RenameProposal[]
  preset: OrganisationPreset
  selected: Set<string>
  collapseState: CollapseState
  handlers: CollapseHandlers
}

export function TVShowsSection({
  showGroups,
  episodes,
  preset,
  selected,
  collapseState,
  handlers,
}: TVShowsSectionProps) {
  const { collapsedSections, collapsedShows, collapsedSeasons } = collapseState
  const { onToggleSection, onExpandAll, onCollapseAll, onToggleShow, onToggleSeason, onToggleKeys, onToggleItem } = handlers
  const collapsed = collapsedSections.has('tv')
  return (
    <div className="bg-card rounded-xl shadow-sm border border-edge overflow-hidden">
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-edge">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="flex items-center gap-3 flex-1 !justify-start hover:text-dim"
          onClick={onToggleSection}
        >
          {collapsed ? (
            <FaChevronRight className="w-3.5 h-3.5 text-hint shrink-0" />
          ) : (
            <FaChevronDown className="w-3.5 h-3.5 text-hint shrink-0" />
          )}
          <span className="font-semibold text-body">
            TV Shows
            <span className="ml-2 text-sm font-normal text-hint">
              ({episodes.length} episode{episodes.length !== 1 ? 's' : ''},{' '}
              {showGroups.length} show{showGroups.length !== 1 ? 's' : ''})
            </span>
          </span>
        </Button>
        {showGroups.length > 0 && !collapsed && (
          <div className="flex gap-3 text-xs text-primary-600 dark:text-primary-400 shrink-0">
            <Button type="button" variant="ghost" size="sm" onClick={onExpandAll} className="hover:underline">
              expand all
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={onCollapseAll} className="hover:underline">
              collapse all
            </Button>
          </div>
        )}
      </div>

      {!collapsed && (
        showGroups.length === 0 ? (
          <p className="px-5 py-6 text-sm text-hint">
            All episodes already match the {preset} format.
          </p>
        ) : (
          showGroups.map((group) => (
            <ShowGroupItem
              key={group.show_title}
              group={group}
              collapsedShows={collapsedShows}
              collapsedSeasons={collapsedSeasons}
              selected={selected}
              onToggleShow={onToggleShow}
              onToggleSeason={onToggleSeason}
              onToggleKeys={onToggleKeys}
              onToggleItem={onToggleItem}
            />
          ))
        )
      )}
    </div>
  )
}
