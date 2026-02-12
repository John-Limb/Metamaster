import React from 'react'
import { FileCard } from './FileCard'
import type { FileItem } from '@/types'

interface FileListProps {
  files: FileItem[]
  selectedFiles: string[]
  onSelectFile: (id: string) => void
  onDoubleClick?: (file: FileItem) => void
  onContextMenu?: (e: React.MouseEvent, file: FileItem) => void
  isLoading?: boolean
  emptyMessage?: string
}

export const FileList: React.FC<FileListProps> = ({
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
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="grid grid-cols-12 gap-4 px-4 py-3 bg-gray-50 border-b border-gray-200 font-semibold text-sm text-gray-700">
        <div className="col-span-1">
          <input
            type="checkbox"
            checked={selectedFiles.length === files.length && files.length > 0}
            onChange={(e) => {
              if (e.target.checked) {
                // Select all
              } else {
                // Deselect all
              }
            }}
            className="w-4 h-4 rounded border-gray-300"
          />
        </div>
        <div className="col-span-6">Name</div>
        <div className="col-span-2">Size</div>
        <div className="col-span-3">Modified</div>
      </div>

      {/* File rows */}
      <div className="divide-y divide-gray-200">
        {files.map((file) => (
          <FileCard
            key={file.id}
            file={file}
            isSelected={selectedFiles.includes(file.id)}
            onSelect={onSelectFile}
            onDoubleClick={onDoubleClick}
            onContextMenu={onContextMenu}
            viewMode="list"
          />
        ))}
      </div>
    </div>
  )
}
