import React from 'react'
import {
  MediaCollectionPage,
  type MediaCollectionConfig,
  type MediaCollectionStore,
} from '@/components/features/media/MediaCollectionPage/MediaCollectionPage'
import { MovieCard } from '../MovieCard'
import { useMovieStore } from '@/stores/movieStore'
import { movieService } from '@/services/movieService'
import type { Movie } from '@/types'
import type { PlexMismatchItem } from '@/services/plexService'
import './MoviesPage.css'

function useMoviesCollectionStore(): MediaCollectionStore<Movie> {
  const { movies, totalMovies, currentPage, isLoading, error, fetchMovies } = useMovieStore()
  return { items: movies, total: totalMovies, currentPage, isLoading, error, fetchItems: fetchMovies }
}

function renderMovieCard(movie: Movie, mismatch: PlexMismatchItem | undefined) {
  return (
    <MovieCard
      key={movie.id}
      id={String(movie.id)}
      title={movie.title}
      year={movie.year ?? 0}
      rating={movie.rating}
      poster_url={movie.poster_url}
      genres={movie.genre}
      quality={movie.quality}
      resolution={movie.resolution}
      codec_video={movie.codec_video}
      codec_audio={movie.codec_audio}
      audio_channels={movie.audio_channels}
      file_size={movie.file_size}
      file_duration={movie.file_duration}
      mismatch={mismatch}
      ourTmdbId={movie.tmdb_id ?? ''}
      onResolve={async () => {}}
      onClick={() => {}}
      onAddToQueue={() => console.log('Add to queue:', movie.id)}
      onScan={() => movieService.scanMovie(String(movie.id))}
      onEdit={() => console.log('Edit:', movie.id)}
      onDelete={() => console.log('Delete:', movie.id)}
      isWatched={movie.is_watched}
    />
  )
}

const filterSections = [
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
    id: 'year',
    label: 'Year',
    multiSelect: true,
    options: [
      { value: '2024', label: '2024', count: 0 },
      { value: '2023', label: '2023', count: 0 },
      { value: '2022', label: '2022', count: 0 },
      { value: '2021', label: '2021', count: 0 },
      { value: '2020', label: '2020', count: 0 },
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

const sortOptions = [
  { value: 'title-asc', label: 'Title', direction: 'asc' as const },
  { value: 'title-desc', label: 'Title', direction: 'desc' as const },
  { value: 'year-asc', label: 'Year', direction: 'asc' as const },
  { value: 'year-desc', label: 'Year', direction: 'desc' as const },
  { value: 'rating-asc', label: 'Rating', direction: 'asc' as const },
  { value: 'rating-desc', label: 'Rating', direction: 'desc' as const },
  { value: 'date-added', label: 'Date Added' },
]

const moviesConfig: MediaCollectionConfig<Movie> = {
  title: 'Movies',
  mediaType: 'movie',
  cssPrefix: 'movies-page',
  useStore: useMoviesCollectionStore,
  onScanDirectory: async () => {
    const result = await movieService.scanDirectory()
    return { files_synced: result.files_synced, items_created: result.movies_created }
  },
  formatScanResult: (r) =>
    `Scan complete: ${r.files_synced} file(s) synced, ${r.items_created} movie(s) created`,
  renderCard: renderMovieCard,
  filterSections,
  sortOptions,
  defaultSort: 'title-asc',
}

const MoviesPage: React.FC = () => <MediaCollectionPage config={moviesConfig} />

export default MoviesPage
