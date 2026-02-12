import React from 'react'
import { FileCard } from './FileCard'
import type { FileItem } from '@/types'

interface FileGridProps {
  files: FileItem[]
  selectedFiles: string[]
  onSelectFile: (id: string) => void
  onDoubleClick?: (file: FileItem) => void
  onContextMenu?: (e: React.MouseEvent, file: FileItem) => void
  isLoading?: boolean
  emptyMessage?: string
}

export const FileGrid: React.FC<FileGridProps> = ({
  files,
  selectedFiles,
  onSelectFile,
  onDoubleClick,
  onContextMenu,
  isLoading = false,
  emptyMessage = 'No files to display',
}) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (files.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-gray-500 text-lg">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
      {files.map((file) => (
        <FileCard
          key={file.id}
          file={file}
          isSelected={selectedFiles.includes(file.id)}
          onSelect={onSelectFile}
          onDoubleClick={onDoubleClick}
          onContextMenu={onContextMenu}
          viewMode="grid"
        />
      ))}
    </div>
  )
}
