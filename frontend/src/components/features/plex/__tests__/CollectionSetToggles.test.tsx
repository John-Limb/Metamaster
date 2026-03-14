import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CollectionSetToggles } from '../CollectionSetToggles'
import { usePlexCollectionStore } from '../../../../stores/plexCollectionStore'

vi.mock('../../../../stores/plexCollectionStore')

const mockToggleCollectionSet = vi.fn()

const defaultSets = [
  { id: 1, connection_id: 1, set_type: 'franchise' as const, enabled: true, last_run_at: null },
  { id: 2, connection_id: 1, set_type: 'genre' as const, enabled: false, last_run_at: '2024-01-15T10:00:00Z' },
  { id: 3, connection_id: 1, set_type: 'decade' as const, enabled: true, last_run_at: null },
]

beforeEach(() => {
  vi.mocked(usePlexCollectionStore).mockReturnValue({
    collectionSets: defaultSets,
    setsLoading: false,
    toggleCollectionSet: mockToggleCollectionSet,
  } as ReturnType<typeof usePlexCollectionStore>)
  mockToggleCollectionSet.mockClear()
})

describe('CollectionSetToggles', () => {
  it('renders all 3 set type labels', () => {
    render(<CollectionSetToggles />)
    expect(screen.getByText('Franchise')).toBeInTheDocument()
    expect(screen.getByText('Genre')).toBeInTheDocument()
    expect(screen.getByText('Decade')).toBeInTheDocument()
  })

  it('shows enabled state correctly', () => {
    render(<CollectionSetToggles />)
    const checkboxes = screen.getAllByRole('checkbox')
    // franchise: enabled=true
    expect(checkboxes[0]).toBeChecked()
    // genre: enabled=false
    expect(checkboxes[1]).not.toBeChecked()
    // decade: enabled=true
    expect(checkboxes[2]).toBeChecked()
  })

  it('calls toggleCollectionSet when toggle clicked', () => {
    render(<CollectionSetToggles />)
    const checkboxes = screen.getAllByRole('checkbox')
    // Click the genre checkbox (currently unchecked → enable it)
    fireEvent.click(checkboxes[1])
    expect(mockToggleCollectionSet).toHaveBeenCalledWith('genre', true)
  })
})
