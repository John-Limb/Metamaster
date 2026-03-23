import type { FileItem, SearchFilters } from '@/types'

// File Management Logic
export const fileManagement = {
  // Get file extension from filename
  getExtension: (filename: string): string => {
    const parts = filename.split('.')
    return parts.length > 1 ? parts.pop()?.toLowerCase() || '' : ''
  },

  // Get file type category
  getFileType: (file: FileItem): string => {
    const ext = fileManagement.getExtension(file.name)

    const typeCategories: Record<string, string[]> = {
      video: ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v', 'mpg', 'mpeg'],
      audio: ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a'],
      image: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico'],
      document: ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'md', 'csv'],
      archive: ['zip', 'rar', '7z', 'tar', 'gz', 'bz2'],
    }

    for (const [type, extensions] of Object.entries(typeCategories)) {
      if (extensions.includes(ext)) {
        return type
      }
    }

    return 'other'
  },

  // Get files by type
  filterByType: (files: FileItem[], type: string): FileItem[] => {
    return files.filter((file) => fileManagement.getFileType(file) === type)
  },

  // Search/Filter Logic
  filterFiles: (files: FileItem[], filters: SearchFilters): FileItem[] => {
    let filtered = [...files]

    // Filter by query
    if (filters.query) {
      const query = filters.query.toLowerCase()
      filtered = filtered.filter(
        (file) =>
          file.name.toLowerCase().includes(query) ||
          (file.path && file.path.toLowerCase().includes(query))
      )
    }

    // Filter by type
    if (filters.type) {
      filtered = filtered.filter((file) => {
        if (filters.type === 'file') return file.type === 'file'
        return true
      })
    }

    // Filter by file type
    if (filters.fileType) {
      filtered = filtered.filter(
        (file) => fileManagement.getExtension(file.name) === filters.fileType
      )
    }

    // Filter by date range
    if (filters.dateFrom) {
      const fromDate = new Date(filters.dateFrom)
      filtered = filtered.filter((file) => new Date(file.createdAt) >= fromDate)
    }

    if (filters.dateTo) {
      const toDate = new Date(filters.dateTo)
      filtered = filtered.filter((file) => new Date(file.createdAt) <= toDate)
    }

    // Filter by size range
    if (filters.sizeMin !== undefined) {
      filtered = filtered.filter((file) => file.size >= filters.sizeMin!)
    }

    if (filters.sizeMax !== undefined) {
      filtered = filtered.filter((file) => file.size <= filters.sizeMax!)
    }

    // Filter by tags
    if (filters.tags && filters.tags.length > 0) {
      filtered = filtered.filter((file) =>
        filters.tags!.some((tag) => (file.metadata?.tags as string[] | undefined)?.includes(tag))
      )
    }

    return filtered
  },

  // Sort files
  sortFiles: (
    files: FileItem[],
    sortBy: 'name' | 'size' | 'date' = 'name',
    order: 'asc' | 'desc' = 'asc'
  ): FileItem[] => {
    const sorted = [...files].sort((a, b) => {
      let comparison = 0

      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name)
          break
        case 'size':
          comparison = a.size - b.size
          break
        case 'date':
          comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
          break
      }

      return order === 'asc' ? comparison : -comparison
    })

    return sorted
  },

  // Batch operation logic
  canBatchDelete: (files: FileItem[], selectedIds: string[]): boolean => {
    const selectedFiles = files.filter((f) => selectedIds.includes(f.id))
    return selectedFiles.length > 0 && !selectedFiles.some((f) => f.type === 'directory')
  },

  canBatchMove: (files: FileItem[], selectedIds: string[]): boolean => {
    return selectedIds.length > 0
  },

  // Validate file operations
  validateDelete: (files: FileItem[], ids: string[]): { valid: boolean; errors: string[] } => {
    const errors: string[] = []
    const selectedFiles = files.filter((f) => ids.includes(f.id))

    if (selectedFiles.length === 0) {
      errors.push('No files selected')
    }

    const directories = selectedFiles.filter((f) => f.type === 'directory')
    if (directories.length > 0) {
      errors.push(`Cannot delete ${directories.length} directory(ies)`)
    }

    return {
      valid: errors.length === 0,
      errors,
    }
  },

  validateMove: (
    ids: string[],
    targetPath: string
  ): { valid: boolean; errors: string[] } => {
    const errors: string[] = []

    if (ids.length === 0) {
      errors.push('No files selected')
    }

    if (!targetPath || targetPath.trim() === '') {
      errors.push('Invalid target path')
    }

    if (targetPath.startsWith(ids[0] || '')) {
      errors.push('Cannot move folder into itself')
    }

    return {
      valid: errors.length === 0,
      errors,
    }
  },

  // Batch operation progress tracking
  createBatchProgress: (total: number) => ({
    total,
    completed: 0,
    failed: 0,
    errors: [] as string[],

    incrementCompleted: function () {
      this.completed++
    },
    incrementFailed: function (error: string) {
      this.failed++
      this.errors.push(error)
    },
    getProgress: function () {
      return Math.round(((this.completed + this.failed) / this.total) * 100)
    },
    isComplete: function () {
      return this.completed + this.failed >= this.total
    },
  }),
}

