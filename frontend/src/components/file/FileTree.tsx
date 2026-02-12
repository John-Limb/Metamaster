import React, { useState } from 'react'
import { FaChevronRight, FaChevronDown, FaFolder, FaFile } from 'react-icons/fa'
import type { FileItem } from '@/types'

interface FileTreeNode extends FileItem {
  children?: FileTreeNode[]
  isExpanded?: boolean
}

interface FileTreeProps {
  files: FileItem[]
  selectedFiles: string[]
  onSelectFile: (id: string) => void
  onDoubleClick?: (file: FileItem) => void
  onContextMenu?: (e: React.MouseEvent, file: FileItem) => void
  isLoading?: boolean
  emptyMessage?: string
}

interface TreeNodeProps {
  node: FileTreeNode
  level: number
  isSelected: boolean
  isExpanded: boolean
  onToggleExpand: (id: string) => void
  onSelectFile: (id: string) => void
  onDoubleClick?: (file: FileItem) => void
  onContextMenu?: (e: React.MouseEvent, file: FileItem) => void
}

const TreeNode: React.FC<TreeNodeProps> = ({
  node,
  level,
  isSelected,
  isExpanded,
  onToggleExpand,
  onSelectFile,
  onDoubleClick,
  onContextMenu,
}) => {
  const isDirectory = node.type === 'directory'
  const hasChildren = node.children && node.children.length > 0

  return (
    <>
      <div
        className={`flex items-center gap-2 px-2 py-1 hover:bg-gray-100 cursor-pointer transition ${
          isSelected ? 'bg-blue-50' : ''
        }`}
        style={{ paddingLeft: `${level * 20 + 8}px` }}
        onClick={() => onSelectFile(node.id)}
        onDoubleClick={() => onDoubleClick?.(node)}
        onContextMenu={(e) => onContextMenu?.(e, node)}
      >
        {isDirectory && hasChildren ? (
          <button
            onClick={(e) => {
              e.stopPropagation()
              onToggleExpand(node.id)
            }}
            className="flex-shrink-0 w-4 h-4 flex items-center justify-center hover:bg-gray-200 rounded"
          >
            {isExpanded ? (
              <FaChevronDown className="w-3 h-3 text-gray-600" />
            ) : (
              <FaChevronRight className="w-3 h-3 text-gray-600" />
            )}
          </button>
        ) : (
          <div className="flex-shrink-0 w-4" />
        )}

        {isDirectory ? (
          <FaFolder className="w-4 h-4 text-blue-500 flex-shrink-0" />
        ) : (
          <FaFile className="w-4 h-4 text-gray-500 flex-shrink-0" />
        )}

        <span className="text-sm text-gray-900 truncate flex-grow">{node.name}</span>
      </div>

      {isDirectory && isExpanded && hasChildren && (
        <div>
          {node.children!.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              isSelected={false}
              isExpanded={false}
              onToggleExpand={onToggleExpand}
              onSelectFile={onSelectFile}
              onDoubleClick={onDoubleClick}
              onContextMenu={onContextMenu}
            />
          ))}
        </div>
      )}
    </>
  )
}

export const FileTree: React.FC<FileTreeProps> = ({
  files,
  selectedFiles,
  onSelectFile,
  onDoubleClick,
  onContextMenu,
  isLoading = false,
  emptyMessage = 'No files to display',
}) => {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())

  const toggleExpand = (id: string) => {
    const newExpanded = new Set(expandedNodes)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedNodes(newExpanded)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (files.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-gray-500 text-lg">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="divide-y divide-gray-200">
        {files.map((file) => (
          <TreeNode
            key={file.id}
            node={file as FileTreeNode}
            level={0}
            isSelected={selectedFiles.includes(file.id)}
            isExpanded={expandedNodes.has(file.id)}
            onToggleExpand={toggleExpand}
            onSelectFile={onSelectFile}
            onDoubleClick={onDoubleClick}
            onContextMenu={onContextMenu}
          />
        ))}
      </div>
    </div>
  )
}
