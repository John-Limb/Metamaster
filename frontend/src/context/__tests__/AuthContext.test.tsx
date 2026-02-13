import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider, useAuth } from '../AuthContext'
import type { ReactNode } from 'react'

// Mock the auth service
vi.mock('@/services/authService', () => ({
  authService: {
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    changePassword: vi.fn(),
    refreshToken: vi.fn(),
  },
  AuthApiError: class AuthApiError extends Error {
    constructor(message: string) {
      super(message)
      this.name = 'AuthApiError'
    }
  },
}))

// Test component to access auth context
function AuthTestComponent() {
  const auth = useAuth()
  return (
    <div>
      <span data-testid="is-authenticated">{auth.isAuthenticated.toString()}</span>
      <span data-testid="is-loading">{auth.isLoading.toString()}</span>
      <span data-testid="user">{auth.user ? auth.user.username : 'null'}</span>
      <span data-testid="error">{auth.error || 'null'}</span>
      <span data-testid="requires-password-change">{auth.requiresPasswordChange.toString()}</span>
      <button onClick={auth.clearError} data-testid="clear-error-btn">
        Clear Error
      </button>
    </div>
  )
}

// Helper to render with router
function renderWithRouter(ui: ReactNode) {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  describe('AuthProvider', () => {
    it('should render children', () => {
      renderWithRouter(
        <AuthProvider>
          <div data-testid="child">Child Content</div>
        </AuthProvider>
      )

      expect(screen.getByTestId('child')).toBeInTheDocument()
      expect(screen.getByText('Child Content')).toBeInTheDocument()
    })

    it('should have initial unauthenticated state', async () => {
      renderWithRouter(
        <AuthProvider>
          <AuthTestComponent />
        </AuthProvider>
      )

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByTestId('is-loading').textContent).toBe('false')
      })

      expect(screen.getByTestId('is-authenticated').textContent).toBe('false')
      expect(screen.getByTestId('user').textContent).toBe('null')
      expect(screen.getByTestId('error').textContent).toBe('null')
      expect(screen.getByTestId('requires-password-change').textContent).toBe('false')
    })
  })

  describe('clearError', () => {
    it('should clear error state when called', async () => {
      const { authService, AuthApiError } = await import('@/services/authService')
      
      // Mock login to fail
      vi.mocked(authService.login).mockRejectedValueOnce(
        new AuthApiError('Invalid credentials')
      )

      // Test component that can trigger login
      function TestComponentWithLogin() {
        const auth = useAuth()
        return (
          <div>
            <span data-testid="error">{auth.error || 'null'}</span>
            <button 
              onClick={() => auth.login({ username: 'test', password: 'wrong' }).catch(() => {})} 
              data-testid="login-btn"
            >
              Login
            </button>
            <button onClick={auth.clearError} data-testid="clear-error-btn">
              Clear Error
            </button>
          </div>
        )
      }

      renderWithRouter(
        <AuthProvider>
          <TestComponentWithLogin />
        </AuthProvider>
      )

      // Wait for initial loading to complete
      await waitFor(() => {
        expect(screen.getByTestId('error').textContent).toBe('null')
      })

      // Trigger login to cause an error
      await act(async () => {
        screen.getByTestId('login-btn').click()
      })

      // Verify error is set
      await waitFor(() => {
        expect(screen.getByTestId('error').textContent).toBe('Invalid credentials')
      })

      // Clear the error
      await act(async () => {
        screen.getByTestId('clear-error-btn').click()
      })

      // Verify error is cleared
      expect(screen.getByTestId('error').textContent).toBe('null')
    })
  })

  describe('useAuth hook', () => {
    it('should throw error when used outside AuthProvider', () => {
      // Suppress console.error for this test
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      function TestComponentOutsideProvider() {
        useAuth()
        return null
      }

      expect(() => render(<TestComponentOutsideProvider />)).toThrow(
        'useAuth must be used within an AuthProvider'
      )

      consoleSpy.mockRestore()
    })

    it('should return auth context when used inside AuthProvider', async () => {
      renderWithRouter(
        <AuthProvider>
          <AuthTestComponent />
        </AuthProvider>
      )

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.getByTestId('is-loading').textContent).toBe('false')
      })

      // Verify context values are accessible
      expect(screen.getByTestId('is-authenticated')).toBeInTheDocument()
      expect(screen.getByTestId('user')).toBeInTheDocument()
      expect(screen.getByTestId('error')).toBeInTheDocument()
    })
  })
})
