import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NeedsAttentionPage } from './NeedsAttentionPage'
import * as enrichmentService from '@/services/enrichmentService'

vi.mock('@/services/enrichmentService', () => ({
  enrichmentService: {
    getPending: vi.fn(),
    setMovieExternalId: vi.fn(),
    triggerMovieEnrich: vi.fn(),
    triggerTvShowEnrich: vi.fn(),
    setTvShowExternalId: vi.fn(),
  },
}))

describe('NeedsAttentionPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows empty state when nothing pending', async () => {
    vi.mocked(enrichmentService.enrichmentService.getPending).mockResolvedValue({
      movies: [],
      tv_shows: [],
      total: 0,
    })
    render(<NeedsAttentionPage />)
    await waitFor(() =>
      expect(screen.getByText(/all media.*fully enriched/i)).toBeInTheDocument()
    )
  })

  it('shows not_found movie in Manual needed section', async () => {
    vi.mocked(enrichmentService.enrichmentService.getPending).mockResolvedValue({
      movies: [
        {
          id: 1,
          title: 'Inception',
          enrichment_status: 'not_found',
          enrichment_error: 'No match found in OMDB',
        },
      ],
      tv_shows: [],
      total: 1,
    })
    render(<NeedsAttentionPage />)
    await waitFor(() => expect(screen.getByText('Inception')).toBeInTheDocument())
    expect(screen.getByText(/no match found/i)).toBeInTheDocument()
  })

  it('shows external_failed movie in Failed section', async () => {
    vi.mocked(enrichmentService.enrichmentService.getPending).mockResolvedValue({
      movies: [
        {
          id: 2,
          title: 'Dune',
          enrichment_status: 'external_failed',
          enrichment_error: 'API unreachable',
        },
      ],
      tv_shows: [],
      total: 1,
    })
    render(<NeedsAttentionPage />)
    await waitFor(() => expect(screen.getByText('Dune')).toBeInTheDocument())
    expect(screen.getAllByRole('button', { name: /retry/i }).length).toBeGreaterThan(0)
  })
})
