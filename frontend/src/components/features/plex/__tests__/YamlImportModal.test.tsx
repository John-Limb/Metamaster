import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { YamlImportModal } from '../YamlImportModal'
import * as service from '../../../../services/plexCollectionService'

vi.mock('../../../../services/plexCollectionService', () => ({
  importYaml: vi.fn(),
}))

describe('YamlImportModal', () => {
  const onClose = vi.fn()
  const onImported = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders "Import Kometa YAML" title', () => {
    render(<YamlImportModal onClose={onClose} onImported={onImported} />)
    expect(screen.getByText('Import Kometa YAML')).toBeInTheDocument()
  })

  it('shows error on failed import', async () => {
    vi.mocked(service.importYaml).mockRejectedValueOnce(new Error('Invalid YAML: bad syntax'))

    render(<YamlImportModal onClose={onClose} onImported={onImported} />)

    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'bad: [yaml' } })
    fireEvent.click(screen.getByRole('button', { name: /import/i }))

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(screen.getByRole('alert')).toHaveTextContent('Invalid YAML: bad syntax')
    })

    expect(onClose).not.toHaveBeenCalled()
    expect(onImported).not.toHaveBeenCalled()
  })

  it('calls onClose and onImported on successful import', async () => {
    vi.mocked(service.importYaml).mockResolvedValueOnce({
      collections_created: ['Test Collection'],
      playlists_created: [],
    })

    render(<YamlImportModal onClose={onClose} onImported={onImported} />)

    fireEvent.change(screen.getByRole('textbox'), {
      target: {
        value: 'collections:\n  Test Collection:\n    builder:\n      builder_type: genre\n      genre: Action',
      },
    })
    fireEvent.click(screen.getByRole('button', { name: /import/i }))

    await waitFor(() => {
      expect(onImported).toHaveBeenCalledOnce()
      expect(onClose).toHaveBeenCalledOnce()
    })
  })
})
