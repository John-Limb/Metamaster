import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act, waitFor } from '@testing-library/react'
import { useFileStore } from '@/stores/fileStore'
import { useQueueStore } from '@/stores/queueStore'
import type { FileItem, QueueTask } from '@/types'

// Mock the file service
vi.mock('@/services/fileService', () => ({
  fileService: {
    getFiles: vi.fn(),
    deleteFile: vi.fn(),
    batchDeleteFiles: vi.fn(),
    batchMoveFiles: vi.fn(),
    getFileStats: vi.fn(),
  },
}))

// Mock the queue service
vi.mock('@/services/queueService', () => ({
  queueService: {
    getTasks: vi.fn(),
    getStats: vi.fn(),
    clearCompletedTasks: vi.fn(),
    retryTask: vi.fn(),
    cancelTask: vi.fn(),
  },
}))

describe('useFileStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useFileStore())

    expect(result.current.files).toEqual([])
    expect(result.current.selectedFiles).toEqual([])
    expect(result.current.currentPath).toBe('/')
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('should set files', () => {
    const mockFiles: FileItem[] = [
      { id: 'file-1', name: 'file1.mp4', path: '/videos', type: 'file', size: 1000, createdAt: '', updatedAt: '' },
      { id: 'file-2', name: 'file2.mp4', path: '/videos', type: 'file', size: 2000, createdAt: '', updatedAt: '' },
    ]

    const { result } = renderHook(() => useFileStore())

    act(() => {
      result.current.setFiles(mockFiles)
    })

    expect(result.current.files).toEqual(mockFiles)
  })

  it('should add a file', () => {
    const { result } = renderHook(() => useFileStore())

    const newFile: FileItem = { id: 'file-3', name: 'file3.mp4', path: '/videos', type: 'file', size: 3000, createdAt: '', updatedAt: '' }

    act(() => {
      result.current.addFile(newFile)
    })

    expect(result.current.files).toHaveLength(1)
    expect(result.current.files[0]).toEqual(newFile)
  })

  it('should remove a file', () => {
    const { result } = renderHook(() => useFileStore())

    act(() => {
      result.current.setFiles([
        { id: 'file-1', name: 'file1.mp4', path: '/videos', type: 'file', size: 1000, createdAt: '', updatedAt: '' },
        { id: 'file-2', name: 'file2.mp4', path: '/videos', type: 'file', size: 2000, createdAt: '', updatedAt: '' },
      ])
    })

    act(() => {
      result.current.removeFile('file-1')
    })

    expect(result.current.files).toHaveLength(1)
    expect(result.current.files[0].id).toBe('file-2')
  })

  it('should select a file', () => {
    const { result } = renderHook(() => useFileStore())

    act(() => {
      result.current.selectFile('file-1')
    })

    expect(result.current.selectedFiles).toEqual(['file-1'])
  })

  it('should deselect a file', () => {
    const { result } = renderHook(() => useFileStore())

    act(() => {
      result.current.selectFile('file-1')
      result.current.selectFile('file-2')
    })

    act(() => {
      result.current.deselectFile('file-1')
    })

    expect(result.current.selectedFiles).toEqual(['file-2'])
  })

  it('should toggle file selection', () => {
    const { result } = renderHook(() => useFileStore())

    act(() => {
      result.current.toggleFileSelection('file-1')
    })

    expect(result.current.selectedFiles).toEqual(['file-1'])

    act(() => {
      result.current.toggleFileSelection('file-1')
    })

    expect(result.current.selectedFiles).toEqual([])
  })

  it('should select multiple files', () => {
    const { result } = renderHook(() => useFileStore())

    act(() => {
      result.current.selectMultiple(['file-1', 'file-2', 'file-3'])
    })

    expect(result.current.selectedFiles).toEqual(['file-1', 'file-2', 'file-3'])
  })

  it('should clear selection', () => {
    const { result } = renderHook(() => useFileStore())

    act(() => {
      result.current.selectMultiple(['file-1', 'file-2'])
      result.current.clearSelection()
    })

    expect(result.current.selectedFiles).toEqual([])
  })

  it('should set current path', () => {
    const { result } = renderHook(() => useFileStore())

    act(() => {
      result.current.setCurrentPath('/videos/movies')
    })

    expect(result.current.currentPath).toBe('/videos/movies')
  })

  it('should add recent path', () => {
    const { result } = renderHook(() => useFileStore())

    act(() => {
      result.current.addRecentPath('/videos')
      result.current.addRecentPath('/documents')
      result.current.addRecentPath('/videos') // Should move to top
    })

    expect(result.current.recentPaths).toEqual(['/videos', '/documents'])
  })

  it('should limit recent paths to 10', () => {
    const { result } = renderHook(() => useFileStore())

    for (let i = 0; i < 15; i++) {
      act(() => {
        result.current.addRecentPath(`/path-${i}`)
      })
    }

    expect(result.current.recentPaths).toHaveLength(10)
    expect(result.current.recentPaths[0]).toBe('/path-14')
  })

  it('should set loading state', () => {
    const { result } = renderHook(() => useFileStore())

    act(() => {
      result.current.setIsLoading(true)
    })

    expect(result.current.isLoading).toBe(true)
  })

  it('should set error state', () => {
    const { result } = renderHook(() => useFileStore())

    act(() => {
      result.current.setError('Test error')
    })

    expect(result.current.error).toBe('Test error')
  })

  it('should clear error', () => {
    const { result } = renderHook(() => useFileStore())

    act(() => {
      result.current.setError('Test error')
      result.current.setError(null)
    })

    expect(result.current.error).toBeNull()
  })
})

