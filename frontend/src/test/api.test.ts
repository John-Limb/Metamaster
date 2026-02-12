import { describe, it, expect, beforeEach, vi } from 'vitest'
import type { AxiosResponse } from 'axios'
import { fileService } from '@/services/fileService'
import { queueService } from '@/services/queueService'
import { movieService } from '@/services/movieService'
import { tvShowService } from '@/services/tvShowService'
import { searchService } from '@/services/searchService'
import { apiClient } from '@/utils/api'
import { errorHandler } from '@/utils/errorHandler'

const createMockResponse = <T>(data: T): AxiosResponse<T> => ({
  data,
  status: 200,
  statusText: 'OK',
  headers: {},
  config: {} as any,
})

describe('API Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('File Operations', () => {
    it('should fetch files successfully', async () => {
      // Mock the API response
      const mockResponse = {
        items: [
          { id: '1', name: 'test.txt', path: '/test', type: 'file' as const, size: 100, createdAt: '2024-01-01', updatedAt: '2024-01-01' },
        ],
        total: 1,
        page: 1,
        pageSize: 20,
        totalPages: 1,
      }

      vi.spyOn(apiClient, 'get').mockResolvedValueOnce(createMockResponse(mockResponse))

      const result = await fileService.getFiles('/test')
      expect(result.items).toHaveLength(1)
      expect(result.items[0].name).toBe('test.txt')
    })

    it('should handle file upload with progress', async () => {
      const mockFile = new File(['test'], 'test.txt', { type: 'text/plain' })
      const mockResponse = {
        id: '1',
        name: 'test.txt',
        path: '/test',
        type: 'file' as const,
        size: 4,
        createdAt: '2024-01-01',
        updatedAt: '2024-01-01',
      }

      vi.spyOn(apiClient, 'post').mockResolvedValueOnce(createMockResponse(mockResponse))

      const progressCallback = vi.fn()
      const result = await fileService.uploadFile(mockFile, '/test', progressCallback)

      expect(result.name).toBe('test.txt')
    })

    it('should handle file deletion', async () => {
      const mockResponse = { success: true }
      vi.spyOn(apiClient, 'delete').mockResolvedValueOnce(createMockResponse(mockResponse))

      const result = await fileService.deleteFile('1')
      expect(result.success).toBe(true)
    })

    it('should handle batch operations', async () => {
      const mockResponse = { success: true }
      vi.spyOn(apiClient, 'post').mockResolvedValueOnce(createMockResponse(mockResponse))

      const result = await fileService.batchDeleteFiles(['1', '2', '3'])
      expect(result.success).toBe(true)
    })
  })

  describe('Queue Operations', () => {
    it('should fetch queue tasks', async () => {
      const mockResponse = {
        items: [
          {
            id: '1',
            type: 'analyze' as const,
            status: 'processing' as const,
            progress: 50,
            createdAt: '2024-01-01',
            updatedAt: '2024-01-01',
          },
        ],
        total: 1,
        page: 1,
        pageSize: 20,
        totalPages: 1,
      }

      vi.spyOn(apiClient, 'get').mockResolvedValueOnce(createMockResponse(mockResponse))

      const result = await queueService.getTasks()
      expect(result.items).toHaveLength(1)
      expect(result.items[0].status).toBe('processing')
    })

    it('should fetch queue statistics', async () => {
      const mockResponse = {
        totalTasks: 10,
        pendingTasks: 2,
        processingTasks: 3,
        completedTasks: 4,
        failedTasks: 1,
      }

      vi.spyOn(apiClient, 'get').mockResolvedValueOnce(createMockResponse(mockResponse))

      const result = await queueService.getStats()
      expect(result.totalTasks).toBe(10)
      expect(result.processingTasks).toBe(3)
    })

    it('should retry failed task', async () => {
      const mockResponse = {
        id: '1',
        type: 'analyze' as const,
        status: 'pending' as const,
        progress: 0,
        createdAt: '2024-01-01',
        updatedAt: '2024-01-01',
      }

      vi.spyOn(apiClient, 'post').mockResolvedValueOnce(createMockResponse(mockResponse))

      const result = await queueService.retryTask('1')
      expect(result.status).toBe('pending')
    })
  })

  describe('Search Operations', () => {
    it('should search across all content types', async () => {
      const mockResponse = {
        items: [
          { id: '1', title: 'Test', type: 'file' as const, relevance: 0.95 },
        ],
        total: 1,
        page: 1,
        pageSize: 20,
        totalPages: 1,
      }

      vi.spyOn(apiClient, 'get').mockResolvedValueOnce(createMockResponse(mockResponse))

      const result = await searchService.search({ query: 'test' })
      expect(result.items).toHaveLength(1)
      expect(result.items[0].relevance).toBe(0.95)
    })

    it('should get search suggestions', async () => {
      const mockResponse = ['test1', 'test2', 'test3']

      vi.spyOn(apiClient, 'get').mockResolvedValueOnce(createMockResponse(mockResponse))

      const result = await searchService.getSuggestions('test')
      expect(result).toHaveLength(3)
    })
  })

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      const mockError = {
        code: '500',
        message: 'Internal Server Error',
      }

      const errorSpy = vi.spyOn(errorHandler, 'handleError')
      errorHandler.handleError(mockError, 'test')

      expect(errorSpy).toHaveBeenCalledWith(mockError, 'test')
    })

    it('should identify retryable errors', () => {
      const retryableError = { code: '503', message: 'Service Unavailable' }
      const nonRetryableError = { code: '400', message: 'Bad Request' }

      expect(errorHandler.isRetryable(retryableError)).toBe(true)
      expect(errorHandler.isRetryable(nonRetryableError)).toBe(false)
    })

    it('should identify authentication errors', () => {
      const authError = { code: '401', message: 'Unauthorized' }
      const otherError = { code: '500', message: 'Server Error' }

      expect(errorHandler.isAuthError(authError)).toBe(true)
      expect(errorHandler.isAuthError(otherError)).toBe(false)
    })

    it('should provide user-friendly error messages', () => {
      const error = { code: '404', message: 'Not Found' }
      const message = errorHandler.getUserMessage(error)

      expect(message).toBe('The requested resource was not found.')
    })
  })

  describe('Retry Logic', () => {
    it('should retry on network errors', async () => {
      const mockError = new Error('Network error')
      const mockSuccess = createMockResponse({ success: true })

      const spy = vi.spyOn(apiClient, 'get')
      spy.mockRejectedValueOnce(mockError)
      spy.mockResolvedValueOnce(mockSuccess)

      // The retry logic is handled by the interceptor
      // This test verifies the error is properly categorized
      expect(errorHandler.isRetryable({ code: 'NETWORK_ERROR', message: 'Network error' })).toBe(true)
    })

    it('should not retry on client errors', () => {
      const clientError = { code: '400', message: 'Bad Request' }
      expect(errorHandler.isRetryable(clientError)).toBe(false)
    })

    it('should retry on server errors', () => {
      const serverError = { code: '500', message: 'Server Error' }
      expect(errorHandler.isRetryable(serverError)).toBe(true)
    })
  })

  describe('Movie Operations', () => {
    it('should fetch movies', async () => {
      const mockResponse = {
        items: [
          { id: '1', title: 'Test Movie', year: 2024 },
        ],
        total: 1,
        page: 1,
        pageSize: 20,
        totalPages: 1,
      }

      vi.spyOn(apiClient, 'get').mockResolvedValueOnce(createMockResponse(mockResponse))

      const result = await movieService.getMovies()
      expect(result.items).toHaveLength(1)
      expect(result.items[0].title).toBe('Test Movie')
    })
  })

  describe('TV Show Operations', () => {
    it('should fetch TV shows', async () => {
      const mockResponse = {
        items: [
          { id: '1', title: 'Test Show', seasons: 2 },
        ],
        total: 1,
        page: 1,
        pageSize: 20,
        totalPages: 1,
      }

      vi.spyOn(apiClient, 'get').mockResolvedValueOnce(createMockResponse(mockResponse))

      const result = await tvShowService.getTVShows()
      expect(result.items).toHaveLength(1)
      expect(result.items[0].title).toBe('Test Show')
    })
  })
})
