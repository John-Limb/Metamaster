import React, { useEffect, useRef } from 'react'
import { FaTrash, FaEdit, FaCopy, FaDownload, FaInfo } from 'react-icons/fa'
import { useUIStore } from '@/stores/uiStore'
import { fileService } from '@/services/fileService'
import type { FileItem } from '@/types'

interface FileContextMenuProps {
  file: FileItem
  x: number
  y: number
  onClose: () => void
}

export const FileContextMenu: React.FC<FileContextMenuProps> = ({ file, x, y, onClose }: FileContextMenuProps) => {
  const menuRef = useRef<HTMLDivElement>(null)
  const { addToast } = useUIStore()

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose()
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [onClose])

  const handleDelete = async () => {
    try {
      await fileService.deleteFile(file.id)
      addToast({
        type: 'success',
        message: `${file.name} deleted successfully`,
      })
      onClose()
    } catch {
      addToast({
        type: 'error',
        message: `Failed to delete ${file.name}`,
      })
    }
  }

  const handleRename = () => {
    const newName = prompt('Enter new name:', file.name)
    if (newName && newName !== file.name) {
      fileService
        .renameFile(file.id, newName)
        .then(() => {
          addToast({
            type: 'success',
            message: `File renamed to ${newName}`,
          })
          onClose()
        })
        .catch(() => {
          addToast({
            type: 'error',
            message: 'Failed to rename file',
          })
        })
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(file.path)
    addToast({
      type: 'success',
      message: 'Path copied to clipboard',
    })
    onClose()
  }

  const handleDownload = () => {
    const link = document.createElement('a')
    link.href = file.path
    link.download = file.name
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    onClose()
  }

  const menuItems = [
    {
      label: 'Rename',
      icon: FaEdit,
      onClick: handleRename,
      show: file.type === 'file',
    },
    {
      label: 'Delete',
      icon: FaTrash,
      onClick: handleDelete,
      className: 'text-red-600 hover:bg-red-50',
    },
    {
      label: 'Copy Path',
      icon: FaCopy,
      onClick: handleCopy,
    },
    {
      label: 'Download',
      icon: FaDownload,
      onClick: handleDownload,
      show: file.type === 'file',
    },
    {
      label: 'Properties',
      icon: FaInfo,
      onClick: () => {
        // Properties modal will be handled by parent
        onClose()
      },
    },
  ]

  return (
    <div
      ref={menuRef}
      className="fixed bg-card rounded-lg shadow-lg border border-edge z-50 py-1 min-w-48"
      style={{
        left: `${x}px`,
        top: `${y}px`,
      }}
    >
      {menuItems
        .filter((item) => item.show !== false)
        .map((item, index) => {
          const Icon = item.icon
          return (
            <button
              key={index}
              onClick={item.onClick}
              className={`w-full flex items-center gap-3 px-4 py-2 text-sm text-dim hover:bg-subtle transition ${
                item.className || ''
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </button>
          )
        })}
    </div>
  )
}
