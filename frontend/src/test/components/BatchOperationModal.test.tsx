import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { BatchOperationModal } from '@/components/file/BatchOperationModal'
import type { FileItem } from '@/types'

// Mock dependencies
vi.mock('@/stores/uiStore', () => ({
  useUIStore: vi.fn(() => ({
    addToast: vi.fn(),
  })),
}))

vi.mock('@/services/fileService', () => ({
  fileService: {
    deleteFile: vi.fn(),
    moveFile: vi.fn(),
    renameFile: vi.fn(),
  },
}))

describe('BatchOperationModal Component', () => {
  const mockFiles: FileItem[] = [
    { id: 'file-1', name: 'file1.mp4', path: '/videos', type: 'file', size: 1000, createdAt: '', updatedAt: '' },
    { id: 'file-2', name: 'file2.mp4', path: '/videos', type: 'file', size: 2000, createdAt: '', updatedAt: '' },
  ]

  const mockOnClose = vi.fn()
  const mockOnComplete = vi.fn()

  const renderModal = (props: Partial<Parameters<typeof BatchOperationModal>[0]> = {}) => {
    return render(
      <BatchOperationModal
        files={mockFiles}
        operation="delete"
        onClose={mockOnClose}
        onComplete={mockOnComplete}
        {...props}
      />
    )
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render batch delete operation', () => {
    renderModal({ operation: 'delete' })

    expect(screen.getByText('Batch delete')).toBeInTheDocument()
    expect(screen.getByText('2 files selected')).toBeInTheDocument()
  })

  it('should render batch move operation', () => {
    renderModal({ operation: 'move' })

    expect(screen.getByText('Batch move')).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Destination Path' })).toBeInTheDocument()
  })

  it('should render batch rename operation', () => {
    renderModal({ operation: 'rename' })

    expect(screen.getByText('Batch rename')).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Name Prefix' })).toBeInTheDocument()
  })

  it('should show warning for delete operation', () => {
    renderModal({ operation: 'delete' })

    expect(screen.getByText(/This action cannot be undone/)).toHaveClass('bg-red-50')
  })

  it('should list selected files', () => {
    renderModal()

    expect(screen.getByText('• file1.mp4')).toBeInTheDocument()
    expect(screen.getByText('• file2.mp4')).toBeInTheDocument()
  })

  it('should show "and X more" when files exceed limit', () => {
    const manyFiles = Array.from({ length: 10 }, (_, i) => ({
      id: `file-${i}`,
      name: `file${i}.mp4`,
      path: '/videos',
      type: 'file' as const,
      size: 1000,
      createdAt: '',
      updatedAt: '',
    }))

    renderModal({ files: manyFiles })

    expect(screen.getByText('... and 5 more')).toBeInTheDocument()
  })

  it('should call onClose when cancel is clicked', () => {
    renderModal()

    const cancelButton = screen.getByRole('button', { name: 'Cancel' })
    fireEvent.click(cancelButton)

    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('should disable execute button when operation is invalid', () => {
    renderModal({ operation: 'move' })

    const executeButton = screen.getByRole('button', { name: 'Execute' })
    expect(executeButton).toBeDisabled()
  })

  it('should enable execute button when move path is provided', () => {
    renderModal({ operation: 'move' })

    const pathInput = screen.getByRole('textbox', { name: 'Destination Path' })
    fireEvent.change(pathInput, { target: { value: '/new/path' } })

    const executeButton = screen.getByRole('button', { name: 'Execute' })
    expect(executeButton).not.toBeDisabled()
  })

  it('should enable execute button when rename prefix is provided', () => {
    renderModal({ operation: 'rename' })

    const prefixInput = screen.getByRole('textbox', { name: 'Name Prefix' })
    fireEvent.change(prefixInput, { target: { value: 'new_prefix' } })

    const executeButton = screen.getByRole('button', { name: 'Execute' })
    expect(executeButton).not.toBeDisabled()
  })

  it('should show progress during processing', async () => {
    const fileService = await import('@/services/fileService')
    fileService.fileService.deleteFile = vi.fn().mockResolvedValue({ success: true })

    renderModal({ operation: 'delete' })

    const executeButton = screen.getByRole('button', { name: 'Execute' })
    fireEvent.click(executeButton)

    await waitFor(() => {
      expect(screen.getByText('Processing...')).toBeInTheDocument()
    })
  })

  it('should close after successful operation', async () => {
    const fileService = await import('@/services/fileService')
    fileService.fileService.deleteFile = vi.fn().mockResolvedValue({ success: true })

    renderModal({ operation: 'delete' })

    const executeButton = screen.getByRole('button', { name: 'Execute' })
    fireEvent.click(executeButton)

    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalledTimes(1)
    })
  })

  it('should call onComplete after successful operation', async () => {
    const fileService = await import('@/services/fileService')
    fileService.fileService.deleteFile = vi.fn().mockResolvedValue({ success: true })

    renderModal({ operation: 'delete' })

    const executeButton = screen.getByRole('button', { name: 'Execute' })
    fireEvent.click(executeButton)

    await waitFor(() => {
      expect(mockOnComplete).toHaveBeenCalledTimes(1)
    })
  })
})
