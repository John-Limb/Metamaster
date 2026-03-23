import React from 'react'
import type { ReactNode } from 'react'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { ToastContainer } from '@/components/common'
import { useUIStore } from '@/stores/uiStore'

interface DashboardLayoutProps {
  children: ReactNode
  title?: string
  subtitle?: string
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  title,
  subtitle,
}) => {
  const toasts = useUIStore((state) => state.toasts)
  const removeToast = useUIStore((state) => state.removeToast)

  return (
    <div className="flex flex-col h-screen bg-page">
      {/* Header */}
      <Header />

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar />

        {/* Content */}
        <main className="flex-1 overflow-y-auto">
          {/* Page Header */}
          {(title || subtitle) && (
            <div className="bg-card border-b border-edge px-4 sm:px-6 lg:px-8 py-6">
              <div className="max-w-7xl mx-auto">
                {title && <h1 className="text-3xl font-bold text-body">{title}</h1>}
                {subtitle && <p className="mt-2 text-dim">{subtitle}</p>}
              </div>
            </div>
          )}

          {/* Page Content */}
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </div>
        </main>
      </div>

      {/* Toast Container */}
      <ToastContainer toasts={toasts} onRemoveToast={removeToast} />
    </div>
  )
}
