/**
 * Authentication service for handling auth API calls
 *
 * Uses fetch API with credentials: 'include' to support cookie-based refresh tokens.
 * The backend sets refresh tokens as httpOnly cookies that are automatically sent
 * with requests when credentials are included.
 */

import type {
  User,
  LoginCredentials,
  RegisterData,
  LoginResponse,
  RefreshResponse,
  ChangePasswordData,
  AuthError,
  MessageResponse,
} from '@/types/auth'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

/**
 * Custom error class for authentication errors
 */
export class AuthApiError extends Error {
  public statusCode: number
  public errorCode?: string

  constructor(message: string, statusCode: number, errorCode?: string) {
    super(message)
    this.name = 'AuthApiError'
    this.statusCode = statusCode
    this.errorCode = errorCode
  }
}

/**
 * Helper function to make authenticated API requests
 */
async function authFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  const defaultHeaders: HeadersInit = {
    'Content-Type': 'application/json',
  }

  // Get the access token from localStorage for authenticated requests
  const token = localStorage.getItem('authToken')
  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`
  }

  const config: RequestInit = {
    ...options,
    credentials: 'include', // Required for cookie-based refresh tokens
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  }

  const response = await fetch(url, config)

  if (!response.ok) {
    let errorMessage = 'An error occurred'
    let errorCode: string | undefined

    try {
      const errorData: AuthError = await response.json()
      errorMessage = errorData.detail || errorMessage
      errorCode = errorData.error_code
    } catch {
      // Response body is not valid JSON
      errorMessage = response.statusText || errorMessage
    }

    throw new AuthApiError(errorMessage, response.status, errorCode)
  }

  // Handle empty responses (e.g., 204 No Content)
  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    return response.json()
  }

  return {} as T
}

/**
 * Authentication service object with methods for all auth operations
 */
export const authService = {
  /**
   * Login with username and password
   * Returns access token and user data on success
   */
  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    const response = await authFetch<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    })

    // Store the access token in localStorage
    if (response.access_token) {
      localStorage.setItem('authToken', response.access_token)
    }

    return response
  },

  /**
   * Register a new user
   * Returns the created user data on success
   */
  register: async (data: RegisterData): Promise<User> => {
    return authFetch<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  /**
   * Logout the current user
   * Invalidates the refresh token cookie on the server
   */
  logout: async (): Promise<void> => {
    try {
      await authFetch<void>('/auth/logout', {
        method: 'POST',
      })
    } finally {
      // Always clear the local token, even if the API call fails
      localStorage.removeItem('authToken')
    }
  },

  /**
   * Refresh the access token using the refresh token cookie
   * Returns a new access token on success
   */
  refreshToken: async (): Promise<RefreshResponse> => {
    const response = await authFetch<RefreshResponse>('/auth/refresh', {
      method: 'POST',
    })

    // Update the stored access token
    if (response.access_token) {
      localStorage.setItem('authToken', response.access_token)
    }

    return response
  },

  /**
   * Get the current authenticated user
   * Returns user data if the access token is valid
   */
  getCurrentUser: async (): Promise<User> => {
    return authFetch<User>('/auth/me', {
      method: 'GET',
    })
  },

  /**
   * Change the current user's password
   * Returns a success message on completion
   */
  changePassword: async (data: ChangePasswordData): Promise<MessageResponse> => {
    return authFetch<MessageResponse>('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
}

export default authService
