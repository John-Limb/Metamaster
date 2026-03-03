/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  type ReactNode,
} from 'react'

import type {
  User,
  LoginCredentials,
  RegisterData,
  ChangePasswordData,
} from '@/types/auth'
import { authService, AuthApiError } from '@/services/authService'

/**
 * Storage keys for auth tokens
 */
const TOKEN_KEY = 'authToken'
const TOKEN_EXPIRY_KEY = 'tokenExpiry'

/**
 * Token refresh configuration
 * Check every 10 minutes, refresh when token expires in less than 5 minutes
 */
const REFRESH_CHECK_INTERVAL = 10 * 60 * 1000 // 10 minutes in milliseconds
const REFRESH_THRESHOLD = 5 * 60 * 1000 // 5 minutes in milliseconds

/**
 * Auth context type definition
 */
interface AuthContextType {
  /** Current authenticated user or null if not authenticated */
  user: User | null
  /** Derived from user presence - true if user is authenticated */
  isAuthenticated: boolean
  /** Loading state for auth operations */
  isLoading: boolean
  /** Error message from last auth operation */
  error: string | null
  /** Flag indicating user must change password before proceeding */
  requiresPasswordChange: boolean
  /** Login with username and password, returns whether password change is required */
  login: (credentials: LoginCredentials) => Promise<{ requiresPasswordChange: boolean }>
  /** Register a new user account */
  register: (data: RegisterData) => Promise<void>
  /** Logout the current user */
  logout: () => Promise<void>
  /** Change the current user's password */
  changePassword: (data: ChangePasswordData) => Promise<void>
  /** Clear the current error state */
  clearError: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

interface AuthProviderProps {
  children: ReactNode
}

/**
 * Authentication context provider
 * 
 * Handles:
 * - User authentication state
 * - Token management and automatic refresh
 * - Login, register, logout, and password change operations
 * - Error handling for auth operations
 */
export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [requiresPasswordChange, setRequiresPasswordChange] = useState(false)
  
  // Use ref for refresh interval to avoid re-renders
  const refreshIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  /**
   * Derive authentication status from user presence
   */
  const isAuthenticated = user !== null

  /**
   * Clear any existing error state
   */
  const clearError = useCallback(() => {
    setError(null)
  }, [])

  /**
   * Store token and its expiry time in localStorage
   */
  const storeToken = useCallback((token: string, expiresIn: number) => {
    localStorage.setItem(TOKEN_KEY, token)
    // Calculate expiry timestamp (current time + expires_in seconds)
    const expiryTime = Date.now() + expiresIn * 1000
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString())
  }, [])

  /**
   * Clear all auth tokens from storage
   */
  const clearTokens = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(TOKEN_EXPIRY_KEY)
  }, [])

  /**
   * Check if token needs refresh (expires in less than threshold)
   */
  const shouldRefreshToken = useCallback((): boolean => {
    const expiryStr = localStorage.getItem(TOKEN_EXPIRY_KEY)
    if (!expiryStr) return false

    const expiry = parseInt(expiryStr, 10)
    const now = Date.now()
    const timeUntilExpiry = expiry - now

    return timeUntilExpiry > 0 && timeUntilExpiry <= REFRESH_THRESHOLD
  }, [])

  /**
   * Refresh the access token
   */
  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      const response = await authService.refreshToken()
      storeToken(response.access_token, response.expires_in)
      return true
    } catch {
      // Refresh failed - clear tokens and user state
      clearTokens()
      setUser(null)
      return false
    }
  }, [storeToken, clearTokens])

  /**
   * Set up automatic token refresh interval
   */
  const setupRefreshInterval = useCallback(() => {
    // Clear any existing interval
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current)
    }

    refreshIntervalRef.current = setInterval(async () => {
      if (shouldRefreshToken()) {
        await refreshToken()
      }
    }, REFRESH_CHECK_INTERVAL)
  }, [shouldRefreshToken, refreshToken])

  /**
   * Fetch current user data on mount if token exists
   */
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem(TOKEN_KEY)
      
      if (!token) {
        setIsLoading(false)
        return
      }

      try {
        const userData = await authService.getCurrentUser()
        setUser(userData)
        
        // Set up token refresh interval
        setupRefreshInterval()
        
        // Check if token needs immediate refresh
        if (shouldRefreshToken()) {
          await refreshToken()
        }
      } catch {
        // Token is invalid or expired - clear it
        clearTokens()
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }

    initializeAuth()

    // Cleanup interval on unmount
    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current)
      }
    }
  }, [clearTokens, refreshToken, setupRefreshInterval, shouldRefreshToken])

  /**
   * Login with credentials
   */
  const login = useCallback(async (credentials: LoginCredentials): Promise<{ requiresPasswordChange: boolean }> => {
    setIsLoading(true)
    setError(null)
    setRequiresPasswordChange(false)

    try {
      const response = await authService.login(credentials)

      // Store token and expiry
      storeToken(response.access_token, response.expires_in)

      // Set user data
      setUser(response.user)

      // Check if password change is required
      const needsPasswordChange = response.requires_password_change ?? false
      if (needsPasswordChange) {
        setRequiresPasswordChange(true)
      }

      // Set up token refresh interval
      setupRefreshInterval()

      return { requiresPasswordChange: needsPasswordChange }
    } catch (err) {
      if (err instanceof AuthApiError) {
        setError(err.message)
      } else {
        setError('An unexpected error occurred during login')
      }
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [storeToken, setupRefreshInterval])

  /**
   * Register a new user
   */
  const register = useCallback(async (data: RegisterData): Promise<void> => {
    setIsLoading(true)
    setError(null)

    try {
      await authService.register(data)
      // After registration, user needs to login
      // We don't automatically log them in
    } catch (err) {
      if (err instanceof AuthApiError) {
        setError(err.message)
      } else {
        setError('An unexpected error occurred during registration')
      }
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  /**
   * Logout the current user
   */
  const logout = useCallback(async (): Promise<void> => {
    setIsLoading(true)
    setError(null)

    try {
      await authService.logout()
    } catch (err) {
      // Even if logout API fails, we clear local state
      if (err instanceof AuthApiError) {
        console.error('Logout API error:', err.message)
      }
    } finally {
      // Always clear local state
      clearTokens()
      setUser(null)
      setRequiresPasswordChange(false)
      
      // Clear refresh interval
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current)
        refreshIntervalRef.current = null
      }
      
      setIsLoading(false)
    }
  }, [clearTokens])

  /**
   * Change the current user's password
   */
  const changePassword = useCallback(async (data: ChangePasswordData): Promise<void> => {
    setIsLoading(true)
    setError(null)

    try {
      await authService.changePassword(data)
      // Clear the requires password change flag on success
      setRequiresPasswordChange(false)
    } catch (err) {
      if (err instanceof AuthApiError) {
        setError(err.message)
      } else {
        setError('An unexpected error occurred while changing password')
      }
      throw err
    } finally {
      setIsLoading(false)
    }
  }, [])

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    error,
    requiresPasswordChange,
    login,
    register,
    logout,
    changePassword,
    clearError,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

/**
 * Hook to access the auth context
 * @throws Error if used outside of AuthProvider
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  
  return context
}

export default AuthContext