describe('useQueueStore', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('should initialize with default values', () => {
    const { result } = renderHook(() => useQueueStore())

    expect(result.current.tasks).toEqual([])
    expect(result.current.stats).toBeNull()
    expect(result.current.isLoading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(result.current.pollingEnabled).toBe(true)
  })

  it('should set tasks', () => {
    const mockTasks: QueueTask[] = [
      { id: 'task-1', type: 'analyze', status: 'pending', progress: 0, createdAt: '', updatedAt: '' },
      { id: 'task-2', type: 'sync', status: 'processing', progress: 50, createdAt: '', updatedAt: '' },
    ]

    const { result } = renderHook(() => useQueueStore())

    act(() => {
      result.current.setTasks(mockTasks)
    })

    expect(result.current.tasks).toEqual(mockTasks)
  })

  it('should add a task', () => {
    const { result } = renderHook(() => useQueueStore())

    const newTask: QueueTask = { id: 'task-3', type: 'index', status: 'pending', progress: 0, createdAt: '', updatedAt: '' }

    act(() => {
      result.current.addTask(newTask)
    })

    expect(result.current.tasks).toHaveLength(1)
    expect(result.current.tasks[0]).toEqual(newTask)
  })

  it('should update a task', () => {
    const { result } = renderHook(() => useQueueStore())

    act(() => {
      result.current.setTasks([
        { id: 'task-1', type: 'analyze', status: 'pending', progress: 0, createdAt: '', updatedAt: '' },
      ])
    })

    act(() => {
      result.current.updateTask('task-1', { status: 'processing', progress: 50 })
    })

    expect(result.current.tasks[0].status).toBe('processing')
    expect(result.current.tasks[0].progress).toBe(50)
  })

  it('should remove a task', () => {
    const { result } = renderHook(() => useQueueStore())

    act(() => {
      result.current.setTasks([
        { id: 'task-1', type: 'analyze', status: 'pending', progress: 0, createdAt: '', updatedAt: '' },
        { id: 'task-2', type: 'sync', status: 'processing', progress: 50, createdAt: '', updatedAt: '' },
      ])
    })

    act(() => {
      result.current.removeTask('task-1')
    })

    expect(result.current.tasks).toHaveLength(1)
    expect(result.current.tasks[0].id).toBe('task-2')
  })

  it('should get pending tasks', () => {
    const { result } = renderHook(() => useQueueStore())

    act(() => {
      result.current.setTasks([
        { id: 'task-1', type: 'analyze', status: 'pending', progress: 0, createdAt: '', updatedAt: '' },
        { id: 'task-2', type: 'sync', status: 'completed', progress: 100, createdAt: '', updatedAt: '' },
        { id: 'task-3', type: 'index', status: 'pending', progress: 0, createdAt: '', updatedAt: '' },
      ])
    })

    const pendingTasks = result.current.getPendingTasks()

    expect(pendingTasks).toHaveLength(2)
    expect(pendingTasks.every(t => t.status === 'pending')).toBe(true)
  })

  it('should get failed tasks', () => {
    const { result } = renderHook(() => useQueueStore())

    act(() => {
      result.current.setTasks([
        { id: 'task-1', type: 'analyze', status: 'failed', progress: 0, createdAt: '', updatedAt: '' },
        { id: 'task-2', type: 'sync', status: 'completed', progress: 100, createdAt: '', updatedAt: '' },
        { id: 'task-3', type: 'index', status: 'failed', progress: 0, createdAt: '', updatedAt: '' },
      ])
    })

    const failedTasks = result.current.getFailedTasks()

    expect(failedTasks).toHaveLength(2)
    expect(failedTasks.every(t => t.status === 'failed')).toBe(true)
  })

  it('should get task by id', () => {
    const { result } = renderHook(() => useQueueStore())

    act(() => {
      result.current.setTasks([
        { id: 'task-1', type: 'analyze', status: 'pending', progress: 0, createdAt: '', updatedAt: '' },
        { id: 'task-2', type: 'sync', status: 'processing', progress: 50, createdAt: '', updatedAt: '' },
      ])
    })

    const task = result.current.getTaskById('task-2')
    expect(task?.id).toBe('task-2')
  })

  it('should set status filter', () => {
    const { result } = renderHook(() => useQueueStore())

    act(() => {
      result.current.setStatusFilter('processing')
    })

    expect(result.current.statusFilter).toBe('processing')
  })

  it('should toggle polling', () => {
    const { result } = renderHook(() => useQueueStore())

    act(() => {
      result.current.setPollingEnabled(false)
    })

    expect(result.current.pollingEnabled).toBe(false)
  })

  it('should set polling interval', () => {
    const { result } = renderHook(() => useQueueStore())

    act(() => {
      result.current.setPollingInterval(10000)
    })

    expect(result.current.pollingInterval).toBe(10000)
  })
})
