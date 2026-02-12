import React, { useState, useEffect } from 'react'
import { FaPlay, FaPause, FaStop, FaSync } from 'react-icons/fa'
import { useUIStore } from '@/stores/uiStore'
import type { FileItem } from '@/types'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'
import { EmptyState } from '@/components/common/EmptyState'
import { ProgressBar } from '@/components/common/ProgressBar'

interface FileScannerProps {
  onScanComplete?: (files: FileItem[]) => void
  onScanError?: (error: string) => void
}

type ScanStatus = 'idle' | 'scanning' | 'paused' | 'completed' | 'error'

export const FileScanner: React.FC<FileScannerProps> = () => {
  const [status, setStatus] = useState<ScanStatus>('idle')
  const [progress, setProgress] = useState(0)
  const [filesFound, setFilesFound] = useState(0)
  const [currentPath, setCurrentPath] = useState('')
  const [recentFiles, setRecentFiles] = useState<FileItem[]>([])
  const [elapsedTime, setElapsedTime] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const { addToast } = useUIStore()

  // Simulate scan progress - would be replaced with real file scanner API
  useEffect(() => {
    if (status !== 'scanning') return

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          setStatus('completed')
          addToast({
            type: 'success',
            message: `Scan completed. Found ${filesFound} files.`,
          })
          return 100
        }
        return prev + Math.random() * 15
      })

      setFilesFound((prev) => prev + Math.floor(Math.random() * 5))
      setElapsedTime((prev) => prev + 1)
    }, 1000)

    return () => clearInterval(interval)
  }, [status, filesFound, addToast])

  const handleStartScan = () => {
    setStatus('scanning')
    setProgress(0)
    setFilesFound(0)
    setElapsedTime(0)
    setRecentFiles([])
    setCurrentPath('/')
    setError(null)
  }

  const handlePauseScan = () => {
    setStatus(status === 'paused' ? 'scanning' : 'paused')
  }

  const handleStopScan = () => {
    setStatus('idle')
    setProgress(0)
    setFilesFound(0)
    setElapsedTime(0)
    addToast({
      type: 'info',
      message: 'Scan stopped',
    })
  }

  const handleRetry = () => {
    setError(null)
    handleStartScan()
  }

  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`
    }
    if (minutes > 0) {
      return `${minutes}m ${secs}s`
    }
    return `${secs}s`
  }

  // Error state
  if (error && status !== 'scanning') {
    return (
      <Card variant="bordered" className="p-6">
        <EmptyState
          iconVariant="error"
          title="Scan Error"
          description={error}
          action={{
            label: 'Retry Scan',
            onClick: handleRetry,
            variant: 'primary',
          }}
          secondaryAction={{
            label: 'View Logs',
            onClick: () => window.location.href = '/settings?section=logs',
            variant: 'ghost',
          }}
        />
      </Card>
    )
  }

  return (
    <Card variant="bordered" className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold text-secondary-900 dark:text-white">File Scanner</h2>
        <p className="text-sm text-secondary-500 dark:text-secondary-400 mt-1">
          Scan your file system for new media files
        </p>
      </div>

      {/* Status Indicator */}
      <div className="flex items-center gap-3">
        <div
          className={`w-3 h-3 rounded-full ${
            status === 'scanning'
              ? 'bg-primary-500 animate-pulse'
              : status === 'completed'
                ? 'bg-green-500'
                : status === 'error'
                  ? 'bg-red-500'
                  : status === 'paused'
                    ? 'bg-yellow-500'
                    : 'bg-secondary-400'
          }`}
        ></div>
        <span className="text-sm font-medium text-secondary-700 dark:text-secondary-300 capitalize">
          {status === 'idle' ? 'Ready to scan' : status}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm text-secondary-600 dark:text-secondary-400">Progress</span>
          <span className="text-sm font-medium text-secondary-900 dark:text-white">
            {Math.round(progress)}%
          </span>
        </div>
        <ProgressBar
          value={progress}
          showLabel={false}
          variant={status === 'paused' ? 'warning' : 'default'}
          size="md"
        />
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-secondary-50 dark:bg-secondary-800 rounded-lg p-4">
          <p className="text-xs text-secondary-500 dark:text-secondary-400 uppercase font-semibold">
            Files Found
          </p>
          <p className="text-2xl font-bold text-secondary-900 dark:text-white mt-2">{filesFound}</p>
        </div>
        <div className="bg-secondary-50 dark:bg-secondary-800 rounded-lg p-4">
          <p className="text-xs text-secondary-500 dark:text-secondary-400 uppercase font-semibold">
            Elapsed Time
          </p>
          <p className="text-lg font-bold text-secondary-900 dark:text-white mt-2">
            {formatTime(elapsedTime)}
          </p>
        </div>
        <div className="bg-secondary-50 dark:bg-secondary-800 rounded-lg p-4">
          <p className="text-xs text-secondary-500 dark:text-secondary-400 uppercase font-semibold">
            Current Path
          </p>
          <p className="text-sm font-mono text-secondary-900 dark:text-white mt-2 truncate">
            {currentPath || '—'}
          </p>
        </div>
      </div>

      {/* Control Buttons */}
      <div className="flex gap-3">
        <Button
          variant="primary"
          onClick={handleStartScan}
          disabled={status === 'scanning'}
          leftIcon={<FaPlay />}
        >
          Start Scan
        </Button>
        <Button
          variant="secondary"
          onClick={handlePauseScan}
          disabled={status !== 'scanning' && status !== 'paused'}
          leftIcon={status === 'paused' ? <FaPlay /> : <FaPause />}
        >
          {status === 'paused' ? 'Resume' : 'Pause'}
        </Button>
        <Button
          variant="danger"
          onClick={handleStopScan}
          disabled={status === 'idle'}
          leftIcon={<FaStop />}
        >
          Stop
        </Button>
      </div>

      {/* Recently Discovered Files */}
      {recentFiles.length > 0 && (
        <div className="space-y-3 pt-6 border-t border-secondary-200 dark:border-secondary-700">
          <h3 className="text-sm font-semibold text-secondary-900 dark:text-white">
            Recently Discovered
          </h3>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {recentFiles.slice(0, 5).map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-2 p-2 bg-secondary-50 dark:bg-secondary-800 rounded"
              >
                <FaSync className="w-3 h-3 text-secondary-400 flex-shrink-0" />
                <span className="text-sm text-secondary-700 dark:text-secondary-300 truncate">
                  {file.name}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State - Idle */}
      {status === 'idle' && filesFound === 0 && !error && (
        <EmptyState
          iconVariant="featureDisabled"
          title="Configure file monitoring"
          description="Set up your media library paths to start discovering files"
          action={{
            label: 'Configure Paths',
            onClick: () => window.location.href = '/settings?section=paths',
            variant: 'secondary',
          }}
        />
      )}

      {/* Completion State */}
      {status === 'completed' && filesFound > 0 && (
        <EmptyState
          iconVariant="noData"
          title="Scan Complete"
          description={`Found ${filesFound} files during the scan. Review and add them to your library.`}
          action={{
            label: 'Review Files',
            onClick: () => window.location.href = '/files',
            variant: 'primary',
          }}
          secondaryAction={{
            label: 'Scan Again',
            onClick: handleStartScan,
            variant: 'ghost',
          }}
        />
      )}
    </Card>
  )
}
