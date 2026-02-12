import React from 'react'
import type { ReactNode } from 'react'
import { Header } from '../Header'
import { Sidebar } from '../Sidebar'
import { Footer } from '../Footer'
import { ToastContainer } from '@/components/common'
import { useUIStore } from '@/stores/uiStore'

interface MainLayoutProps {
  children: ReactNode
  showFooter?: boolean
}

export const MainLayout: React.FC<MainLayoutProps> = ({ 
  children, 
  showFooter = true 
}) => {
  const toasts = useUIStore((state) => state.toasts)
  const removeToast = useUIStore((state) => state.removeToast)

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <Header />

      {/* Main Content Area */}
      <div className="flex flex-1 pt-16 overflow-hidden">
        {/* Sidebar */}
        <Sidebar />

        {/* Content */}
        <main className="flex-1 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </div>

          {/* Footer */}
          {showFooter && <Footer />}
        </main>
      </div>

      {/* Toast Container */}
      <ToastContainer toasts={toasts} onRemoveToast={removeToast} />
    </div>
  )
}

export default MainLayout
