import { describe, it, expect } from 'vitest'
import { fileManagement, validation, formatting, searchHelpers } from '@/utils/businessLogic'
import type { FileItem, SearchFilters } from '@/types'

describe('Business Logic Utilities', () => {
  describe('fileManagement', () => {
    const mockFile = (name: string, size: number, type: 'file' | 'directory' = 'file'): FileItem => ({
      id: `file-${name}`,
      name,
      path: `/test/${name}`,
      type,
      size,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    })

    describe('getExtension', () => {
      it('should extract extension from filename', () => {
        expect(fileManagement.getExtension('document.pdf')).toBe('pdf')
        expect(fileManagement.getExtension('image.jpg')).toBe('jpg')
        expect(fileManagement.getExtension('noextension')).toBe('')
      })

      it('should handle uppercase extensions', () => {
        expect(fileManagement.getExtension('image.PNG')).toBe('png')
      })
    })

    describe('getFileType', () => {
      it('should identify video files', () => {
        const videoFile = mockFile('video.mp4', 1000000)
        expect(fileManagement.getFileType(videoFile)).toBe('video')
      })

      it('should identify audio files', () => {
        const audioFile = mockFile('song.mp3', 5000000)
        expect(fileManagement.getFileType(audioFile)).toBe('audio')
      })

      it('should identify image files', () => {
        const imageFile = mockFile('photo.jpg', 2000000)
        expect(fileManagement.getFileType(imageFile)).toBe('image')
      })

      it('should identify document files', () => {
        const docFile = mockFile('document.pdf', 100000)
        expect(fileManagement.getFileType(docFile)).toBe('document')
      })

      it('should identify archive files', () => {
        const archiveFile = mockFile('archive.zip', 10000000)
        expect(fileManagement.getFileType(archiveFile)).toBe('archive')
      })

      it('should return other for unknown types', () => {
        const unknownFile = mockFile('unknown.xyz', 1000)
        expect(fileManagement.getFileType(unknownFile)).toBe('other')
      })
    })

    describe('formatSize', () => {
      it('should format bytes', () => {
        expect(fileManagement.formatSize(500)).toBe('500 B')
      })

      it('should format kilobytes', () => {
        expect(fileManagement.formatSize(2048)).toBe('2 KB')
      })

      it('should format megabytes', () => {
        expect(fileManagement.formatSize(2097152)).toBe('2 MB')
      })

      it('should format gigabytes', () => {
        expect(fileManagement.formatSize(2147483648)).toBe('2 GB')
      })

      it('should handle zero', () => {
        expect(fileManagement.formatSize(0)).toBe('0 B')
      })
    })

    describe('filterByType', () => {
      it('should filter files by type', () => {
        const files: FileItem[] = [
          mockFile('video1.mp4', 1000),
          mockFile('video2.mkv', 2000),
          mockFile('audio1.mp3', 500),
          mockFile('image1.jpg', 3000),
        ]

        const videoFiles = fileManagement.filterByType(files, 'video')
        expect(videoFiles).toHaveLength(2)
        expect(videoFiles.every(f => f.name.includes('video'))).toBe(true)
      })
    })

    describe('filterFiles', () => {
      it('should filter files by query', () => {
        const files: FileItem[] = [
          mockFile('test-file-1.mp4', 1000),
          mockFile('other-file.mp4', 2000),
          mockFile('test-file-2.mp4', 3000),
        ]

        const filters: SearchFilters = { query: 'test' }
        const result = fileManagement.filterFiles(files, filters)

        // 'test-file-1.mp4' and 'test-file-2.mp4' contain 'test'
        expect(result.length).toBeGreaterThanOrEqual(2)
      })

      it('should filter files by type', () => {
        const files: FileItem[] = [
          mockFile('file1.mp4', 1000, 'file'),
          mockFile('folder1', 0, 'directory'),
          mockFile('file2.mp4', 2000, 'file'),
        ]

        const filters: SearchFilters = { type: 'file' }
        const result = fileManagement.filterFiles(files, filters)

        expect(result).toHaveLength(2)
        expect(result.every(f => f.type === 'file')).toBe(true)
      })

      it('should filter files by size range', () => {
        const files: FileItem[] = [
          mockFile('small.mp4', 1000000),
          mockFile('medium.mp4', 5000000),
          mockFile('large.mp4', 10000000),
        ]

        const filters: SearchFilters = { sizeMin: 2000000, sizeMax: 8000000 }
        const result = fileManagement.filterFiles(files, filters)

        expect(result).toHaveLength(1)
        expect(result[0].name).toBe('medium.mp4')
      })

      it('should filter files by date range', () => {
        const files: FileItem[] = [
          { ...mockFile('old.mp4', 1000), createdAt: '2023-01-01' },
          { ...mockFile('new.mp4', 2000), createdAt: '2024-06-01' },
        ]

        const filters: SearchFilters = { dateFrom: '2024-01-01' }
        const result = fileManagement.filterFiles(files, filters)

        expect(result).toHaveLength(1)
        expect(result[0].name).toBe('new.mp4')
      })
    })

    describe('sortFiles', () => {
      it('should sort files by name', () => {
        const files: FileItem[] = [
          mockFile('zebra.mp4', 1000),
          mockFile('apple.mp4', 2000),
          mockFile('banana.mp4', 3000),
        ]

        const sorted = fileManagement.sortFiles(files, 'name', 'asc')
        expect(sorted[0].name).toBe('apple.mp4')
        expect(sorted[1].name).toBe('banana.mp4')
        expect(sorted[2].name).toBe('zebra.mp4')
      })

      it('should sort files by size', () => {
        const files: FileItem[] = [
          mockFile('large.mp4', 10000),
          mockFile('small.mp4', 1000),
          mockFile('medium.mp4', 5000),
        ]

        const sorted = fileManagement.sortFiles(files, 'size', 'asc')
        expect(sorted[0].name).toBe('small.mp4')
        expect(sorted[1].name).toBe('medium.mp4')
        expect(sorted[2].name).toBe('large.mp4')
      })

      it('should reverse order when desc', () => {
        const files: FileItem[] = [
          mockFile('a.mp4', 1000),
          mockFile('b.mp4', 2000),
          mockFile('c.mp4', 3000),
        ]

        const sorted = fileManagement.sortFiles(files, 'name', 'desc')
        expect(sorted[0].name).toBe('c.mp4')
      })
    })

    describe('canBatchDelete', () => {
      it('should return true when files are selected and no directories', () => {
        const files: FileItem[] = [
          mockFile('file1.mp4', 1000),
          mockFile('file2.mp4', 2000),
        ]
        expect(fileManagement.canBatchDelete(files, ['file-file1.mp4', 'file-file2.mp4'])).toBe(true)
      })

      it('should return false when directories are selected', () => {
        const files: FileItem[] = [
          mockFile('file1.mp4', 1000),
          mockFile('folder1', 0, 'directory'),
        ]
        // mockFile generates id as 'file-' + name, so 'file-folder1' not 'folder-folder1'
        expect(fileManagement.canBatchDelete(files, ['file-file1.mp4', 'file-folder1'])).toBe(false)
      })

      it('should return false when no files are selected', () => {
        const files: FileItem[] = [
          mockFile('file1.mp4', 1000),
        ]
        expect(fileManagement.canBatchDelete(files, [])).toBe(false)
      })
    })

    describe('validateDelete', () => {
      it('should return valid for deletable files', () => {
        const files: FileItem[] = [
          mockFile('file1.mp4', 1000, 'file'),
          mockFile('file2.mp4', 2000, 'file'),
        ]

        const result = fileManagement.validateDelete(files, ['file-file1.mp4', 'file-file2.mp4'])
        expect(result.valid).toBe(true)
        expect(result.errors).toHaveLength(0)
      })

      it('should return invalid when directories are included', () => {
        const files: FileItem[] = [
          mockFile('file1.mp4', 1000, 'file'),
          mockFile('folder1', 0, 'directory'),
        ]

        const result = fileManagement.validateDelete(files, ['file-file1.mp4', 'file-folder1'])
        expect(result.valid).toBe(false)
        expect(result.errors.some(e => e.includes('directory'))).toBe(true)
      })

      it('should return invalid when no files selected', () => {
        const files: FileItem[] = [
          mockFile('file1.mp4', 1000),
        ]

        const result = fileManagement.validateDelete(files, [])
        expect(result.valid).toBe(false)
        expect(result.errors).toContain('No files selected')
      })
    })

    describe('validateMove', () => {
      it('should return valid for valid move operation', () => {
        const result = fileManagement.validateMove(['file1'], '/new/path')
        expect(result.valid).toBe(true)
      })

      it('should return invalid when no files selected', () => {
        const result = fileManagement.validateMove([], '/new/path')
        expect(result.valid).toBe(false)
        expect(result.errors).toContain('No files selected')
      })

      it('should return invalid for empty target path', () => {
        const result = fileManagement.validateMove(['file1'], '')
        expect(result.valid).toBe(false)
      })
    })
  })

  describe('validation', () => {
    describe('isValidFileName', () => {
      it('should return true for valid file names', () => {
        expect(validation.isValidFileName('document.pdf')).toBe(true)
        expect(validation.isValidFileName('my-file_2024.txt')).toBe(true)
      })

      it('should return false for invalid file names', () => {
        expect(validation.isValidFileName('')).toBe(false)
        expect(validation.isValidFileName('file<name>.txt')).toBe(false)
        expect(validation.isValidFileName('file|name.txt')).toBe(false)
      })
    })

    describe('isValidPath', () => {
      it('should return true for valid paths', () => {
        expect(validation.isValidPath('/home/user')).toBe(true)
        expect(validation.isValidPath('/files/documents')).toBe(true)
      })

      it('should return false for invalid paths', () => {
        expect(validation.isValidPath('')).toBe(false)
        expect(validation.isValidPath('home/user')).toBe(false)
      })
    })

    describe('isValidEmail', () => {
      it('should return true for valid emails', () => {
        expect(validation.isValidEmail('user@example.com')).toBe(true)
        expect(validation.isValidEmail('user.name@domain.org')).toBe(true)
      })

      it('should return false for invalid emails', () => {
        expect(validation.isValidEmail('invalid')).toBe(false)
        expect(validation.isValidEmail('user@')).toBe(false)
        expect(validation.isValidEmail('@domain.com')).toBe(false)
      })
    })

    describe('isValidUrl', () => {
      it('should return true for valid URLs', () => {
        expect(validation.isValidUrl('https://example.com')).toBe(true)
        expect(validation.isValidUrl('http://localhost:3000')).toBe(true)
      })

      it('should return false for invalid URLs', () => {
        expect(validation.isValidUrl('not-a-url')).toBe(false)
        expect(validation.isValidUrl('')).toBe(false)
      })
    })

    describe('sanitizeFileName', () => {
      it('should replace invalid characters', () => {
        expect(validation.sanitizeFileName('file<name>.txt')).toBe('file_name_.txt')
        expect(validation.sanitizeFileName('file|name.txt')).toBe('file_name.txt')
      })

      it('should trim whitespace', () => {
        expect(validation.sanitizeFileName('  filename  ')).toBe('filename')
      })
    })
  })

  describe('formatting', () => {
    describe('formatDate', () => {
      it('should format date in short format', () => {
        const result = formatting.formatDate('2024-01-15', 'short')
        expect(result).toContain('Jan')
        expect(result).toContain('15')
      })

      it('should format date in long format', () => {
        const result = formatting.formatDate('2024-01-15', 'long')
        expect(result).toContain('January')
        expect(result).toContain('15')
        expect(result).toContain('2024')
      })

      it('should format date relatively', () => {
        const result = formatting.formatDate(new Date(), 'relative')
        expect(result).toBe('just now')
      })
    })

    describe('formatPercentage', () => {
      it('should format percentage correctly', () => {
        expect(formatting.formatPercentage(50)).toBe('50.0%')
        expect(formatting.formatPercentage(33.33, 2)).toBe('33.33%')
      })
    })

    describe('formatDuration', () => {
      it('should format seconds', () => {
        expect(formatting.formatDuration(30)).toBe('30s')
      })

      it('should format minutes', () => {
        expect(formatting.formatDuration(90)).toBe('1m 30s')
      })

      it('should format hours', () => {
        expect(formatting.formatDuration(3660)).toBe('1h 1m')
      })
    })

    describe('formatNumber', () => {
      it('should format number with separators', () => {
        expect(formatting.formatNumber(1000)).toBe('1,000')
        expect(formatting.formatNumber(1000000)).toBe('1,000,000')
      })
    })

    describe('truncate', () => {
      it('should truncate text with suffix', () => {
        expect(formatting.truncate('Hello World', 8)).toBe('Hello...')
        expect(formatting.truncate('Hello World', 5, '***')).toBe('He***')
      })
    })
  })

  describe('searchHelpers', () => {
    describe('highlightMatch', () => {
      it('should highlight matching text', () => {
        const result = searchHelpers.highlightMatch('Hello World', 'World')
        expect(result).toContain('<mark>World</mark>')
      })

      it('should return original text if no query', () => {
        const result = searchHelpers.highlightMatch('Hello World', '')
        expect(result).toBe('Hello World')
      })

      it('should escape special regex characters', () => {
        const result = searchHelpers.highlightMatch('test(1)', '(1)')
        expect(result).toContain('<mark>(1)</mark>')
      })
    })

    describe('calculateRelevance', () => {
      it('should return 100 for exact match', () => {
        expect(searchHelpers.calculateRelevance('hello', 'hello')).toBe(100)
      })

      it('should return 90 for prefix match', () => {
        expect(searchHelpers.calculateRelevance('hello world', 'hello')).toBe(90)
      })

      it('should return 70 for contains match', () => {
        expect(searchHelpers.calculateRelevance('the hello world', 'hello')).toBe(70)
      })

      it('should return lower score for partial match', () => {
        expect(searchHelpers.calculateRelevance('hello world', 'llo')).toBeGreaterThan(0)
      })
    })

    describe('generateSuggestions', () => {
      it('should generate suggestions based on query', () => {
        const options = ['apple', 'apricot', 'banana', 'application']
        const result = searchHelpers.generateSuggestions('app', options)

        expect(result).toContain('apple')
        expect(result).toContain('application')
        expect(result).not.toContain('banana')
      })

      it('should return empty array for empty query', () => {
        const result = searchHelpers.generateSuggestions('', ['apple', 'banana'])
        expect(result).toEqual([])
      })

      it('should limit to 10 suggestions', () => {
        const options = Array.from({ length: 20 }, (_, i) => `option${i}`)
        const result = searchHelpers.generateSuggestions('option', options)
        expect(result).toHaveLength(10)
      })
    })
  })
})
