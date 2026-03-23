import React from 'react'
import { FileCard } from './FileCard'
import { CheckboxInput } from '@/components/common'
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
}: FileListProps) => {
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
        <p className="text-hint text-lg">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-edge overflow-hidden">
      {/* Header */}
      <div className="grid grid-cols-12 gap-4 px-4 py-3 bg-subtle border-b border-edge font-semibold text-sm text-dim">
        <div className="col-span-1">
          <CheckboxInput
            checked={selectedFiles.length === files.length && files.length > 0}
            indeterminate={selectedFiles.length > 0 && selectedFiles.length < files.length}
            onChange={(checked) => {
              if (checked) {
                // Select all
              } else {
                // Deselect all
              }
            }}
          />
        </div>
        <div className="col-span-6">Name</div>
        <div className="col-span-2">Size</div>
        <div className="col-span-3">Modified</div>
      </div>

      {/* File rows */}
      <div className="divide-y divide-edge">
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
