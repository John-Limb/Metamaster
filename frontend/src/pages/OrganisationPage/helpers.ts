import type { RenameProposal } from '@/services/organisationService'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface SeasonGroup {
  season_number: number
  episodes: RenameProposal[]
}

export interface ShowGroup {
  show_title: string
  seasons: SeasonGroup[]
}

// ---------------------------------------------------------------------------
// groupEpisodes
// ---------------------------------------------------------------------------

export function groupEpisodes(episodes: RenameProposal[]): ShowGroup[] {
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
// maybeShorten
// ---------------------------------------------------------------------------

export function maybeShorten(path: string): string {
  const parts = path.split('/')
  return parts.length <= 3 ? path : `…/${parts.slice(-3).join('/')}`
}
