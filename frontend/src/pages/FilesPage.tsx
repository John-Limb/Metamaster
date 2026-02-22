import React, { useState } from 'react'
import { FileExplorer, FileScanner } from '@/components/file'

export const FilesPage: React.FC = () => {
  const [showScanner, setShowScanner] = useState(false)

  return (
    <div className="h-full flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Files</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">Browse and manage your media files</p>
        </div>
        <button
          onClick={() => setShowScanner((s) => !s)}
          className="text-sm px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
        >
          {showScanner ? 'Hide Scanner' : 'Show Scanner'}
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 min-h-0 flex flex-col gap-4">
        <div className="flex-1 min-h-0">
          <FileExplorer showDetailsPanel={true} />
        </div>
        {showScanner && (
          <div>
            <FileScanner />
          </div>
        )}
      </div>
    </div>
  )
}
