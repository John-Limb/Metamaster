import { apiClient } from '@/utils/api'
import { errorHandler } from '@/utils/errorHandler'
import type { QueueTask, QueueStats, PaginatedResponse, ApiResponse } from '@/types'

export const queueService = {
  // Get queue tasks
  getTasks: async (page = 1, pageSize = 20, status?: string) => {
    try {
      const params = new URLSearchParams()
      params.append('page', String(page))
      params.append('pageSize', String(pageSize))
      if (status) params.append('status', status)

      const response = await apiClient.get<PaginatedResponse<QueueTask>>(
        `/queue/tasks?${params.toString()}`
      )
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `getTasks: page=${page}, status=${status}`)
      throw error
    }
  },

  // Get queue statistics
  getStats: async () => {
    try {
      const response = await apiClient.get<QueueStats>('/queue/stats')
      return response.data
    } catch (error) {
      errorHandler.handleError(error, 'getStats')
      throw error
    }
  },

  // Get task details
  getTaskDetails: async (id: string) => {
    try {
      const response = await apiClient.get<QueueTask>(`/queue/tasks/${id}`)
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `getTaskDetails: ${id}`)
      throw error
    }
  },

  // Retry failed task
  retryTask: async (id: string) => {
    try {
      const response = await apiClient.post<QueueTask>(`/queue/tasks/${id}/retry`)
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `retryTask: ${id}`)
      throw error
    }
  },

  // Cancel task
  cancelTask: async (id: string) => {
    try {
      const response = await apiClient.post<ApiResponse<void>>(`/queue/tasks/${id}/cancel`)
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `cancelTask: ${id}`)
      throw error
    }
  },

  // Clear completed tasks
  clearCompletedTasks: async () => {
    try {
      const response = await apiClient.post<ApiResponse<void>>('/queue/clear-completed')
      return response.data
    } catch (error) {
      errorHandler.handleError(error, 'clearCompletedTasks')
      throw error
    }
  },

  // Get task progress
  getTaskProgress: async (id: string) => {
    try {
      const response = await apiClient.get<{ progress: number; status: string }>(
        `/queue/tasks/${id}/progress`
      )
      return response.data
    } catch (error) {
      errorHandler.handleError(error, `getTaskProgress: ${id}`)
      throw error
    }
  },
}
