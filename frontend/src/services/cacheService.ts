import { apiClient } from '@/utils/api'
import { errorHandler } from '@/utils/errorHandler'
import type { ApiResponse } from '@/types'

export interface CacheStats {
  totalSize: number
  itemCount: number
  hitRate: number
  missRate: number
}

export interface CacheItem {
  key: string
  size: number
  createdAt: string
  expiresAt?: string
}

export const cacheService = {
  // Get cache statistics
  getStats: async () => {
    try {
      const response = await apiClient.get<CacheStats>('/cache/stats')
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'getStats')
      throw error
    }
  },

  // Get all cache items
  getItems: async (page = 1, pageSize = 20) => {
    try {
      const response = await apiClient.get<{ items: CacheItem[]; total: number }>(
        `/cache/items?page=${page}&pageSize=${pageSize}`
      )
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `getItems: page=${page}`)
      throw error
    }
  },

  // Get cache item by key
  getItem: async (key: string) => {
    try {
      const response = await apiClient.get<CacheItem>(`/cache/items/${encodeURIComponent(key)}`)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `getItem: ${key}`)
      throw error
    }
  },

  // Clear specific cache key
  clearKey: async (key: string) => {
    try {
      const response = await apiClient.delete<ApiResponse<void>>(
        `/cache/items/${encodeURIComponent(key)}`
      )
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `clearKey: ${key}`)
      throw error
    }
  },

  // Clear all cache
  clearAll: async () => {
    try {
      const response = await apiClient.post<ApiResponse<void>>('/cache/clear')
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'clearAll')
      throw error
    }
  },

  // Clear cache by pattern
  clearByPattern: async (pattern: string) => {
    try {
      const response = await apiClient.post<ApiResponse<void>>('/cache/clear-pattern', {
        pattern,
      })
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `clearByPattern: ${pattern}`)
      throw error
    }
  },

  // Warm up cache
  warmUp: async () => {
    try {
      const response = await apiClient.post<ApiResponse<void>>('/cache/warmup')
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'warmUp')
      throw error
    }
  },

  // Get cache configuration
  getConfig: async () => {
    try {
      const response = await apiClient.get<Record<string, any>>('/cache/config')
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'getConfig')
      throw error
    }
  },
}
