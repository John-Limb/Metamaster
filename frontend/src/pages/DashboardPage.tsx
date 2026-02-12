import React from 'react'
import { Link } from 'react-router-dom'
import { FaFolder, FaFilm, FaTv, FaDatabase, FaPlus } from 'react-icons/fa'
import { EmptyState, InlineEmptyState } from '@/components/common/EmptyState'
import { Button } from '@/components/common/Button'
import { Card } from '@/components/common/Card'

interface StatCardProps {
  icon: React.ReactNode
  title: string
  value: string | number
  subtitle?: string
}

const StatCard: React.FC<StatCardProps> = ({ icon, title, value, subtitle }) => (
  <Card variant="bordered" className="p-6">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-secondary-500 dark:text-secondary-400 text-sm font-medium">{title}</p>
        <p className="text-3xl font-bold text-secondary-900 dark:text-white mt-2">{value}</p>
        {subtitle && <p className="text-secondary-400 text-xs mt-1">{subtitle}</p>}
      </div>
      <div className="text-primary-500 text-3xl opacity-20">{icon}</div>
    </div>
  </Card>
)

export const DashboardPage: React.FC = () => {
  // In a real implementation, this would fetch data from the API
  // For now, we show empty state patterns
  const isConfigured = false // This would come from configuration context

  const handleAddFiles = () => {
    // Navigate to files page
    window.location.href = '/files'
  }

  const handleScanDirectory = () => {
    // Navigate to files page with scan prompt
    window.location.href = '/files?action=scan'
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-secondary-900 dark:text-white mb-2">Dashboard</h1>
        <p className="text-secondary-600 dark:text-secondary-400">Overview of your media library</p>
      </div>

      {/* Statistics Grid - Shows loading skeleton when loading */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={<FaFolder />}
          title="Total Files"
          value="—"
          subtitle="Files in library"
        />
        <StatCard
          icon={<FaFilm />}
          title="Movies"
          value="—"
          subtitle="Movies indexed"
        />
        <StatCard
          icon={<FaTv />}
          title="TV Shows"
          value="—"
          subtitle="Shows indexed"
        />
        <StatCard
          icon={<FaDatabase />}
          title="Storage Used"
          value="—"
          subtitle="Total storage"
        />
      </div>

      {/* Recent Activity - Empty State */}
      <Card variant="bordered" className="p-6">
        <h2 className="text-lg font-semibold text-secondary-900 dark:text-white mb-4">Recent Activity</h2>
        <InlineEmptyState
          title="No recent activity"
          description="Start by uploading or scanning files"
          iconVariant="noData"
          action={{
            label: 'Add Files',
            onClick: handleAddFiles,
          }}
        />
      </Card>

      {/* Quick Actions */}
      <Card variant="bordered" className="p-6">
        <h2 className="text-lg font-semibold text-secondary-900 dark:text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button
            variant="primary"
            size="md"
            onClick={handleAddFiles}
            leftIcon={<FaPlus />}
          >
            Upload Files
          </Button>
          <Button
            variant="secondary"
            size="md"
            onClick={handleScanDirectory}
          >
            Scan Directory
          </Button>
          <Link to="/settings">
            <Button
              variant="ghost"
              size="md"
              className="w-full"
            >
              View Settings
            </Button>
          </Link>
        </div>
      </Card>

      {/* Storage Chart - Placeholder with guidance */}
      <Card variant="bordered" className="p-6">
        <h2 className="text-lg font-semibold text-secondary-900 dark:text-white mb-4">Storage Breakdown</h2>
        <EmptyState
          iconVariant="featureDisabled"
          title="Configure storage to see breakdown"
          description="Set up your media library paths to enable storage analytics"
          action={{
            label: 'Configure Storage',
            onClick: () => window.location.href = '/settings?section=paths',
            variant: 'secondary',
          }}
          className="py-8"
        />
      </Card>
    </div>
  )
}
