import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { CollectionCard } from '../CollectionCard'
import type { PlexCollection } from '../../../../services/plexCollectionService'

const baseCollection: PlexCollection = {
  id: 1,
  connection_id: 1,
  name: 'My Collection',
  description: null,
  sort_title: null,
  builder_type: 'static_items',
  builder_config: {},
  plex_rating_key: null,
  last_synced_at: null,
  enabled: true,
  is_default: false,
  items: [],
  content_type: 'movie',
}

describe('CollectionCard delete modal', () => {
  it('shows confirmation modal when Delete clicked', () => {
    const onDelete = vi.fn()
    render(
      <CollectionCard
        collection={baseCollection}
        onToggleEnabled={vi.fn()}
        onPush={vi.fn()}
        onDelete={onDelete}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    expect(screen.getByText((content, element) => element?.textContent === 'Delete My Collection?')).toBeInTheDocument()
    expect(onDelete).not.toHaveBeenCalled()
  })

  it('does not show Plex checkbox when plex_rating_key is null', () => {
    render(
      <CollectionCard
        collection={baseCollection}
        onToggleEnabled={vi.fn()}
        onPush={vi.fn()}
        onDelete={vi.fn()}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    expect(screen.queryByRole('checkbox', { name: /delete from plex/i })).not.toBeInTheDocument()
  })

  it('shows checked Plex checkbox when plex_rating_key is set', () => {
    const col = { ...baseCollection, plex_rating_key: 'plex-123' }
    render(
      <CollectionCard
        collection={col}
        onToggleEnabled={vi.fn()}
        onPush={vi.fn()}
        onDelete={vi.fn()}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    const checkbox = screen.getByRole('checkbox', { name: /delete from plex/i }) as HTMLInputElement
    expect(checkbox.checked).toBe(true)
  })

  it('calls onDelete with deleteFromPlex=false when no Plex key', () => {
    const onDelete = vi.fn()
    render(
      <CollectionCard
        collection={baseCollection}
        onToggleEnabled={vi.fn()}
        onPush={vi.fn()}
        onDelete={onDelete}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    fireEvent.click(screen.getByRole('button', { name: /^delete$/i }))
    expect(onDelete).toHaveBeenCalledWith(1, false)
  })

  it('calls onDelete with deleteFromPlex=true when Plex key set and checkbox checked', () => {
    const col = { ...baseCollection, plex_rating_key: 'plex-123' }
    const onDelete = vi.fn()
    render(
      <CollectionCard
        collection={col}
        onToggleEnabled={vi.fn()}
        onPush={vi.fn()}
        onDelete={onDelete}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    fireEvent.click(screen.getByRole('button', { name: /^delete$/i }))
    expect(onDelete).toHaveBeenCalledWith(1, true)
  })

  it('Cancel closes the modal without calling onDelete', () => {
    const onDelete = vi.fn()
    render(
      <CollectionCard
        collection={baseCollection}
        onToggleEnabled={vi.fn()}
        onPush={vi.fn()}
        onDelete={onDelete}
      />
    )
    fireEvent.click(screen.getByRole('button', { name: /delete/i }))
    fireEvent.click(screen.getByRole('button', { name: /cancel/i }))
    expect(onDelete).not.toHaveBeenCalled()
    expect(screen.queryByText((content, element) => element?.textContent === 'Delete My Collection?')).not.toBeInTheDocument()
  })
})
