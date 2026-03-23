import React from 'react'
import { FaFile, FaFolder, FaImage, FaVideo, FaMusic, FaFileArchive } from 'react-icons/fa'
import { CheckboxInput } from '@/components/common'
import type { FileItem } from '@/types'

interface FileCardProps {
  file: FileItem
  isSelected?: boolean
  onSelect?: (id: string) => void
  onDoubleClick?: (file: FileItem) => void
  onContextMenu?: (e: React.MouseEvent, file: FileItem) => void
  viewMode?: 'grid' | 'list'
}

const getFileIcon = (file: FileItem) => {
  if (file.type === 'directory') {
    return <FaFolder className="w-8 h-8 text-blue-500" />
  }

  const mimeType = file.mimeType || ''
  const name = file.name.toLowerCase()

  if (mimeType.startsWith('image/') || name.match(/\.(jpg|jpeg|png|gif|webp|svg)$/)) {
    return <FaImage className="w-8 h-8 text-purple-500" />
  }
  if (mimeType.startsWith('video/') || name.match(/\.(mp4|mkv|avi|mov|flv|wmv)$/)) {
    return <FaVideo className="w-8 h-8 text-red-500" />
  }
  if (mimeType.startsWith('audio/') || name.match(/\.(mp3|wav|flac|aac|ogg)$/)) {
    return <FaMusic className="w-8 h-8 text-green-500" />
  }
  if (name.match(/\.(zip|rar|7z|tar|gz)$/)) {
    return <FaFileArchive className="w-8 h-8 text-orange-500" />
  }

  return <FaFile className="w-8 h-8 text-hint" />
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export const FileCard: React.FC<FileCardProps> = ({
  file,
  isSelected = false,
  onSelect,
  onDoubleClick,
  onContextMenu,
  viewMode = 'grid',
}) => {
  const handleClick = (e: React.MouseEvent) => {
    if (e.ctrlKey || e.metaKey) {
      onSelect?.(file.id)
    } else if (e.shiftKey) {
      onSelect?.(file.id)
    } else {
      onSelect?.(file.id)
    }
  }

  const handleDoubleClick = () => {
    onDoubleClick?.(file)
  }

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault()
    onContextMenu?.(e, file)
  }

  if (viewMode === 'list') {
    return (
      <div
        className={`flex items-center gap-4 px-4 py-3 border-b border-edge cursor-pointer transition ${
          isSelected
            ? 'bg-primary-50 dark:bg-primary-900/20'
            : 'hover:bg-subtle'
        }`}
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
        onContextMenu={handleContextMenu}
      >
        <CheckboxInput
          checked={isSelected ?? false}
          onChange={() => onSelect?.(file.id)}
          onClick={(e) => e.stopPropagation()}
        />
        <div className="flex-shrink-0">{getFileIcon(file)}</div>
        <div className="flex-grow min-w-0">
          <p className="text-sm font-medium text-body truncate">{file.name}</p>
          <p className="text-xs text-hint">{formatDate(file.updatedAt)}</p>
        </div>
        <div className="flex-shrink-0 text-right">
          <p className="text-sm text-dim">{formatFileSize(file.size)}</p>
          <p className="text-xs text-hint">{file.type}</p>
        </div>
      </div>
    )
  }

  // Grid view
  return (
    <div
      className={`p-4 rounded-lg border-2 transition cursor-pointer ${
        isSelected
          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
          : 'border-edge hover:border-edge bg-card'
      }`}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      onContextMenu={handleContextMenu}
    >
      <div className="flex flex-col items-center gap-3">
        <div className="flex-shrink-0">{getFileIcon(file)}</div>
        <div className="text-center min-w-0 w-full">
          <p className="text-sm font-medium text-body truncate" title={file.name}>
            {file.name}
          </p>
          <p className="text-xs text-hint mt-1">{formatFileSize(file.size)}</p>
          <p className="text-xs text-hint">{formatDate(file.updatedAt)}</p>
        </div>
        <CheckboxInput
          checked={isSelected ?? false}
          onChange={() => onSelect?.(file.id)}
          onClick={(e) => e.stopPropagation()}
        />
      </div>
    </div>
  )
}
