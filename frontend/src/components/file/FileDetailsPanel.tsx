import React from 'react'
import { FaFile, FaFolder, FaClock, FaDatabase } from 'react-icons/fa'
import type { FileItem } from '@/types'

interface FileDetailsPanelProps {
  file: FileItem
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
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export const FileDetailsPanel: React.FC<FileDetailsPanelProps> = ({ file }: FileDetailsPanelProps) => {
  const isDirectory = file.type === 'directory'

  return (
    <div className="p-6 space-y-6">
      {/* File Icon and Name */}
      <div className="flex flex-col items-center gap-4 pb-6 border-b border-edge">
        <div className="text-6xl">
          {isDirectory ? (
            <FaFolder className="text-blue-500" />
          ) : (
            <FaFile className="text-hint" />
          )}
        </div>
        <div className="text-center">
          <h3 className="text-lg font-semibold text-body break-words">{file.name}</h3>
          <p className="text-sm text-hint mt-1">{file.type}</p>
        </div>
      </div>

      {/* File Properties */}
      <div className="space-y-4">
        <h4 className="text-sm font-semibold text-body">Properties</h4>

        {/* Path */}
        <div>
          <label className="text-xs font-medium text-hint uppercase">Path</label>
          <p className="text-sm text-body break-all mt-1">{file.path}</p>
        </div>

        {/* File ID */}
        <div>
          <label className="text-xs font-medium text-hint uppercase">ID</label>
          <p className="text-sm text-body font-mono break-all mt-1">{file.id}</p>
        </div>

        {/* Size */}
        <div className="flex items-center gap-2">
          <FaDatabase className="w-4 h-4 text-hint" />
          <div className="flex-1">
            <label className="text-xs font-medium text-hint uppercase">Size</label>
            <p className="text-sm text-body mt-1">{formatFileSize(file.size)}</p>
          </div>
        </div>

        {/* MIME Type */}
        {file.mimeType && (
          <div>
            <label className="text-xs font-medium text-hint uppercase">MIME Type</label>
            <p className="text-sm text-body mt-1">{file.mimeType}</p>
          </div>
        )}

        {/* Created Date */}
        <div className="flex items-center gap-2">
          <FaClock className="w-4 h-4 text-hint" />
          <div className="flex-1">
            <label className="text-xs font-medium text-hint uppercase">Created</label>
            <p className="text-sm text-body mt-1">{formatDate(file.createdAt)}</p>
          </div>
        </div>

        {/* Modified Date */}
        <div className="flex items-center gap-2">
          <FaClock className="w-4 h-4 text-hint" />
          <div className="flex-1">
            <label className="text-xs font-medium text-hint uppercase">Modified</label>
            <p className="text-sm text-body mt-1">{formatDate(file.updatedAt)}</p>
          </div>
        </div>

        {/* Indexed Status */}
        <div>
          <label className="text-xs font-medium text-hint uppercase">Indexed</label>
          <p className="text-sm text-body mt-1">
            {file.isIndexed ? (
              <span className="inline-flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                Yes
              </span>
            ) : (
              <span className="inline-flex items-center gap-2">
                <span className="w-2 h-2 bg-hint rounded-full"></span>
                No
              </span>
            )}
          </p>
        </div>
      </div>

      {/* Metadata */}
      {file.metadata && Object.keys(file.metadata).length > 0 && (
        <div className="space-y-4 pt-6 border-t border-edge">
          <h4 className="text-sm font-semibold text-body">Metadata</h4>
          <div className="space-y-3">
            {Object.entries(file.metadata).map(([key, value]) => (
              <div key={key}>
                <label className="text-xs font-medium text-hint uppercase">{key}</label>
                <p className="text-sm text-body mt-1 break-words">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