// Validation utilities
export const validation = {
  // Validate file name
  isValidFileName: (name: string): boolean => {
    // eslint-disable-next-line no-control-regex
    const invalidChars = /[<>:"/\\|?*\u0000-\u001f]/
    return name.trim().length > 0 && !invalidChars.test(name)
  },

  // Validate path
  isValidPath: (path: string): boolean => {
    return path.startsWith('/') && path.length > 1
  },

  // Validate email
  isValidEmail: (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  },

  // Validate URL
  isValidUrl: (url: string): boolean => {
    try {
      new URL(url)
      return true
    } catch {
      return false
    }
  },

  // Sanitize file name
  sanitizeFileName: (name: string): string => {
    // eslint-disable-next-line no-control-regex
    return name.replace(/[<>:"/\\|?*\u0000-\u001f]/g, '_').trim()
  },
}

// Formatting utilities
export const formatting = {
  // Format date
  formatDate: (date: string | Date, format: 'short' | 'long' | 'relative' = 'short'): string => {
    const d = typeof date === 'string' ? new Date(date) : date

    if (format === 'relative') {
      const now = new Date()
      const diff = now.getTime() - d.getTime()
      const seconds = Math.floor(diff / 1000)
      const minutes = Math.floor(seconds / 60)
      const hours = Math.floor(minutes / 60)
      const days = Math.floor(hours / 24)

      if (seconds < 60) return 'just now'
      if (minutes < 60) return `${minutes}m ago`
      if (hours < 24) return `${hours}h ago`
      if (days < 7) return `${days}d ago`
    }

    if (format === 'long') {
      return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    }

    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  },

  // Format percentage
  formatPercentage: (value: number, decimals = 1): string => {
    return `${value.toFixed(decimals)}%`
  },

  // Format duration (seconds to human readable)
  formatDuration: (seconds: number): string => {
    if (seconds < 60) return `${seconds}s`

    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60

    if (minutes < 60) {
      return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
    }

    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60

    if (remainingMinutes > 0) {
      return `${hours}h ${remainingMinutes}m`
    }

    return `${hours}h`
  },

  // Format number with separators
  formatNumber: (num: number): string => {
    return num.toLocaleString()
  },

  // Truncate text
  truncate: (text: string, maxLength: number, suffix = '...'): string => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength - suffix.length) + suffix
  },
}

// Search helpers
export const searchHelpers = {
  // Highlight matching text
  highlightMatch: (text: string, query: string): string => {
    if (!query.trim()) return text

    // eslint-disable-next-line security/detect-non-literal-regexp
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
    return text.replace(regex, '<mark>$1</mark>')
  },

  // Get search relevance score
  calculateRelevance: (text: string, query: string): number => {
    const lowerText = text.toLowerCase()
    const lowerQuery = query.toLowerCase()

    if (lowerText === lowerQuery) return 100
    if (lowerText.startsWith(lowerQuery)) return 90
    if (lowerText.includes(lowerQuery)) return 70

    // Partial word match
    const queryWords = lowerQuery.split(/\s+/)
    const textWords = lowerText.split(/\s+/)
    const matchedWords = queryWords.filter((word) =>
      textWords.some((textWord) => textWord.includes(word))
    )

    return Math.round((matchedWords.length / queryWords.length) * 60)
  },

  // Generate search suggestions
  generateSuggestions: (query: string, options: string[]): string[] => {
    if (!query.trim() || options.length === 0) return []

    const lowerQuery = query.toLowerCase()
    return options
      .filter((option) => option.toLowerCase().includes(lowerQuery))
      .slice(0, 10)
  },
}
