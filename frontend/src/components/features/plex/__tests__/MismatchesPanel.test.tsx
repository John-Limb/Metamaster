import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MismatchesPanel } from '../MismatchesPanel'

const mismatches = [
  { id: 10, item_type: 'movie', item_id: 42, plex_rating_key: '77', plex_tmdb_id: '9999' },
]

describe('MismatchesPanel', () => {
  it('renders nothing when there are no mismatches', () => {
    const { container } = render(
      <MismatchesPanel mismatches={[]} onResolve={vi.fn()} />
    )
    expect(container.firstChild).toBeNull()
  })

  it('shows mismatch count when mismatches exist', () => {
    render(<MismatchesPanel mismatches={mismatches} onResolve={vi.fn()} />)
    expect(screen.getByText(/1 TMDB mismatch/i)).toBeInTheDocument()
  })

  it('shows item details', () => {
    render(<MismatchesPanel mismatches={mismatches} onResolve={vi.fn()} />)
    expect(screen.getByText(/movie #42/i)).toBeInTheDocument()
  })

  it('opens the resolve modal when Resolve is clicked', () => {
    render(<MismatchesPanel mismatches={mismatches} onResolve={vi.fn()} />)
    fireEvent.click(screen.getByText(/Resolve/i))
    expect(screen.getByText(/Trust MetaMaster/i)).toBeInTheDocument()
  })
})
