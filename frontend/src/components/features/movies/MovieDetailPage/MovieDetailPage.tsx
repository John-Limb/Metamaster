import React, { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button, Badge, Card, EmptyState } from '@/components/common'
import './MovieDetailPage.css'

// Mock movie detail type
interface MovieDetail {
  id: string
  title: string
  backdropUrl?: string
  posterUrl?: string
  year: number
  rating: number
  genres: string[]
  quality?: string
  runtime?: number
  overview?: string
  director?: string
  cast: Array<{ name: string; role: string }>
  relatedMovies: Array<{ id: string; title: string; posterUrl?: string }>
}

const MovieDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [movie, setMovie] = useState<MovieDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Simulate loading
    setIsLoading(true)
    const timer = setTimeout(() => {
      setMovie(null)
      setIsLoading(false)
    }, 1000)
    return () => clearTimeout(timer)
  }, [id])

  if (isLoading) {
    return (
      <div className="movie-detail-page">
        <div className="movie-detail-page__loading">
          <div className="movie-detail-page__skeleton-backdrop" />
          <div className="movie-detail-page__skeleton-content">
            <div className="movie-detail-page__skeleton-title" />
            <div className="movie-detail-page__skeleton-meta" />
            <div className="movie-detail-page__skeleton-overview" />
          </div>
        </div>
      </div>
    )
  }

  if (!movie) {
    return (
      <div className="movie-detail-page">
        <EmptyState
          variant="not-found"
          title="Movie not found"
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

  return (
    <div className="movie-detail-page">
      {/* Hero Backdrop */}
      <div className="movie-detail-page__hero">
        {movie.backdropUrl ? (
          <img
            src={movie.backdropUrl}
            alt={`${movie.title} backdrop`}
            className="movie-detail-page__backdrop"
          />
        ) : (
          <div className="movie-detail-page__backdrop-placeholder" />
        )}
        <div className="movie-detail-page__hero-overlay" />
      </div>

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

        <div className="movie-detail-page__main">
          {/* Poster */}
          <div className="movie-detail-page__poster-wrapper">
            {movie.posterUrl ? (
              <img
                src={movie.posterUrl}
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
              <span className="movie-detail-page__year">{movie.year}</span>
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

            <div className="movie-detail-page__genres">
              {movie.genres.map((genre) => (
                <Badge key={genre} variant="secondary">
                  {genre}
                </Badge>
              ))}
            </div>

            {movie.overview && (
              <p className="movie-detail-page__overview">{movie.overview}</p>
            )}

            {movie.director && (
              <div className="movie-detail-page__detail-row">
                <span className="movie-detail-page__detail-label">Director</span>
                <span className="movie-detail-page__detail-value">{movie.director}</span>
              </div>
            )}

            <div className="movie-detail-page__actions">
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
                Play
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

        {/* Cast Section */}
        {movie.cast.length > 0 && (
          <section className="movie-detail-page__section">
            <h2 className="movie-detail-page__section-title">Cast</h2>
            <div className="movie-detail-page__cast-grid">
              {movie.cast.map((actor) => (
                <Card key={actor.name} variant="outlined" padding="sm">
                  <div className="movie-detail-page__cast-item">
                    <span className="movie-detail-page__cast-name">{actor.name}</span>
                    <span className="movie-detail-page__cast-role">{actor.role}</span>
                  </div>
                </Card>
              ))}
            </div>
          </section>
        )}

        {/* Related Movies Section */}
        {movie.relatedMovies.length > 0 && (
          <section className="movie-detail-page__section">
            <h2 className="movie-detail-page__section-title">Related Movies</h2>
            <div className="movie-detail-page__related-grid">
              {movie.relatedMovies.map((relatedMovie) => (
                <Card
                  key={relatedMovie.id}
                  variant="elevated"
                  className="movie-detail-page__related-card"
                  onClick={() => navigate(`/movies/${relatedMovie.id}`)}
                >
                  {relatedMovie.posterUrl ? (
                    <img
                      src={relatedMovie.posterUrl}
                      alt={relatedMovie.title}
                      className="movie-detail-page__related-poster"
                    />
                  ) : (
                    <div className="movie-detail-page__related-poster-placeholder" />
                  )}
                  <Card.Content className="movie-detail-page__related-content">
                    <h4 className="movie-detail-page__related-title">{relatedMovie.title}</h4>
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

export default MovieDetailPage
