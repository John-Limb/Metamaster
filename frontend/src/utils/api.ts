import axios, { AxiosError } from 'axios'
import type { AxiosInstance, AxiosResponse, AxiosRequestConfig } from 'axios'
import type { ApiError } from '@/types'

import { API_BASE_URL, API_TIMEOUT, MAX_RETRIES, RETRY_DELAY } from '@/utils/constants'

interface RetryConfig extends AxiosRequestConfig {
  retryCount?: number
  _retry?: boolean
}

class ApiClient {
  private client: AxiosInstance
  private retryCount: Map<string, number> = new Map()
  private isRefreshing = false
  private refreshSubscribers: Array<(token: string) => void> = []

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

  private onTokenRefreshed(token: string): void {
    this.refreshSubscribers.forEach((callback) => callback(token))
    this.refreshSubscribers = []
  }

  private addRefreshSubscriber(callback: (token: string) => void): void {
    this.refreshSubscribers.push(callback)
  }

  private async attemptTokenRefresh(): Promise<string | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!response.ok) {
        return null
      }

      const data = await response.json()
      if (data.access_token) {
        localStorage.setItem('authToken', data.access_token)
        return data.access_token
      }
      return null
    } catch {
      return null
    }
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

        // Handle 401 Unauthorized - attempt token refresh before redirecting
        if (error.response?.status === 401 && config && !config._retry) {
          if (this.isRefreshing) {
            // Another request is already refreshing, queue this one
            return new Promise((resolve) => {
              this.addRefreshSubscriber((newToken: string) => {
                config.headers = config.headers || {}
                config.headers.Authorization = `Bearer ${newToken}`
                resolve(this.client(config))
              })
            })
          }

          config._retry = true
          this.isRefreshing = true

          const newToken = await this.attemptTokenRefresh()

          if (newToken) {
            this.isRefreshing = false
            this.onTokenRefreshed(newToken)
            config.headers = config.headers || {}
            config.headers.Authorization = `Bearer ${newToken}`
            return this.client(config)
          }

          // Refresh failed - clear auth and redirect
          this.isRefreshing = false
          this.refreshSubscribers = []
          localStorage.removeItem('authToken')
          localStorage.removeItem('tokenExpiry')
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
