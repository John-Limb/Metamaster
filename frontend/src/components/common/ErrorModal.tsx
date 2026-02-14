import React from 'react'
import { FaExclamationCircle, FaTimes } from 'react-icons/fa'

interface ErrorModalProps {
  isOpen: boolean
  title?: string
  message: string
  details?: string
  onClose: () => void
  onRetry?: () => void | Promise<void>
  isRetrying?: boolean
}

export const ErrorModal: React.FC<ErrorModalProps> = ({
  isOpen,
  title = 'Error',
  message,
  details,
  onClose,
  onRetry,
  isRetrying = false,
}) => {
  if (!isOpen) return null

  const handleRetry = async () => {
    if (onRetry) {
      await onRetry()
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div className="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 animate-slide-in">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-900/30 rounded-t-lg">
          <div className="flex items-center gap-3">
            <FaExclamationCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
            <h2 className="text-lg font-semibold text-red-900 dark:text-red-300">{title}</h2>
          </div>
          <button
            onClick={onClose}
            className="text-red-400 hover:text-red-600 dark:hover:text-red-300 transition"
            aria-label="Close error modal"
          >
            <FaTimes className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-gray-700 dark:text-gray-300 text-sm font-medium mb-3">{message}</p>
          {details && (
            <details className="text-xs text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 p-3 rounded border border-gray-200 dark:border-gray-600">
              <summary className="cursor-pointer font-semibold text-gray-700 dark:text-gray-300 mb-2">
                Error Details
              </summary>
              <pre className="overflow-auto max-h-40 whitespace-pre-wrap break-words">
                {details}
              </pre>
            </details>
          )}
        </div>

        {/* Footer */}
        <div className="flex gap-3 p-6 border-t border-gray-200 dark:border-gray-700 justify-end">
          <button
            onClick={onClose}
            disabled={isRetrying}
            className="px-4 py-2 text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            Close
          </button>
          {onRetry && (
            <button
              onClick={handleRetry}
              disabled={isRetrying}
              className="px-4 py-2 text-white bg-red-600 rounded-lg hover:bg-red-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {isRetrying ? 'Retrying...' : 'Retry'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
