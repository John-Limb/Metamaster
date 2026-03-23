import React from 'react'
import {
  MediaCollectionPage,
  type MediaCollectionConfig,
  type MediaCollectionStore,
} from '@/components/features/media/MediaCollectionPage/MediaCollectionPage'
import { TVShowCard } from '../TVShowCard'
import { useTVShowStore } from '@/stores/tvShowStore'
import { usePlexStore } from '@/stores/plexStore'
import { tvShowService } from '@/services/tvShowService'
import type { TVShow } from '@/types'
import './TVShowsPage.css'

function useTVShowsCollectionStore(): MediaCollectionStore<TVShow> {
  const { tvShows, totalTVShows, currentPage, isLoading, error, fetchTVShows } = useTVShowStore()
  return { items: tvShows, total: totalTVShows, currentPage, isLoading, error, fetchItems: fetchTVShows }
}

const tvShowFilterSections = [
  {
    id: 'genre',
    label: 'Genre',
    multiSelect: true,
    options: [
      { value: 'action', label: 'Action', count: 0 },
      { value: 'comedy', label: 'Comedy', count: 0 },
      { value: 'drama', label: 'Drama', count: 0 },
      { value: 'horror', label: 'Horror', count: 0 },
      { value: 'sci-fi', label: 'Sci-Fi', count: 0 },
      { value: 'thriller', label: 'Thriller', count: 0 },
    ],
  },
  {
    id: 'status',
    label: 'Status',
    multiSelect: true,
    options: [
      { value: 'continuing', label: 'Continuing', count: 0 },
      { value: 'ended', label: 'Ended', count: 0 },
    ],
  },
  {
    id: 'rating',
    label: 'Rating',
    multiSelect: false,
    options: [
      { value: '5', label: '5 Stars', count: 0 },
      { value: '4', label: '4+ Stars', count: 0 },
      { value: '3', label: '3+ Stars', count: 0 },
    ],
  },
]

const tvShowSortOptions = [
  { value: 'name-asc', label: 'Name', direction: 'asc' as const },
  { value: 'name-desc', label: 'Name', direction: 'desc' as const },
  { value: 'rating-asc', label: 'Rating', direction: 'asc' as const },
  { value: 'rating-desc', label: 'Rating', direction: 'desc' as const },
]

const TVShowsPage: React.FC = () => {
  const { resolveMismatch } = usePlexStore()

  const tvShowsConfig: MediaCollectionConfig<TVShow> = {
    title: 'TV Shows',
    mediaType: 'tv_show',
    cssPrefix: 'tvshows-page',
    useStore: useTVShowsCollectionStore,
    onScanDirectory: async () => {
      const result = await tvShowService.scanDirectory()
      return { files_synced: result.files_synced, items_created: result.shows_created }
    },
    formatScanResult: (r) =>
      `Scan complete: ${r.files_synced} file(s) synced, ${r.items_created} episode(s) created`,
    renderCard: (show, mismatch) => (
      <TVShowCard
        key={show.id}
        id={String(show.id)}
        title={show.title}
        rating={show.rating}
        poster_url={show.poster_url}
        genres={show.genre}
        seasons={show.seasons}
        episodes={show.episodes}
        mismatch={mismatch}
        ourTmdbId={show.tmdb_id ?? ''}
        onResolve={resolveMismatch}
        onClick={() => {}}
        onAddToQueue={() => console.log('Add to queue:', show.id)}
        onEdit={() => console.log('Edit:', show.id)}
        onDelete={() => console.log('Delete:', show.id)}
        watchedEpisodeCount={show.watched_episode_count}
        totalEpisodeCount={show.total_episode_count}
      />
    ),
    filterSections: tvShowFilterSections,
    sortOptions: tvShowSortOptions,
    defaultSort: 'name-asc',
  }

  return <MediaCollectionPage config={tvShowsConfig} />
}

export default TVShowsPage
