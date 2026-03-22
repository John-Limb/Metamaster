import React from 'react'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { PlaylistRow } from '../PlaylistRow'
import type { PlexPlaylist } from '../../../../services/plexCollectionService'

const basePlaylist: PlexPlaylist = {
  id: 2,
  connection_id: 1,
  name: 'My Playlist',
  description: null,
  builder_config: {},
  plex_rating_key: null,
  last_synced_at: null,
  enabled: true,
  items: [],
}

describe('PlaylistRow', () => {
  it('renders the playlist name as a button', () => {
    render(
      <table><tbody>
        <PlaylistRow playlist={basePlaylist} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    expect(screen.getByRole('button', { name: /my playlist/i })).toBeInTheDocument()
  })

  it('calls onSelect when name is clicked', () => {
    const onSelect = vi.fn()
    render(
      <table><tbody>
        <PlaylistRow playlist={basePlaylist} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={onSelect} isSelected={false} />
      </tbody></table>
    )
    fireEvent.click(screen.getByRole('button', { name: /my playlist/i }))
    expect(onSelect).toHaveBeenCalledWith(2)
  })

  it('shows simple confirm dialog (no Plex checkbox) when Delete clicked', () => {
    render(
      <table><tbody>
        <PlaylistRow playlist={basePlaylist} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    expect(screen.getByText('Delete My Playlist?')).toBeInTheDocument()
    expect(screen.queryByRole('checkbox', { name: /plex/i })).not.toBeInTheDocument()
  })

  it('calls onDelete when confirmed', () => {
    const onDelete = vi.fn()
    render(
      <table><tbody>
        <PlaylistRow playlist={basePlaylist} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={onDelete} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    const dialog = screen.getByRole('dialog')
    fireEvent.click(within(dialog).getByRole('button', { name: /^delete$/i }))
    expect(onDelete).toHaveBeenCalledWith(2)
  })

  it('shows select checkbox in selectable mode', () => {
    const onBulkSelect = vi.fn()
    render(
      <table><tbody>
        <PlaylistRow playlist={basePlaylist} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={false} selectable onBulkSelect={onBulkSelect} bulkSelected={false} />
      </tbody></table>
    )
    expect(screen.getByRole('checkbox', { name: /select my playlist/i })).toBeInTheDocument()
  })
})
