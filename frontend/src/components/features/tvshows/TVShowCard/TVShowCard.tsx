import React, { useState } from 'react'
import { Card, Badge, Button } from '@/components/common'
import './TVShowCard.css'

export interface TVShowCardProps {
  id: string
  title: string
  posterUrl?: string
  seasons?: number
  episodes?: number
  status?: 'continuing' | 'ended' | 'returning'
  nextEpisode?: {
    season: number
    episode: number
    airDate?: string
  }
  rating?: number
  genres?: string[]
  onClick?: () => void
  onAddToQueue?: () => void
  onEdit?: () => void
  onDelete?: () => void
}

export const TVShowCard: React.FC<TVShowCardProps> = ({
  id,
  title,
  posterUrl,
  seasons = 0,
  episodes = 0,
  status,
  nextEpisode,
  rating,
  genres = [],
  onClick,
  onAddToQueue,
  onEdit,
  onDelete,
}) => {
  const [showActions, setShowActions] = useState(false)

  const renderStars = (rating: number) => {
    const stars = Math.round(rating / 2)
    return '★'.repeat(stars) + '☆'.repeat(5 - stars)
  }

  const getStatusBadgeVariant = (status?: string) => {
    switch (status) {
      case 'continuing':
        return 'success'
      case 'returning':
        return 'indigo'
      case 'ended':
        return 'secondary'
      default:
        return 'secondary'
    }
  }

  const getStatusLabel = (status?: string) => {
    switch (status) {
      case 'continuing':
        return 'Continuing'
      case 'returning':
        return 'Returning'
      case 'ended':
        return 'Ended'
      default:
        return 'Unknown'
    }
  }

  return (
    <Card
      variant="elevated"
      className="tvshow-card"
      onClick={onClick}
    >
      <div className="tvshow-card__poster-wrapper">
        {posterUrl ? (
          <img
            src={posterUrl}
            alt={`${title} poster`}
            className="tvshow-card__poster"
            loading="lazy"
          />
        ) : (
          <div className="tvshow-card__poster-placeholder">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="48"
              height="48"
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
              <line x1="2" y1="7" x2="7" y2="7" />
              <line x1="2" y1="17" x2="7" y2="17" />
              <line x1="17" y1="17" x2="22" y2="17" />
              <line x1="17" y1="7" x2="22" y2="7" />
            </svg>
          </div>
        )}

        {rating !== undefined && (
          <div className="tvshow-card__rating">
            <span className="tvshow-card__rating-stars">{renderStars(rating)}</span>
            <span className="tvshow-card__rating-value">{rating.toFixed(1)}</span>
          </div>
        )}

        <div className="tvshow-card__badges">
          {status && (
            <Badge variant={getStatusBadgeVariant(status)} size="sm">
              {getStatusLabel(status)}
            </Badge>
          )}
          {seasons > 0 && (
            <Badge variant="secondary" size="sm">
              {seasons} {seasons === 1 ? 'Season' : 'Seasons'}
            </Badge>
          )}
        </div>

        {nextEpisode && (
          <div className="tvshow-card__next-episode">
            <span className="tvshow-card__next-episode-label">S{nextEpisode.season}:E{nextEpisode.episode}</span>
            {nextEpisode.airDate && (
              <span className="tvshow-card__next-episode-date">{nextEpisode.airDate}</span>
            )}
          </div>
        )}

        <div
          className={`tvshow-card__overlay ${showActions ? 'tvshow-card__overlay--visible' : ''}`}
        >
          <div className="tvshow-card__actions">
            {onAddToQueue && (
              <Button
                variant="secondary"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  onAddToQueue()
                }}
                aria-label="Add to queue"
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
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
              </Button>
            )}
            {onEdit && (
              <Button
                variant="secondary"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  onEdit()
                }}
                aria-label="Edit"
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
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
              </Button>
            )}
            {onDelete && (
              <Button
                variant="danger"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  onDelete()
                }}
                aria-label="Delete"
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
                  <polyline points="3 6 5 6 21 6" />
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                </svg>
              </Button>
            )}
          </div>
        </div>
      </div>

      <Card.Content className="tvshow-card__content">
        <h3 className="tvshow-card__title">{title}</h3>
        <div className="tvshow-card__meta">
          {episodes > 0 && (
            <span className="tvshow-card__episodes">{episodes} episodes</span>
          )}
          {genres.length > 0 && (
            <div className="tvshow-card__genres">
              {genres.slice(0, 2).map((genre) => (
                <Badge key={genre} variant="secondary" size="sm">
                  {genre}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </Card.Content>
    </Card>
  )
}
