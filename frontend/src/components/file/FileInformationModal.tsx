import React from 'react'
import { FaTimes, FaFolder } from 'react-icons/fa'
import { FilePreview } from './FilePreview'
import type { FileItem } from '@/types'

interface FileInformationModalProps {
  file: FileItem
  onClose: () => void
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

export const FileInformationModal: React.FC<FileInformationModalProps> = ({ file, onClose }) => {
  const isDirectory = file.type === 'directory'

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 sticky top-0 bg-white">
          <h2 className="text-xl font-semibold text-gray-900">File Information</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition"
          >
            <FaTimes className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Preview Section */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-900">Preview</h3>
            {!isDirectory ? (
              <FilePreview file={file} maxWidth={300} maxHeight={250} />
            ) : (
              <div className="flex items-center justify-center bg-gray-100 rounded-lg p-12">
                <FaFolder className="w-16 h-16 text-blue-500" />
              </div>
            )}
          </div>

          {/* Basic Information */}
          <div className="space-y-3 pt-6 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900">Basic Information</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase">Name</label>
                <p className="text-sm text-gray-900 mt-1 break-words">{file.name}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase">Type</label>
                <p className="text-sm text-gray-900 mt-1 capitalize">{file.type}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase">Size</label>
                <p className="text-sm text-gray-900 mt-1">{formatFileSize(file.size)}</p>
              </div>
              {file.mimeType && (
                <div>
                  <label className="text-xs font-medium text-gray-500 uppercase">MIME Type</label>
                  <p className="text-sm text-gray-900 mt-1">{file.mimeType}</p>
                </div>
              )}
            </div>
          </div>

          {/* Path Information */}
          <div className="space-y-3 pt-6 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900">Path Information</h3>
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase">Full Path</label>
              <p className="text-sm text-gray-900 mt-1 break-all font-mono bg-gray-50 p-3 rounded">
                {file.path}
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500 uppercase">File ID</label>
              <p className="text-sm text-gray-900 mt-1 break-all font-mono bg-gray-50 p-3 rounded">
                {file.id}
              </p>
            </div>
          </div>

          {/* Dates */}
          <div className="space-y-3 pt-6 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900">Dates</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase">Created</label>
                <p className="text-sm text-gray-900 mt-1">{formatDate(file.createdAt)}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase">Modified</label>
                <p className="text-sm text-gray-900 mt-1">{formatDate(file.updatedAt)}</p>
              </div>
            </div>
          </div>

          {/* Indexing Status */}
          <div className="space-y-3 pt-6 border-t border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900">Indexing Status</h3>
            <div className="flex items-center gap-3 bg-gray-50 p-4 rounded-lg">
              <div
                className={`w-3 h-3 rounded-full ${file.isIndexed ? 'bg-green-500' : 'bg-gray-400'}`}
              ></div>
              <span className="text-sm text-gray-700">
                {file.isIndexed ? 'Indexed' : 'Not indexed'}
              </span>
            </div>
          </div>

          {/* Metadata */}
          {file.metadata && Object.keys(file.metadata).length > 0 && (
            <div className="space-y-3 pt-6 border-t border-gray-200">
              <h3 className="text-sm font-semibold text-gray-900">Metadata</h3>
              <div className="space-y-3">
                {Object.entries(file.metadata).map(([key, value]) => (
                  <div key={key}>
                    <label className="text-xs font-medium text-gray-500 uppercase">{key}</label>
                    <p className="text-sm text-gray-900 mt-1 break-words bg-gray-50 p-3 rounded font-mono">
                      {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-gray-200 sticky bottom-0 bg-white">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300 transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
