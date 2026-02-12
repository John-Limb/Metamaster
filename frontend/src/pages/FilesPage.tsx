import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Breadcrumb } from '@/components/common'
import { FileExplorer, FileScanner } from '@/components/file'
import { useFileStore } from '@/stores/fileStore'
import type { BreadcrumbItem } from '@/components/common'

export const FilesPage: React.FC = () => {
  const navigate = useNavigate()
  const { currentPath, navigateToPath } = useFileStore()

  // Generate breadcrumb items from current path
  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    const parts = currentPath.split('/').filter(Boolean)
    const items: BreadcrumbItem[] = []

    // Add root
    items.push({
      label: 'Files',
      onClick: () => navigateToPath('/'),
    })

    // Add path segments
    let accumulatedPath = ''
    parts.forEach((part) => {
      accumulatedPath += '/' + part
      items.push({
        label: part,
        onClick: () => navigateToPath(accumulatedPath),
      })
    })

    return items
  }

  const breadcrumbItems = generateBreadcrumbs()

  return (
    <div className="space-y-6 h-full flex flex-col">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Files</h1>
        <p className="text-gray-600">Browse and manage your files</p>
      </div>

      {/* Breadcrumb Navigation */}
      <Breadcrumb items={breadcrumbItems} showHome={true} onHomeClick={() => navigateToPath('/')} />

      {/* Main Content */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* File Explorer */}
        <div className="lg:col-span-2 min-h-0">
          <FileExplorer showDetailsPanel={true} />
        </div>

        {/* File Scanner Sidebar */}
        <div className="lg:col-span-1">
          <FileScanner />
        </div>
      </div>
    </div>
  )
}
