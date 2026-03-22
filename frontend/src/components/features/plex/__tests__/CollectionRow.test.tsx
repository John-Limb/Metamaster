import React from 'react'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { CollectionRow } from '../CollectionRow'
import type { PlexCollection } from '../../../../services/plexCollectionService'

const baseCollection: PlexCollection = {
  id: 1,
  connection_id: 1,
  name: 'Action Films',
  description: null,
  sort_title: null,
  builder_type: 'genre',
  builder_config: { genre: 'Action' },
  plex_rating_key: null,
  last_synced_at: null,
  enabled: false,
  is_default: false,
  items: [],
  content_type: 'movie',
}

describe('CollectionRow', () => {
  it('renders the collection name as a button', () => {
    render(
      <table><tbody>
        <CollectionRow collection={baseCollection} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    expect(screen.getByRole('button', { name: /action films/i })).toBeInTheDocument()
  })

  it('renders the builder type badge', () => {
    render(
      <table><tbody>
        <CollectionRow collection={baseCollection} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    expect(screen.getByText('Genre')).toBeInTheDocument()
  })

  it('calls onSelect when name button is clicked', () => {
    const onSelect = vi.fn()
    render(
      <table><tbody>
        <CollectionRow collection={baseCollection} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={onSelect} isSelected={false} />
      </tbody></table>
    )
    fireEvent.click(screen.getByRole('button', { name: /action films/i }))
    expect(onSelect).toHaveBeenCalledWith(1)
  })

  it('shows delete confirm dialog when Delete clicked', () => {
    render(
      <table><tbody>
        <CollectionRow collection={baseCollection} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    expect(screen.getByText('Delete Action Films?')).toBeInTheDocument()
  })

  it('calls onDelete with deleteFromPlex=false when no plex_rating_key', () => {
    const onDelete = vi.fn()
    render(
      <table><tbody>
        <CollectionRow collection={baseCollection} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={onDelete} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    const dialog = screen.getByRole('dialog')
    fireEvent.click(within(dialog).getByRole('button', { name: /^delete$/i }))
    expect(onDelete).toHaveBeenCalledWith(1, false)
  })

  it('shows "Also delete from Plex" checkbox when plex_rating_key is set', () => {
    const col = { ...baseCollection, plex_rating_key: 'rk-1' }
    render(
      <table><tbody>
        <CollectionRow collection={col} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={false} />
      </tbody></table>
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    expect(screen.getByRole('checkbox', { name: /also delete from plex/i })).toBeInTheDocument()
  })

  it('highlights the row when isSelected is true', () => {
    const { container } = render(
      <table><tbody>
        <CollectionRow collection={baseCollection} onToggleEnabled={vi.fn()} onPush={vi.fn()} onDelete={vi.fn()} onSelect={vi.fn()} isSelected={true} />
      </tbody></table>
    )
    const row = container.querySelector('tr')
    expect(row?.className).toMatch(/border-indigo/)
  })
})
