import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fileService } from '@/services/fileService'
import { queueService } from '@/services/queueService'
import { searchService } from '@/services/searchService'
import { apiClient } from '@/utils/api'

// Mock the api client
vi.mock('@/utils/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('fileService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should get files with correct parameters', async () => {
    const mockResponse = {
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      totalPages: 0,
    }

    vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse } as any)

    const result = await fileService.getFiles('/videos', 2, 10)

    expect(apiClient.get).toHaveBeenCalledWith(
      '/files?path=%2Fvideos&page=2&pageSize=10'
    )
    expect(result).toEqual(mockResponse)
  })

  it('should get file details', async () => {
    const mockFile = { id: 'file-1', name: 'test.mp4' }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockFile } as any)

    const result = await fileService.getFileDetails('file-1')

    expect(apiClient.get).toHaveBeenCalledWith('/files/file-1')
    expect(result).toEqual(mockFile)
  })

  it('should delete file', async () => {
    const mockResponse = { success: true }
    vi.mocked(apiClient.delete).mockResolvedValue({ data: mockResponse } as any)

    const result = await fileService.deleteFile('file-1')

    expect(apiClient.delete).toHaveBeenCalledWith('/files/file-1')
    expect(result).toEqual(mockResponse)
  })

  it('should move file', async () => {
    const mockFile = { id: 'file-1', path: '/new/path' }
    vi.mocked(apiClient.patch).mockResolvedValue({ data: mockFile } as any)

    const result = await fileService.moveFile('file-1', '/new/path')

    expect(apiClient.patch).toHaveBeenCalledWith('/files/file-1', { path: '/new/path' })
    expect(result).toEqual(mockFile)
  })

  it('should rename file', async () => {
    const mockFile = { id: 'file-1', name: 'new-name.mp4' }
    vi.mocked(apiClient.patch).mockResolvedValue({ data: mockFile } as any)

    const result = await fileService.renameFile('file-1', 'new-name.mp4')

    expect(apiClient.patch).toHaveBeenCalledWith('/files/file-1', { name: 'new-name.mp4' })
    expect(result).toEqual(mockFile)
  })

  it('should batch delete files', async () => {
    const mockResponse = { success: true }
    vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse } as any)

    const result = await fileService.batchDeleteFiles(['file-1', 'file-2'])

    expect(apiClient.post).toHaveBeenCalledWith('/files/batch-delete', { ids: ['file-1', 'file-2'] })
    expect(result).toEqual(mockResponse)
  })

  it('should batch move files', async () => {
    const mockResponse = { success: true }
    vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse } as any)

    const result = await fileService.batchMoveFiles(['file-1', 'file-2'], '/new/path')

    expect(apiClient.post).toHaveBeenCalledWith('/files/batch-move', {
      ids: ['file-1', 'file-2'],
      path: '/new/path',
    })
    expect(result).toEqual(mockResponse)
  })

  it('should search files', async () => {
    const mockResponse = {
      items: [{ id: 'file-1', name: 'test.mp4' }],
      total: 1,
      page: 1,
      pageSize: 20,
      totalPages: 1,
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse } as any)

    const result = await fileService.searchFiles('test', 1, 20)

    expect(apiClient.get).toHaveBeenCalledWith(
      '/files/search?query=test&page=1&pageSize=20'
    )
    expect(result).toEqual(mockResponse)
  })
})

describe('queueService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should get queue tasks', async () => {
    const mockResponse = {
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      totalPages: 0,
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse } as any)

    const result = await queueService.getTasks(1, 20)

    expect(apiClient.get).toHaveBeenCalledWith('/queue/tasks?page=1&pageSize=20')
    expect(result).toEqual(mockResponse)
  })

  it('should get queue tasks with status filter', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({ data: { items: [], total: 0, page: 1, pageSize: 20, totalPages: 0 } } as any)

    await queueService.getTasks(1, 20, 'processing')

    expect(apiClient.get).toHaveBeenCalledWith('/queue/tasks?page=1&pageSize=20&status=processing')
  })

  it('should get queue stats', async () => {
    const mockStats = {
      totalTasks: 100,
      pendingTasks: 20,
      processingTasks: 5,
      completedTasks: 70,
      failedTasks: 5,
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockStats } as any)

    const result = await queueService.getStats()

    expect(apiClient.get).toHaveBeenCalledWith('/queue/stats')
    expect(result).toEqual(mockStats)
  })

  it('should retry failed task', async () => {
    const mockTask = { id: 'task-1', status: 'pending' }
    vi.mocked(apiClient.post).mockResolvedValue({ data: mockTask } as any)

    const result = await queueService.retryTask('task-1')

    expect(apiClient.post).toHaveBeenCalledWith('/queue/tasks/task-1/retry')
    expect(result).toEqual(mockTask)
  })

  it('should cancel task', async () => {
    const mockResponse = { success: true }
    vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse } as any)

    const result = await queueService.cancelTask('task-1')

    expect(apiClient.post).toHaveBeenCalledWith('/queue/tasks/task-1/cancel')
    expect(result).toEqual(mockResponse)
  })

  it('should clear completed tasks', async () => {
    const mockResponse = { success: true }
    vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse } as any)

    const result = await queueService.clearCompletedTasks()

    expect(apiClient.post).toHaveBeenCalledWith('/queue/clear-completed')
    expect(result).toEqual(mockResponse)
  })

  it('should get task progress', async () => {
    const mockProgress = { progress: 75, status: 'processing' }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockProgress } as any)

    const result = await queueService.getTaskProgress('task-1')

    expect(apiClient.get).toHaveBeenCalledWith('/queue/tasks/task-1/progress')
    expect(result).toEqual(mockProgress)
  })
})

describe('searchService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should search with filters', async () => {
    const mockResponse = {
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      totalPages: 0,
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockResponse } as any)

    const filters = { query: 'test', type: 'movie' as const }
    const result = await searchService.search(filters, 1, 20)

    expect(result).toEqual(mockResponse)
  })

  it('should get search suggestions', async () => {
    const mockSuggestions = ['test1', 'test2', 'test3']
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockSuggestions } as any)

    const result = await searchService.getSuggestions('test', 3)

    expect(result).toEqual(mockSuggestions)
  })

  it('should get recent searches', async () => {
    const mockRecent = ['search1', 'search2']
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockRecent } as any)

    const result = await searchService.getRecentSearches(10)

    expect(result).toEqual(mockRecent)
  })
})
