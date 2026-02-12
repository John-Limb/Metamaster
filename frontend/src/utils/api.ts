import axios, { AxiosError } from 'axios'
import type { AxiosInstance, AxiosResponse, AxiosRequestConfig } from 'axios'
import type { ApiError } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000')
const MAX_RETRIES = parseInt(import.meta.env.VITE_MAX_RETRIES || '3')
const RETRY_DELAY = parseInt(import.meta.env.VITE_RETRY_DELAY || '1000')

interface RetryConfig extends AxiosRequestConfig {
  retryCount?: number
}

class ApiClient {
  private client: AxiosInstance
  private retryCount: Map<string, number> = new Map()

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('authToken')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        // Add request ID for tracking
        config.headers['X-Request-ID'] = this.generateRequestId()
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor with retry logic
    this.client.interceptors.response.use(
      (response) => {
        // Clear retry count on success
        const requestId = response.config.headers['X-Request-ID'] as string
        if (requestId) {
          this.retryCount.delete(requestId)
        }
        return response
      },
      async (error: AxiosError) => {
        const config = error.config as RetryConfig
        const requestId = config?.headers?.['X-Request-ID'] as string

        // Handle 401 Unauthorized
        if (error.response?.status === 401) {
          localStorage.removeItem('authToken')
          window.location.href = '/login'
          return Promise.reject(this.handleError(error))
        }

        // Retry logic for specific status codes
        if (this.shouldRetry(error) && config) {
          const currentRetry = this.retryCount.get(requestId) || 0
          if (currentRetry < MAX_RETRIES) {
            this.retryCount.set(requestId, currentRetry + 1)
            const delay = RETRY_DELAY * Math.pow(2, currentRetry) // Exponential backoff
            await this.sleep(delay)
            return this.client(config)
          }
        }

        return Promise.reject(this.handleError(error))
      }
    )
  }

  private shouldRetry(error: AxiosError): boolean {
    // Retry on network errors or specific status codes
    if (!error.response) {
      return true // Network error
    }
    // Retry on 408 (Request Timeout), 429 (Too Many Requests), 5xx errors
    const retryableStatuses = [408, 429, 500, 502, 503, 504]
    return retryableStatuses.includes(error.response.status)
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  private handleError(error: AxiosError): ApiError {
    if (error.response) {
      return {
        code: String(error.response.status),
        message: (error.response.data as any)?.message || error.message,
        details: (error.response.data as Record<string, any>) || undefined,
      }
    } else if (error.request) {
      return {
        code: 'NETWORK_ERROR',
        message: 'Network error occurred',
      }
    } else {
      return {
        code: 'ERROR',
        message: error.message,
      }
    }
  }

  public get<T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get<T>(url, config)
  }

  public get defaults() {
    return this.client.defaults
  }

  public post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post<T>(url, data, config)
  }

  public put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put<T>(url, data, config)
  }

  public patch<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.patch<T>(url, data, config)
  }

  public delete<T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.delete<T>(url, config)
  }
}

export const apiClient = new ApiClient()
