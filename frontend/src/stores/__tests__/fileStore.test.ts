import { describe, it, expect, vi, beforeEach } from 'vitest'
import { act } from '@testing-library/react'

// Mock fileService before importing the store
const mockGetFiles = vi.fn()
const mockGetFileStats = vi.fn()

vi.mock('@/services/fileService', () => ({
  fileService: {
    getFiles: (...args: unknown[]) => mockGetFiles(...args),
    getFileStats: (...args: unknown[]) => mockGetFileStats(...args),
    deleteFile: vi.fn(),
    batchDeleteFiles: vi.fn(),
    batchMoveFiles: vi.fn(),
  },
}))

import { useFileStore } from '../fileStore'

describe('useFileStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset store state between tests
    const { setState } = useFileStore
    setState({
      files: [],
      selectedFiles: [],
      currentPath: '/',
      isLoading: false,
      error: null,
      stats: null,
      recentPaths: [],
    })
  })

  describe('fetchFiles', () => {
    it('sets files from API response', async () => {
      const mockItems = [
        { id: '1', name: 'movie.mp4', path: '/media/movie.mp4', type: 'file' as const, size: 1000, createdAt: '', updatedAt: '' },
      ]
      mockGetFiles.mockResolvedValue({ items: mockItems, total: 1 })

      await act(async () => {
        await useFileStore.getState().fetchFiles('/media')
      })

      const state = useFileStore.getState()
      expect(state.files).toEqual(mockItems)
      expect(state.currentPath).toBe('/media')
      expect(state.isLoading).toBe(false)
    })

    it('sets error on failure', async () => {
      mockGetFiles.mockRejectedValue(new Error('Network error'))

      await act(async () => {
        try {
          await useFileStore.getState().fetchFiles('/')
        } catch {
          // expected
        }
      })

      const state = useFileStore.getState()
      expect(state.error).toBe('Network error')
      expect(state.isLoading).toBe(false)
    })
  })

  describe('navigateToPath', () => {
    it('updates currentPath and clears selection', () => {
      useFileStore.setState({ selectedFiles: ['1', '2'], currentPath: '/' })

      act(() => {
        useFileStore.getState().navigateToPath('/media/movies')
      })

      const state = useFileStore.getState()
      expect(state.currentPath).toBe('/media/movies')
      expect(state.selectedFiles).toEqual([])
    })
  })

  describe('fetchStats', () => {
    it('sets stats from API response', async () => {
      const mockStats = { totalFiles: 5, totalSize: 10000, filesByType: { '.mp4': 3 }, lastUpdated: '2024-01-01' }
      mockGetFileStats.mockResolvedValue(mockStats)

      await act(async () => {
        await useFileStore.getState().fetchStats()
      })

      expect(useFileStore.getState().stats).toEqual(mockStats)
    })
  })
})
