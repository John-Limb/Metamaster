import { apiClient } from '@/utils/api'
import { errorHandler } from '@/utils/errorHandler'

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'not_ready' | 'ready' | 'alive'
  message: string
}

export interface DetailedHealthCheck {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  checks: Record<string, { status: string; [key: string]: unknown }>
}

export interface MetricsPayload {
  system: Record<string, unknown>
  application: Record<string, unknown>
  database: Record<string, unknown>
  cache: Record<string, unknown>
  tasks: Record<string, unknown>
}

export const healthService = {
  // Get overall health status
  getHealth: async () => {
    try {
      const response = await apiClient.get<HealthStatus>('/health/')
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'getHealth')
      throw error
    }
  },

  getDetailedHealth: async () => {
    try {
      const response = await apiClient.get<DetailedHealthCheck>('/health/detailed')
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'getDetailedHealth')
      throw error
    }
  },

  getMetrics: async () => {
    try {
      const response = await apiClient.get<MetricsPayload>('/health/metrics')
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'getMetrics')
      throw error
    }
  },

  isReady: async () => {
    try {
      const response = await apiClient.get<HealthStatus>('/health/ready')
      return response.data.status === 'ready'
    } catch (error: any) {
      errorHandler.handleError(error, 'isReady')
      return false
    }
  },

  isAlive: async () => {
    try {
      const response = await apiClient.get<HealthStatus>('/health/live')
      return response.data.status === 'alive'
    } catch (error: any) {
      errorHandler.handleError(error, 'isAlive')
      return false
    }
  },
}
