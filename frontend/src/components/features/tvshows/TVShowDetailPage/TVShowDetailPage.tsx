import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button, Badge, Card, EmptyState } from '@/components/common'
import './TVShowDetailPage.css'

// Mock TV show detail type
interface TVShowDetail {
  id: string
  title: string
  backdropUrl?: string
  poster_url?: string
  rating: number
  status: 'continuing' | 'ended' | 'returning'
  genres: string[]
  network?: string
  premiereDate?: string
  overview?: string
  seasons: Array<{
    seasonNumber: number
    episodeCount: number
    title: string
    airDate?: string
  }>
  cast: Array<{ name: string; role: string }>
  relatedShows: Array<{ id: string; title: string; poster_url?: string }>
}

const TVShowDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [showDetail, setShowDetail] = useState<TVShowDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [expandedSeason, setExpandedSeason] = useState<number | null>(null)

  useEffect(() => {
    // Simulate loading
    setIsLoading(true)
    const timer = setTimeout(() => {
      setShowDetail(null)
      setIsLoading(false)
    }, 1000)
    return () => clearTimeout(timer)
  }, [id])

  if (isLoading) {
    return (
      <div className="tvshow-detail-page">
        <div className="tvshow-detail-page__loading">
          <div className="tvshow-detail-page__skeleton-backdrop" />
          <div className="tvshow-detail-page__skeleton-content">
            <div className="tvshow-detail-page__skeleton-title" />
            <div className="tvshow-detail-page__skeleton-meta" />
            <div className="tvshow-detail-page__skeleton-overview" />
          </div>
        </div>
      </div>
    )
  }

  if (!showDetail) {
    return (
      <div className="tvshow-detail-page">
        <EmptyState
          variant="not-found"
          title="TV Show not found"
          description="The TV show you're looking for doesn't exist or has been removed."
          action={{
            label: 'Back to TV Shows',
            onClick: () => navigate('/tv-shows'),
          }}
        />
      </div>
    )
  }

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

  const toggleSeason = (seasonNumber: number) => {
    setExpandedSeason(expandedSeason === seasonNumber ? null : seasonNumber)
  }

  return (
    <div className="tvshow-detail-page">
      {/* Hero Backdrop */}
      <div className="tvshow-detail-page__hero">
        {showDetail.backdropUrl ? (
          <img
            src={showDetail.backdropUrl}
            alt={`${showDetail.title} backdrop`}
            className="tvshow-detail-page__backdrop"
          />
        ) : (
          <div className="tvshow-detail-page__backdrop-placeholder" />
        )}
        <div className="tvshow-detail-page__hero-overlay" />
      </div>

      {/* Content */}
      <div className="tvshow-detail-page__content">
        {/* Back Button */}
        <Button
          variant="secondary"
          onClick={() => navigate('/tv-shows')}
          className="tvshow-detail-page__back-btn"
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
          Back to TV Shows
        </Button>

        <div className="tvshow-detail-page__main">
          {/* Poster */}
          <div className="tvshow-detail-page__poster-wrapper">
            {showDetail.poster_url ? (
              <img
                src={showDetail.poster_url}
                alt={`${showDetail.title} poster`}
                className="tvshow-detail-page__poster"
              />
            ) : (
              <div className="tvshow-detail-page__poster-placeholder">
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
          <div className="tvshow-detail-page__info">
            <h1 className="tvshow-detail-page__title">{showDetail.title}</h1>

            <div className="tvshow-detail-page__meta">
              {showDetail.network && (
                <span className="tvshow-detail-page__network">{showDetail.network}</span>
              )}
              {showDetail.premiereDate && (
                <span className="tvshow-detail-page__premiere">
                  Premiered {showDetail.premiereDate}
                </span>
              )}
              <Badge variant={getStatusBadgeVariant(showDetail.status)}>
                {getStatusLabel(showDetail.status)}
              </Badge>
            </div>

            {showDetail.rating != null && (
              <div className="tvshow-detail-page__rating">
                <span className="tvshow-detail-page__rating-stars">
                  {renderStars(showDetail.rating)}
                </span>
                <span className="tvshow-detail-page__rating-value">
                  {showDetail.rating.toFixed(1)}/10
                </span>
              </div>
            )}

            <div className="tvshow-detail-page__genres">
              {showDetail.genres.map((genre) => (
                <Badge key={genre} variant="secondary">
                  {genre}
                </Badge>
              ))}
            </div>

            {showDetail.overview && (
              <p className="tvshow-detail-page__overview">{showDetail.overview}</p>
            )}

            <div className="tvshow-detail-page__actions">
              <Button variant="primary" size="lg">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  stroke="none"
                >
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
                Play Latest
              </Button>
              <Button variant="secondary" size="lg">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
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
                Add to Queue
              </Button>
            </div>
          </div>
        </div>

        {/* Seasons & Episodes Section */}
        <section className="tvshow-detail-page__section">
          <h2 className="tvshow-detail-page__section-title">Seasons & Episodes</h2>
          <div className="tvshow-detail-page__seasons">
            {showDetail.seasons.map((season) => (
              <Card key={season.seasonNumber} variant="outlined" className="tvshow-detail-page__season-card">
                <div
                  className="tvshow-detail-page__season-header"
                  onClick={() => toggleSeason(season.seasonNumber)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && toggleSeason(season.seasonNumber)}
                >
                  <div className="tvshow-detail-page__season-info">
                    <h3 className="tvshow-detail-page__season-title">{season.title}</h3>
                    <span className="tvshow-detail-page__season-meta">
                      {season.episodeCount} episodes
                      {season.airDate && ` • ${season.airDate}`}
                    </span>
                  </div>
                  <svg
                    className={`tvshow-detail-page__season-arrow ${expandedSeason === season.seasonNumber ? 'tvshow-detail-page__season-arrow--expanded' : ''}`}
                    xmlns="http://www.w3.org/2000/svg"
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </div>
                {expandedSeason === season.seasonNumber && (
                  <div className="tvshow-detail-page__episodes">
                    {Array.from({ length: Math.min(season.episodeCount, 5) }).map((_, index) => (
                      <div key={index} className="tvshow-detail-page__episode-item">
                        <span className="tvshow-detail-page__episode-number">
                          {index + 1}
                        </span>
                        <span className="tvshow-detail-page__episode-title">
                          Episode {index + 1}
                        </span>
                        <Button variant="ghost" size="sm">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="currentColor"
                            stroke="none"
                          >
                            <polygon points="5 3 19 12 5 21 5 3" />
                          </svg>
                        </Button>
                      </div>
                    ))}
                    {season.episodeCount > 5 && (
                      <Button variant="secondary" size="sm" className="tvshow-detail-page__view-all">
                        View all {season.episodeCount} episodes
                      </Button>
                    )}
                  </div>
                )}
              </Card>
            ))}
          </div>
        </section>

        {/* Cast Section */}
        {showDetail.cast.length > 0 && (
          <section className="tvshow-detail-page__section">
            <h2 className="tvshow-detail-page__section-title">Cast</h2>
            <div className="tvshow-detail-page__cast-grid">
              {showDetail.cast.map((actor) => (
                <Card key={actor.name} variant="outlined" padding="sm">
                  <div className="tvshow-detail-page__cast-item">
                    <span className="tvshow-detail-page__cast-name">{actor.name}</span>
                    <span className="tvshow-detail-page__cast-role">{actor.role}</span>
                  </div>
                </Card>
              ))}
            </div>
          </section>
        )}

        {/* Related Shows Section */}
        {showDetail.relatedShows.length > 0 && (
          <section className="tvshow-detail-page__section">
            <h2 className="tvshow-detail-page__section-title">Related Shows</h2>
            <div className="tvshow-detail-page__related-grid">
              {showDetail.relatedShows.map((relatedShow) => (
                <Card
                  key={relatedShow.id}
                  variant="elevated"
                  className="tvshow-detail-page__related-card"
                  onClick={() => navigate(`/tv-shows/${relatedShow.id}`)}
                >
                  {relatedShow.poster_url ? (
                    <img
                      src={relatedShow.poster_url}
                      alt={relatedShow.title}
                      className="tvshow-detail-page__related-poster"
                    />
                  ) : (
                    <div className="tvshow-detail-page__related-poster-placeholder" />
                  )}
                  <Card.Content className="tvshow-detail-page__related-content">
                    <h4 className="tvshow-detail-page__related-title">{relatedShow.title}</h4>
                  </Card.Content>
                </Card>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

export default TVShowDetailPage
