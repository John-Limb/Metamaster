import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button, Badge, Card, EmptyState } from '@/components/common'
import { movieService } from '@/services/movieService'
import { enrichmentService } from '@/services/enrichmentService'
import { EnrichmentBadge } from '@/components/features/media/EnrichmentBadge/EnrichmentBadge'
import { formatFileSize } from '@/utils/helpers'
import type { Movie } from '@/types'
import './MovieDetailPage.css'

const MovieDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [movie, setMovie] = useState<Movie | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [externalIdInput, setExternalIdInput] = useState('')
  const [enriching, setEnriching] = useState(false)

  useEffect(() => {
    if (!id) return
    setIsLoading(true)
    setError(null)
    movieService
      .getMovieDetails(id)
      .then((data) => setMovie(data))
      .catch(() => setError('Failed to load movie details'))
      .finally(() => setIsLoading(false))
  }, [id])

  const formatDuration = (seconds: number) => {
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    return h > 0 ? `${h}h ${m}m` : `${m}m`
  }

  const parseGenres = (genres?: string[] | string): string[] => {
    if (!genres) return []
    if (Array.isArray(genres)) return genres
    try {
      return JSON.parse(genres)
    } catch {
      return []
    }
  }

  if (isLoading) {
    return (
      <div className="movie-detail-page">
        <div className="movie-detail-page__loading">
          <div className="movie-detail-page__skeleton-content">
            <div className="movie-detail-page__skeleton-title" />
            <div className="movie-detail-page__skeleton-meta" />
            <div className="movie-detail-page__skeleton-overview" />
          </div>
        </div>
      </div>
    )
  }

  if (!movie && !isLoading) {
    return (
      <div className="movie-detail-page">
        <EmptyState
          variant="not-found"
          title={error || 'Movie not found'}
          description="The movie you're looking for doesn't exist or has been removed."
          action={{
            label: 'Back to Movies',
            onClick: () => navigate('/movies'),
          }}
        />
      </div>
    )
  }

  const renderStars = (rating: number) => {
    const stars = Math.round(rating / 2)
    return '★'.repeat(stars) + '☆'.repeat(5 - stars)
  }

  const genres = parseGenres(movie?.genre)
  const hasFileInfo = movie?.resolution || movie?.codec_video || movie?.codec_audio || movie?.file_size || movie?.file_duration

  return (
    <div className="movie-detail-page">
      {/* Content */}
      <div className="movie-detail-page__content">
        {/* Back Button */}
        <Button
          variant="secondary"
          onClick={() => navigate('/movies')}
          className="movie-detail-page__back-btn"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Back to Movies
        </Button>

        {movie && (
        <div className="movie-detail-page__main">
          {/* Poster */}
          <div className="movie-detail-page__poster-wrapper">
            {movie.poster_url ? (
              <img
                src={movie.poster_url}
                alt={`${movie.title} poster`}
                className="movie-detail-page__poster"
              />
            ) : (
              <div className="movie-detail-page__poster-placeholder">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="64"
                  height="64"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18" />
                  <line x1="7" y1="2" x2="7" y2="22" />
                  <line x1="17" y1="2" x2="17" y2="22" />
                  <line x1="2" y1="12" x2="22" y2="12" />
                </svg>
              </div>
            )}
          </div>

          {/* Info */}
          <div className="movie-detail-page__info">
            <h1 className="movie-detail-page__title">{movie.title}</h1>

            <div className="movie-detail-page__meta">
              {movie.year && <span className="movie-detail-page__year">{movie.year}</span>}
              {movie.runtime && (
                <span className="movie-detail-page__runtime">
                  {Math.floor(movie.runtime / 60)}h {movie.runtime % 60}m
                </span>
              )}
              {movie.quality && (
                <Badge variant="indigo">{movie.quality}</Badge>
              )}
            </div>

            {movie.rating != null && (
              <div className="movie-detail-page__rating">
                <span className="movie-detail-page__rating-stars">
                  {renderStars(movie.rating)}
                </span>
                <span className="movie-detail-page__rating-value">
                  {movie.rating.toFixed(1)}/10
                </span>
              </div>
            )}

            {genres.length > 0 && (
              <div className="movie-detail-page__genres">
                {genres.map((genre) => (
                  <Badge key={genre} variant="secondary">
                    {genre}
                  </Badge>
                ))}
              </div>
            )}

            {movie.plot && (
              <p className="movie-detail-page__overview">{movie.plot}</p>
            )}

            {movie.director && (
              <div className="movie-detail-page__detail-row">
                <span className="movie-detail-page__detail-label">Director</span>
                <span className="movie-detail-page__detail-value">{movie.director}</span>
              </div>
            )}

            {/* File Information */}
            {hasFileInfo && (
              <section className="movie-detail-page__section">
                <h2 className="movie-detail-page__section-title">File Information</h2>
                <div className="movie-detail-page__file-info">
                  {movie.resolution && (
                    <div className="movie-detail-page__detail-row">
                      <span className="movie-detail-page__detail-label">Resolution</span>
                      <span className="movie-detail-page__detail-value">{movie.resolution}</span>
                    </div>
                  )}
                  {movie.codec_video && (
                    <div className="movie-detail-page__detail-row">
                      <span className="movie-detail-page__detail-label">Video Codec</span>
                      <span className="movie-detail-page__detail-value">{movie.codec_video}</span>
                    </div>
                  )}
                  {movie.codec_audio && (
                    <div className="movie-detail-page__detail-row">
                      <span className="movie-detail-page__detail-label">Audio Codec</span>
                      <span className="movie-detail-page__detail-value">{movie.codec_audio}</span>
                    </div>
                  )}
                  {movie.file_size != null && (
                    <div className="movie-detail-page__detail-row">
                      <span className="movie-detail-page__detail-label">File Size</span>
                      <span className="movie-detail-page__detail-value">{formatFileSize(movie.file_size)}</span>
                    </div>
                  )}
                  {movie.file_duration != null && (
                    <div className="movie-detail-page__detail-row">
                      <span className="movie-detail-page__detail-label">Duration</span>
                      <span className="movie-detail-page__detail-value">{formatDuration(movie.file_duration)}</span>
                    </div>
                  )}
                </div>
              </section>
            )}

            {/* Enrichment Status */}
            <section className="movie-detail-page__section">
              <h2 className="movie-detail-page__section-title">Enrichment Status</h2>
              <div className="movie-detail-page__file-info">
                <div className="movie-detail-page__detail-row">
                  <span className="movie-detail-page__detail-label">Status</span>
                  <span className="movie-detail-page__detail-value" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <EnrichmentBadge status={(movie as any).enrichment_status} />
                    <span>{(movie as any).enrichment_status ?? 'unknown'}</span>
                  </span>
                </div>

                {(movie as any).enrichment_error && (
                  <div className="movie-detail-page__detail-row">
                    <span className="movie-detail-page__detail-label">Error</span>
                    <span className="movie-detail-page__detail-value" style={{ color: 'var(--color-error, #ef4444)', fontSize: '0.875rem' }}>
                      {(movie as any).enrichment_error}
                    </span>
                  </div>
                )}

                {(movie as any).detected_external_id && (
                  <div className="movie-detail-page__detail-row">
                    <span className="movie-detail-page__detail-label">Detected ID</span>
                    <span className="movie-detail-page__detail-value" style={{ fontSize: '0.875rem' }}>
                      <code>{(movie as any).detected_external_id}</code>
                    </span>
                  </div>
                )}

                {(movie as any).manual_external_id && (
                  <div className="movie-detail-page__detail-row">
                    <span className="movie-detail-page__detail-label">Manual Override</span>
                    <span className="movie-detail-page__detail-value" style={{ fontSize: '0.875rem' }}>
                      <code>{(movie as any).manual_external_id}</code>
                    </span>
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem', alignItems: 'center' }}>
                <input
                  type="text"
                  placeholder="TMDB ID (e.g. 278)"
                  value={externalIdInput}
                  onChange={(e) => setExternalIdInput(e.target.value)}
                  style={{
                    flex: 1,
                    border: '1px solid var(--color-border, #d1d5db)',
                    borderRadius: '0.375rem',
                    padding: '0.25rem 0.5rem',
                    fontSize: '0.875rem',
                    background: 'var(--color-surface, #fff)',
                    color: 'var(--color-text, inherit)',
                  }}
                />
                <Button
                  variant="primary"
                  size="sm"
                  onClick={async () => {
                    if (!externalIdInput.trim() || !movie) return
                    setEnriching(true)
                    try {
                      await enrichmentService.setMovieExternalId(Number(movie.id), externalIdInput.trim())
                      window.location.reload()
                    } finally {
                      setEnriching(false)
                    }
                  }}
                  disabled={enriching || !externalIdInput.trim()}
                >
                  {enriching ? 'Saving...' : 'Save & Enrich'}
                </Button>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={async () => {
                    if (!movie) return
                    setEnriching(true)
                    try {
                      await enrichmentService.triggerMovieEnrich(Number(movie.id))
                      window.location.reload()
                    } finally {
                      setEnriching(false)
                    }
                  }}
                  disabled={enriching}
                >
                  {enriching ? '...' : 'Re-Enrich'}
                </Button>
              </div>
            </section>

          </div>
        </div>
        )}
      </div>
    </div>
  )
}

export default MovieDetailPage
