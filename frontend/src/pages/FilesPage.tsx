import React, { useState } from 'react'
import { FileExplorer, FileScanner } from '@/components/file'

export const FilesPage: React.FC = () => {
  const [showScanner, setShowScanner] = useState(false)

  return (
    <div className="h-full flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-body">Files</h1>
          <p className="text-hint mt-1">Browse and manage your media files</p>
        </div>
        <button
          onClick={() => setShowScanner((s) => !s)}
          className="text-sm px-3 py-1.5 rounded-lg border border-edge text-dim hover:bg-subtle transition-colors"
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
