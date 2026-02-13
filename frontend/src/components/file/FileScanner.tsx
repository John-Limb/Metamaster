import React from 'react'
import { Card } from '@/components/common/Card'
import { EmptyState } from '@/components/common/EmptyState'

interface FileScannerProps {
  onScanComplete?: (files: unknown[]) => void
  onScanError?: (error: string) => void
}

export const FileScanner: React.FC<FileScannerProps> = () => {
  // Show empty state - scan functionality requires API integration
  // When API is available, this would use queueService to start/monitor scan tasks
  return (
    <Card variant="bordered" className="p-6">
      <EmptyState
        iconVariant="featureDisabled"
        title="File Scanner"
        description="Scan functionality requires API integration. Configure your media library paths to enable file scanning."
        action={{
          label: 'Configure Paths',
          onClick: () => window.location.href = '/settings?section=paths',
          variant: 'primary',
        }}
      />
    </Card>
  )
}
