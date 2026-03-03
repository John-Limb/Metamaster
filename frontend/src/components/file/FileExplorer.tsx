import React, { useState, useEffect } from 'react'
import { FaList, FaThLarge, FaTree, FaArrowLeft } from 'react-icons/fa'
import { useFileStore } from '@/stores/fileStore'
import { FileGrid } from './FileGrid'
import { FileList } from './FileList'
import { FileTree } from './FileTree'
import { FileContextMenu } from './FileContextMenu'
import { FileDetailsPanel } from './FileDetailsPanel'
import type { FileItem } from '@/types'

type ViewMode = 'grid' | 'list' | 'tree'

interface FileExplorerProps {
  onFileDoubleClick?: (file: FileItem) => void
  showDetailsPanel?: boolean
}

export const FileExplorer: React.FC<FileExplorerProps> = ({
  onFileDoubleClick,
  showDetailsPanel = true,
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [contextMenu, setContextMenu] = useState<{
    x: number
    y: number
    file: FileItem
  } | null>(null)
  const [selectedFileDetails, setSelectedFileDetails] = useState<FileItem | null>(null)

  const {
    files,
    selectedFiles,
    currentPath,
    isLoading,
    toggleFileSelection,
    clearSelection,
    navigateToPath,
    fetchFiles,
  } = useFileStore()

  // Fetch files when currentPath changes or on initial mount
  useEffect(() => {
    fetchFiles(currentPath).catch(() => {
      // Error is already stored in fileStore.error
    })
  }, [currentPath, fetchFiles])

  const handleSelectFile = (id: string) => {
    toggleFileSelection(id)
    const file = files.find((f) => f.id === id)
    if (file) {
      setSelectedFileDetails(selectedFiles.includes(id) ? null : file)
    }
  }

  const handleDoubleClick = (file: FileItem) => {
    if (file.type === 'directory') {
      navigateToPath(file.path)
      clearSelection()
      setSelectedFileDetails(null)
    } else {
      onFileDoubleClick?.(file)
    }
  }

  const handleContextMenu = (e: React.MouseEvent, file: FileItem) => {
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      file,
    })
  }

  const handleCloseContextMenu = () => {
    setContextMenu(null)
  }

  const handleNavigateBack = () => {
    const parts = currentPath.split('/').filter(Boolean)
    if (parts.length > 0) {
      parts.pop()
      const newPath = '/' + parts.join('/')
      navigateToPath(newPath)
      clearSelection()
      setSelectedFileDetails(null)
    }
  }

  useEffect(() => {
    const handleClickOutside = () => {
      handleCloseContextMenu()
    }

    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [])

  return (
    <div className="flex flex-col gap-4 h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-3">
        <div className="flex items-center gap-2 min-w-0">
          {currentPath !== '/' && (
            <button
              onClick={handleNavigateBack}
              className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition flex-shrink-0"
              title="Go back"
            >
              <FaArrowLeft className="w-4 h-4 text-slate-600 dark:text-slate-400" />
            </button>
          )}
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300 truncate">
            {currentPath}
          </span>
        </div>

        <div className="flex items-center gap-1 flex-shrink-0">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded-lg transition ${
              viewMode === 'grid'
                ? 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/50 dark:text-indigo-400'
                : 'hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400'
            }`}
            title="Grid view"
          >
            <FaThLarge className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded-lg transition ${
              viewMode === 'list'
                ? 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/50 dark:text-indigo-400'
                : 'hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400'
            }`}
            title="List view"
          >
            <FaList className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('tree')}
            className={`p-2 rounded-lg transition ${
              viewMode === 'tree'
                ? 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/50 dark:text-indigo-400'
                : 'hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400'
            }`}
            title="Tree view"
          >
            <FaTree className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex gap-4 flex-1 min-h-0">
        {/* File view */}
        <div className="flex-1 min-w-0 bg-white dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 rounded-lg overflow-auto">
          {viewMode === 'grid' && (
            <div className="p-4">
              <FileGrid
                files={files}
                selectedFiles={selectedFiles}
                onSelectFile={handleSelectFile}
                onDoubleClick={handleDoubleClick}
                onContextMenu={handleContextMenu}
                isLoading={isLoading}
              />
            </div>
          )}
          {viewMode === 'list' && (
            <FileList
              files={files}
              selectedFiles={selectedFiles}
              onSelectFile={handleSelectFile}
              onDoubleClick={handleDoubleClick}
              onContextMenu={handleContextMenu}
              isLoading={isLoading}
            />
          )}
          {viewMode === 'tree' && (
            <div className="p-4">
              <FileTree
                files={files}
                selectedFiles={selectedFiles}
                onSelectFile={handleSelectFile}
                onDoubleClick={handleDoubleClick}
                onContextMenu={handleContextMenu}
                isLoading={isLoading}
              />
            </div>
          )}
        </div>

        {/* Details panel */}
        {showDetailsPanel && selectedFileDetails && (
          <div className="w-72 flex-shrink-0 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg overflow-auto">
            <FileDetailsPanel file={selectedFileDetails} />
          </div>
        )}
      </div>

      {/* Context menu */}
      {contextMenu && (
        <FileContextMenu
          file={contextMenu.file}
          x={contextMenu.x}
          y={contextMenu.y}
          onClose={handleCloseContextMenu}
        />
      )}
    </div>
  )
}
