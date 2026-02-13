/**
 * Authentication types matching backend schemas from app/domain/auth/schemas.py
 */

/**
 * User data returned from API responses
 */
export interface User {
  id: number
  username: string
  email: string
  avatar_url: string | null
  created_at: string
}

/**
 * Credentials for login request
 */
export interface LoginCredentials {
  username: string
  password: string
}

/**
 * Data for user registration
 */
export interface RegisterData {
  username: string
  email: string
  password: string
}

/**
 * Response from successful login
 */
export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
  requires_password_change?: boolean
}

/**
 * Response from token refresh
 */
export interface RefreshResponse {
  access_token: string
  token_type: string
  expires_in: number
}

/**
 * Data for password change request
 */
export interface ChangePasswordData {
  current_password: string
  new_password: string
}

/**
 * Error response from auth endpoints
 */
export interface AuthError {
  detail: string
  error_code?: string
}

/**
 * Simple message response
 */
export interface MessageResponse {
  message: string
}
