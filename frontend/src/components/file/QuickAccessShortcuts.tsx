import React from 'react'
import { FaHome, FaDownload, FaMusic, FaVideo, FaImage, FaFile } from 'react-icons/fa'
import { useFileStore } from '@/stores/fileStore'

interface Shortcut {
  id: string
  label: string
  path: string
  icon: React.ReactNode
  color: string
}

interface QuickAccessShortcutsProps {
  onNavigate?: (path: string) => void
  className?: string
}

export const QuickAccessShortcuts: React.FC<QuickAccessShortcutsProps> = ({
  onNavigate,
  className = '',
}: QuickAccessShortcutsProps) => {
  const { navigateToPath } = useFileStore()

  const shortcuts: Shortcut[] = [
    {
      id: 'home',
      label: 'Home',
      path: '/',
      icon: <FaHome className="w-5 h-5" />,
      color: 'bg-blue-100 text-blue-600 hover:bg-blue-200',
    },
    {
      id: 'downloads',
      label: 'Downloads',
      path: '/Downloads',
      icon: <FaDownload className="w-5 h-5" />,
      color: 'bg-green-100 text-green-600 hover:bg-green-200',
    },
    {
      id: 'music',
      label: 'Music',
      path: '/Music',
      icon: <FaMusic className="w-5 h-5" />,
      color: 'bg-purple-100 text-purple-600 hover:bg-purple-200',
    },
    {
      id: 'videos',
      label: 'Videos',
      path: '/Videos',
      icon: <FaVideo className="w-5 h-5" />,
      color: 'bg-red-100 text-red-600 hover:bg-red-200',
    },
    {
      id: 'pictures',
      label: 'Pictures',
      path: '/Pictures',
      icon: <FaImage className="w-5 h-5" />,
      color: 'bg-pink-100 text-pink-600 hover:bg-pink-200',
    },
    {
      id: 'documents',
      label: 'Documents',
      path: '/Documents',
      icon: <FaFile className="w-5 h-5" />,
      color: 'bg-yellow-100 text-yellow-600 hover:bg-yellow-200',
    },
  ]

  const handleNavigate = (path: string) => {
    navigateToPath(path)
    onNavigate?.(path)
  }

  return (
    <div className={`space-y-2 ${className}`}>
      <h3 className="text-sm font-semibold text-body px-2">Quick Access</h3>
      <div className="space-y-1">
        {shortcuts.map((shortcut) => (
          <button
            key={shortcut.id}
            onClick={() => handleNavigate(shortcut.path)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition ${shortcut.color}`}
            title={shortcut.label}
          >
            {shortcut.icon}
            <span className="text-sm font-medium">{shortcut.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
