import React, { useState } from 'react'
import { FaTrash, FaArrowRight, FaEdit, FaTimes } from 'react-icons/fa'
import { useUIStore } from '@/stores/uiStore'
import { fileService } from '@/services/fileService'
import type { FileItem } from '@/types'

interface BatchOperationModalProps {
  files: FileItem[]
  operation: 'delete' | 'move' | 'rename'
  onClose: () => void
  onComplete?: () => void
}

export const BatchOperationModal: React.FC<BatchOperationModalProps> = ({
  files,
  operation,
  onClose,
  onComplete,
}) => {
  const [isProcessing, setIsProcessing] = useState(false)
  const [newPath, setNewPath] = useState('')
  const [newNamePrefix, setNewNamePrefix] = useState('')
  const [progress, setProgress] = useState(0)

  const { addToast } = useUIStore()

  const handleExecute = async () => {
    if (files.length === 0) return

    setIsProcessing(true)
    let completed = 0
    let failed = 0

    try {
      for (const file of files) {
        try {
          if (operation === 'delete') {
            await fileService.deleteFile(file.id)
          } else if (operation === 'move' && newPath) {
            await fileService.moveFile(file.id, newPath)
          } else if (operation === 'rename' && newNamePrefix) {
            const newName = `${newNamePrefix}_${file.name}`
            await fileService.renameFile(file.id, newName)
          }
          completed++
        } catch (error) {
          failed++
        }
        setProgress(Math.round(((completed + failed) / files.length) * 100))
      }

      addToast({
        type: 'success',
        message: `Batch ${operation} completed. ${completed} succeeded, ${failed} failed.`,
      })

      onComplete?.()
      onClose()
    } catch (error) {
      addToast({
        type: 'error',
        message: `Batch ${operation} failed`,
      })
    } finally {
      setIsProcessing(false)
    }
  }

  const isValid =
    operation === 'delete' ||
    (operation === 'move' && newPath) ||
    (operation === 'rename' && newNamePrefix)

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4 p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {operation === 'delete' && <FaTrash className="w-5 h-5 text-red-600" />}
            {operation === 'move' && <FaArrowRight className="w-5 h-5 text-blue-600" />}
            {operation === 'rename' && <FaEdit className="w-5 h-5 text-yellow-600" />}
            <h2 className="text-lg font-semibold text-gray-900 capitalize">
              Batch {operation}
            </h2>
          </div>
          <button
            onClick={onClose}
            disabled={isProcessing}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <FaTimes className="w-5 h-5" />
          </button>
        </div>

        {/* File Count */}
        <div className="bg-gray-50 rounded-lg p-4">
          <p className="text-sm text-gray-600">
            {files.length} file{files.length !== 1 ? 's' : ''} selected
          </p>
          <div className="mt-2 space-y-1 max-h-32 overflow-y-auto">
            {files.slice(0, 5).map((file) => (
              <p key={file.id} className="text-xs text-gray-700 truncate">
                • {file.name}
              </p>
            ))}
            {files.length > 5 && (
              <p className="text-xs text-gray-500">... and {files.length - 5} more</p>
            )}
          </div>
        </div>

        {/* Operation-specific inputs */}
        {operation === 'move' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Destination Path
            </label>
            <input
              type="text"
              value={newPath}
              onChange={(e) => setNewPath(e.target.value)}
              placeholder="/path/to/destination"
              disabled={isProcessing}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            />
          </div>
        )}

        {operation === 'rename' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Name Prefix
            </label>
            <input
              type="text"
              value={newNamePrefix}
              onChange={(e) => setNewNamePrefix(e.target.value)}
              placeholder="new_prefix"
              disabled={isProcessing}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            />
            <p className="text-xs text-gray-500 mt-2">
              Files will be renamed to: prefix_filename
            </p>
          </div>
        )}

        {operation === 'delete' && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-sm text-red-800">
              This action cannot be undone. Are you sure you want to delete these files?
            </p>
          </div>
        )}

        {/* Progress Bar */}
        {isProcessing && (
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Progress</span>
              <span className="text-sm font-medium text-gray-900">{progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
              <div
                className="bg-blue-500 h-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-4 border-t border-gray-200">
          <button
            onClick={onClose}
            disabled={isProcessing}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition"
          >
            Cancel
          </button>
          <button
            onClick={handleExecute}
            disabled={!isValid || isProcessing}
            className={`flex-1 px-4 py-2 text-white rounded-lg transition disabled:opacity-50 ${
              operation === 'delete'
                ? 'bg-red-600 hover:bg-red-700'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {isProcessing ? 'Processing...' : 'Execute'}
          </button>
        </div>
      </div>
    </div>
  )
}
