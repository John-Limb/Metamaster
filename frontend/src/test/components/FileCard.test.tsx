import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { FileCard } from '@/components/file/FileCard'
import type { FileItem } from '@/types'

describe('FileCard Component', () => {
  const mockFile: FileItem = {
    id: 'file-1',
    name: 'test-video.mp4',
    path: '/videos',
    type: 'file',
    size: 1073741824,
    mimeType: 'video/mp4',
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z',
  }

  const mockOnSelect = vi.fn()
  const mockOnDoubleClick = vi.fn()
  const mockOnContextMenu = vi.fn()

  const renderFileCard = (props: Partial<Parameters<typeof FileCard>[0]> = {}) => {
    return render(
      <FileCard
        file={mockFile}
        onSelect={mockOnSelect}
        onDoubleClick={mockOnDoubleClick}
        onContextMenu={mockOnContextMenu}
        {...props}
      />
    )
  }

  it('should render file name', () => {
    renderFileCard()

    expect(screen.getByText('test-video.mp4')).toBeInTheDocument()
  })

  it('should render video icon for video files', () => {
    renderFileCard()

    expect(screen.getByTestId('video-icon')).toBeInTheDocument()
  })

  it('should show selected state when isSelected is true', () => {
    renderFileCard({ isSelected: true })

    expect(screen.getByTestId('file-card')).toHaveClass('border-blue-500')
    expect(screen.getByTestId('file-card')).toHaveClass('bg-blue-50')
  })

  it('should show unselected state when isSelected is false', () => {
    renderFileCard({ isSelected: false })

    expect(screen.getByTestId('file-card')).toHaveClass('border-gray-200')
  })

  it('should call onSelect when clicked', () => {
    renderFileCard()

    const card = screen.getByTestId('file-card')
    fireEvent.click(card)

    expect(mockOnSelect).toHaveBeenCalledWith('file-1')
  })

  it('should call onDoubleClick when double clicked', () => {
    renderFileCard()

    const card = screen.getByTestId('file-card')
    fireEvent.doubleClick(card)

    expect(mockOnDoubleClick).toHaveBeenCalledWith(mockFile)
  })

  it('should call onContextMenu when right clicked', () => {
    renderFileCard()

    const card = screen.getByTestId('file-card')
    fireEvent.contextMenu(card)

    expect(mockOnContextMenu).toHaveBeenCalled()
  })

  it('should render checkbox', () => {
    renderFileCard()

    expect(screen.getByRole('checkbox')).toBeInTheDocument()
  })

  it('should render file size', () => {
    renderFileCard()

    expect(screen.getByText('1 GB')).toBeInTheDocument()
  })

  it('should render file date', () => {
    renderFileCard()

    expect(screen.getByText(/Jan/)).toBeInTheDocument()
  })

  it('should render in list view', () => {
    renderFileCard({ viewMode: 'list' })

    expect(screen.getByTestId('file-list-item')).toBeInTheDocument()
  })

  it('should render in grid view', () => {
    renderFileCard({ viewMode: 'grid' })

    expect(screen.getByTestId('file-card')).toBeInTheDocument()
  })

  it('should render folder icon for directories', () => {
    const folderFile: FileItem = {
      ...mockFile,
      type: 'directory',
      mimeType: undefined,
      name: 'My Folder',
    }

    renderFileCard({ file: folderFile })

    expect(screen.getByTestId('folder-icon')).toBeInTheDocument()
  })

  it('should render image icon for image files', () => {
    const imageFile: FileItem = {
      ...mockFile,
      name: 'photo.jpg',
      mimeType: 'image/jpeg',
    }

    renderFileCard({ file: imageFile })

    expect(screen.getByTestId('image-icon')).toBeInTheDocument()
  })

  it('should render audio icon for audio files', () => {
    const audioFile: FileItem = {
      ...mockFile,
      name: 'song.mp3',
      mimeType: 'audio/mpeg',
    }

    renderFileCard({ file: audioFile })

    expect(screen.getByTestId('audio-icon')).toBeInTheDocument()
  })

  it('should render archive icon for archive files', () => {
    const archiveFile: FileItem = {
      ...mockFile,
      name: 'archive.zip',
    }

    renderFileCard({ file: archiveFile })

    expect(screen.getByTestId('archive-icon')).toBeInTheDocument()
  })

  it('should render default file icon for unknown types', () => {
    const unknownFile: FileItem = {
      ...mockFile,
      name: 'file.xyz',
    }

    renderFileCard({ file: unknownFile })

    expect(screen.getByTestId('file-icon')).toBeInTheDocument()
  })
})
