import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MismatchResolveModal } from '../MismatchResolveModal'

describe('MismatchResolveModal', () => {
  const mismatch = {
    id: 10,
    item_type: 'movie',
    item_id: 42,
    plex_rating_key: '77',
    plex_tmdb_id: '9999',
  }

  it('shows our tmdb id and plex tmdb id', () => {
    render(
      <MismatchResolveModal
        mismatch={mismatch}
        ourTmdbId="603"
        onResolve={vi.fn()}
        onClose={vi.fn()}
      />
    )
    expect(screen.getByText(/603/)).toBeInTheDocument()
    expect(screen.getByText(/9999/)).toBeInTheDocument()
  })

  it('calls onResolve with metamaster when that button is clicked', () => {
    const onResolve = vi.fn()
    render(
      <MismatchResolveModal
        mismatch={mismatch}
        ourTmdbId="603"
        onResolve={onResolve}
        onClose={vi.fn()}
      />
    )
    fireEvent.click(screen.getByText(/Trust MetaMaster/i))
    expect(onResolve).toHaveBeenCalledWith(10, 'metamaster')
  })

  it('calls onResolve with plex when that button is clicked', () => {
    const onResolve = vi.fn()
    render(
      <MismatchResolveModal
        mismatch={mismatch}
        ourTmdbId="603"
        onResolve={onResolve}
        onClose={vi.fn()}
      />
    )
    fireEvent.click(screen.getByText(/Trust Plex/i))
    expect(onResolve).toHaveBeenCalledWith(10, 'plex')
  })

  it('calls onClose when Cancel is clicked', () => {
    const onClose = vi.fn()
    render(
      <MismatchResolveModal
        mismatch={mismatch}
        ourTmdbId="603"
        onResolve={vi.fn()}
        onClose={onClose}
      />
    )
    fireEvent.click(screen.getByText(/Cancel/i))
    expect(onClose).toHaveBeenCalledOnce()
  })
})
