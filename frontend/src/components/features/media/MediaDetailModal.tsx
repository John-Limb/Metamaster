import React, { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useEscapeKey } from '@/hooks'
import { Badge, Button } from '@/components/common'
import { formatBytes, formatDuration } from '@/utils/formatting'
import { movieService } from '@/services/movieService'
import { tvShowService } from '@/services/tvShowService'
import type { Movie, TVShow } from '@/types'
import './MediaDetailModal.css'

type MediaType = 'movie' | 'tv_show'

interface MediaDetailModalProps {
  isOpen: boolean
  mediaType: MediaType
  mediaId: string
  onClose: () => void
  onMetadataSynced?: () => void
}

const formatRuntime = (minutes: number) => {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}

const parseGenres = (genres?: string | string[]): string[] => {
  if (!genres) return []
  if (Array.isArray(genres)) return genres
  try {
    const parsed = JSON.parse(genres)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const renderStars = (rating: number) => {
  const stars = Math.round(rating / 2)
  return '★'.repeat(stars) + '☆'.repeat(5 - stars)
}

export const MediaDetailModal: React.FC<MediaDetailModalProps> = ({
  isOpen,
  mediaType,
  mediaId,
  onClose,
  onMetadataSynced,
}) => {
  const navigate = useNavigate()
  const [movie, setMovie] = useState<Movie | null>(null)
  const [tvShow, setTVShow] = useState<TVShow | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSyncing, setIsSyncing] = useState(false)
  const [syncError, setSyncError] = useState<string | null>(null)
  const [syncSuccess, setSyncSuccess] = useState(false)

  useEffect(() => {
    if (!isOpen || !mediaId) return

    setIsLoading(true)
    setMovie(null)
    setTVShow(null)
    setSyncError(null)
    setSyncSuccess(false)

    if (mediaType === 'movie') {
      movieService
        .getMovieDetails(mediaId)
        .then(setMovie)
        .catch(() => {})
        .finally(() => setIsLoading(false))
    } else {
      tvShowService
        .getTVShowDetails(mediaId)
        .then(setTVShow)
        .catch(() => {})
        .finally(() => setIsLoading(false))
    }
  }, [isOpen, mediaId, mediaType])

  useEscapeKey(onClose, isOpen)

  const handleSyncMetadata = useCallback(async () => {
    setIsSyncing(true)
    setSyncError(null)
    setSyncSuccess(false)
    try {
      if (mediaType === 'movie') {
        await movieService.syncMetadata(mediaId)
        // Also run FFprobe scan to get quality/resolution/codec data
        try {
          await movieService.scanMovie(mediaId)
        } catch {
          // Scan may fail if ffprobe unavailable — non-fatal
        }
        const refreshed = await movieService.getMovieDetails(mediaId)
        setMovie(refreshed)
      } else {
        await tvShowService.syncMetadata(mediaId)
        const refreshed = await tvShowService.getTVShowDetails(mediaId)
        setTVShow(refreshed)
      }
      setSyncSuccess(true)
      onMetadataSynced?.()
      setTimeout(() => setSyncSuccess(false), 3000)
    } catch {
      setSyncError('Failed to sync metadata. Check server logs.')
      setTimeout(() => setSyncError(null), 5000)
    } finally {
      setIsSyncing(false)
    }
  }, [mediaType, mediaId, onMetadataSynced])

  const handleViewDetails = useCallback(() => {
    onClose()
    if (mediaType === 'movie') {
      navigate(`/movies/${mediaId}`)
    } else {
      navigate(`/tv-shows/${mediaId}`)
    }
  }, [navigate, mediaType, mediaId, onClose])

  if (!isOpen) return null

  const title = mediaType === 'movie' ? movie?.title : tvShow?.title
  const poster_url = mediaType === 'movie' ? movie?.poster_url : tvShow?.poster_url
  const rating = mediaType === 'movie' ? movie?.rating : tvShow?.rating
  const genres = parseGenres(
    mediaType === 'movie' ? (movie?.genre || movie?.genres) : (tvShow?.genre || tvShow?.genres)
  )
  const plot = mediaType === 'movie' ? movie?.plot : tvShow?.plot
  const hasPoster = Boolean(poster_url)

  return (
    <div className="media-modal__backdrop" onClick={onClose} aria-hidden="true">
      <div
        className="media-modal"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={title || 'Media details'}
      >
        {/* Close button */}
        <button type="button" className="media-modal__close" onClick={onClose} aria-label="Close">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        {isLoading ? (
          <div className="media-modal__loading">
            <div className="media-modal__spinner" />
            <p>Loading details...</p>
          </div>
        ) : (
          <div className="media-modal__body">
            {/* Poster */}
            <div className="media-modal__poster-section">
              {poster_url ? (
                <img src={poster_url} alt={`${title} poster`} className="media-modal__poster" />
              ) : (
                <div className="media-modal__poster-placeholder">
                  <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="2" y="2" width="20" height="20" rx="2.18" ry="2.18" />
                    <line x1="7" y1="2" x2="7" y2="22" />
                    <line x1="17" y1="2" x2="17" y2="22" />
                    <line x1="2" y1="12" x2="22" y2="12" />
                    <line x1="2" y1="7" x2="7" y2="7" />
                    <line x1="2" y1="17" x2="7" y2="17" />
                    <line x1="17" y1="17" x2="22" y2="17" />
                    <line x1="17" y1="7" x2="22" y2="7" />
                  </svg>
                  <span>No poster</span>
                </div>
              )}

              {!hasPoster && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleSyncMetadata}
                  disabled={isSyncing}
                  className="media-modal__sync-btn--prominent"
                >
                  {isSyncing ? 'Syncing...' : 'Fetch Poster & Metadata'}
                </Button>
              )}
            </div>

            {/* Details */}
            <div className="media-modal__details">
              <div className="media-modal__header">
                <h2 className="media-modal__title">{title || 'Unknown'}</h2>
                <div className="media-modal__meta-row">
                  {mediaType === 'movie' && movie?.year && (
                    <span className="media-modal__year">{movie.year}</span>
                  )}
                  {mediaType === 'movie' && movie?.runtime != null && movie.runtime > 0 && (
                    <span className="media-modal__runtime">{formatRuntime(movie.runtime)}</span>
                  )}
                  {mediaType === 'tv_show' && tvShow?.status && (
                    <Badge
                      variant={tvShow.status.toLowerCase() === 'ended' ? 'secondary' : 'success'}
                      size="sm"
                    >
                      {tvShow.status}
                    </Badge>
                  )}
                  {mediaType === 'tv_show' && tvShow?.seasons != null && tvShow.seasons > 0 && (
                    <span className="media-modal__seasons">
                      {tvShow.seasons} {tvShow.seasons === 1 ? 'Season' : 'Seasons'}
                    </span>
                  )}
                  {mediaType === 'tv_show' && tvShow?.episodes != null && tvShow.episodes > 0 && (
                    <span className="media-modal__episodes">
                      {tvShow.episodes} Episodes
                    </span>
                  )}
                </div>
              </div>

              {rating != null && (
                <div className="media-modal__rating">
                  <span className="media-modal__rating-stars">{renderStars(rating)}</span>
                  <span className="media-modal__rating-value">{rating.toFixed(1)}/10</span>
                </div>
              )}

              {genres.length > 0 && (
                <div className="media-modal__genres">
                  {genres.map((genre) => (
                    <Badge key={genre} variant="secondary" size="sm">
                      {genre}
                    </Badge>
                  ))}
                </div>
              )}

              {plot && (
                <div className="media-modal__plot">
                  <h3>Overview</h3>
                  <p>{plot}</p>
                </div>
              )}

              {mediaType === 'movie' && movie?.quality && (
                <div className="media-modal__quality-badge">
                  <Badge variant="indigo" size="md">{movie.quality}</Badge>
                </div>
              )}

              {/* File info for movies */}
              {mediaType === 'movie' && movie && (movie.resolution || movie.codec_video || movie.codec_audio || movie.audio_channels || movie.file_size || movie.file_duration) && (
                <div className="media-modal__file-info">
                  <h3>File Information</h3>
                  <div className="media-modal__file-grid">
                    {movie.resolution && (
                      <div className="media-modal__file-item">
                        <span className="media-modal__file-label">Resolution</span>
                        <span className="media-modal__file-value">{movie.resolution}</span>
                      </div>
                    )}
                    {movie.codec_video && (
                      <div className="media-modal__file-item">
                        <span className="media-modal__file-label">Video Codec</span>
                        <span className="media-modal__file-value">{movie.codec_video}</span>
                      </div>
                    )}
                    {movie.codec_audio && (
                      <div className="media-modal__file-item">
                        <span className="media-modal__file-label">Audio Codec</span>
                        <span className="media-modal__file-value">{movie.codec_audio}</span>
                      </div>
                    )}
                    {movie.audio_channels && (
                      <div className="media-modal__file-item">
                        <span className="media-modal__file-label">Audio</span>
                        <span className="media-modal__file-value">{movie.audio_channels}</span>
                      </div>
                    )}
                    {movie.file_size != null && (
                      <div className="media-modal__file-item">
                        <span className="media-modal__file-label">File Size</span>
                        <span className="media-modal__file-value">{formatBytes(movie.file_size)}</span>
                      </div>
                    )}
                    {movie.file_duration != null && (
                      <div className="media-modal__file-item">
                        <span className="media-modal__file-label">Duration</span>
                        <span className="media-modal__file-value">{formatDuration(movie.file_duration)}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Sync status messages */}
              {syncSuccess && (
                <p className="media-modal__sync-success">Metadata synced successfully.</p>
              )}
              {syncError && (
                <p className="media-modal__sync-error">{syncError}</p>
              )}

              {/* Actions */}
              <div className="media-modal__actions">
                <Button variant="primary" onClick={handleViewDetails}>
                  View Full Details
                </Button>
                {hasPoster && (
                  <Button
                    variant="secondary"
                    onClick={handleSyncMetadata}
                    disabled={isSyncing}
                  >
                    {isSyncing ? 'Syncing...' : 'Sync Metadata'}
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
