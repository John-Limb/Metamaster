import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock apiClient before importing fileService
const mockGet = vi.fn()
const mockDelete = vi.fn()
const mockPatch = vi.fn()
const mockPost = vi.fn()

vi.mock('@/utils/api', () => ({
  apiClient: {
    get: (...args: unknown[]) => mockGet(...args),
    delete: (...args: unknown[]) => mockDelete(...args),
    patch: (...args: unknown[]) => mockPatch(...args),
    post: (...args: unknown[]) => mockPost(...args),
  },
}))

vi.mock('@/utils/errorHandler', () => ({
  errorHandler: { handleError: vi.fn() },
}))

import { fileService } from '../fileService'

describe('fileService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getFiles', () => {
    it('calls correct URL with encoded path', async () => {
      const mockData = { items: [], total: 0, page: 1, pageSize: 20, totalPages: 0 }
      mockGet.mockResolvedValue({ data: mockData })

      const result = await fileService.getFiles('/media/movies', 1, 20)

      expect(mockGet).toHaveBeenCalledWith(
        '/files?path=%2Fmedia%2Fmovies&page=1&pageSize=20'
      )
      expect(result).toEqual(mockData)
    })

    it('encodes special characters in path', async () => {
      mockGet.mockResolvedValue({ data: { items: [] } })

      await fileService.getFiles('/media/my movies & shows', 2, 10)

      expect(mockGet).toHaveBeenCalledWith(
        '/files?path=%2Fmedia%2Fmy%20movies%20%26%20shows&page=2&pageSize=10'
      )
    })
  })

  describe('getFileStats', () => {
    it('calls /files/stats and returns data', async () => {
      const mockStats = { totalFiles: 5, totalSize: 1000, filesByType: { '.mp4': 3 }, lastUpdated: '2024-01-01' }
      mockGet.mockResolvedValue({ data: mockStats })

      const result = await fileService.getFileStats()

      expect(mockGet).toHaveBeenCalledWith('/files/stats')
      expect(result).toEqual(mockStats)
    })
  })

  describe('getFileDetails', () => {
    it('calls correct URL with file id', async () => {
      const mockFile = { id: '1', name: 'test.mp4' }
      mockGet.mockResolvedValue({ data: mockFile })

      const result = await fileService.getFileDetails('1')

      expect(mockGet).toHaveBeenCalledWith('/files/1')
      expect(result).toEqual(mockFile)
    })
  })
})
