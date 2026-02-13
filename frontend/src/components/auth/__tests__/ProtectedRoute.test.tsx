import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { ProtectedRoute } from '../ProtectedRoute'

// Mock useAuth hook
const mockUseAuth = vi.fn()

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}))

// Mock LoadingSpinner component
vi.mock('@/components/common/LoadingSpinner', () => ({
  LoadingSpinner: ({ message }: { message: string }) => (
    <div data-testid="loading-spinner">{message}</div>
  ),
}))

// Helper to render with router
function renderWithRouter(
  ui: React.ReactElement,
  { initialEntries = ['/protected'] }: { initialEntries?: string[] } = {}
) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <Routes>
        <Route path="/login" element={<div data-testid="login-page">Login Page</div>} />
        <Route path="/change-password" element={<div data-testid="change-password-page">Change Password Page</div>} />
        <Route path="/" element={<div data-testid="home-page">Home Page</div>} />
        <Route path="/protected" element={ui} />
      </Routes>
    </MemoryRouter>
  )
}

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('loading state', () => {
    it('should show loading state when isLoading is true', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: true,
        requiresPasswordChange: false,
      })

      renderWithRouter(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument()
      expect(screen.getByText('Checking authentication...')).toBeInTheDocument()
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
    })
  })

  describe('unauthenticated state', () => {
    it('should redirect to /login when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        requiresPasswordChange: false,
      })

      renderWithRouter(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('login-page')).toBeInTheDocument()
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
    })

    it('should not render children when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        isLoading: false,
        requiresPasswordChange: false,
      })

      renderWithRouter(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
    })
  })

  describe('authenticated state', () => {
    it('should render children when authenticated', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        requiresPasswordChange: false,
      })

      renderWithRouter(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
      expect(screen.queryByTestId('login-page')).not.toBeInTheDocument()
      expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument()
    })

    it('should render children when authenticated without password change requirement', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        requiresPasswordChange: false,
      })

      renderWithRouter(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
    })
  })

  describe('password change requirement', () => {
    it('should redirect to /change-password when requiresPasswordChange is true', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        requiresPasswordChange: true,
      })

      renderWithRouter(
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('change-password-page')).toBeInTheDocument()
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
    })

    it('should render children when requirePasswordChange prop is true and user needs password change', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        requiresPasswordChange: true,
      })

      renderWithRouter(
        <ProtectedRoute requirePasswordChange>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('protected-content')).toBeInTheDocument()
      expect(screen.queryByTestId('change-password-page')).not.toBeInTheDocument()
    })

    it('should redirect to home when requirePasswordChange prop is true but user does not need password change', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        isLoading: false,
        requiresPasswordChange: false,
      })

      renderWithRouter(
        <ProtectedRoute requirePasswordChange>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      )

      expect(screen.getByTestId('home-page')).toBeInTheDocument()
      expect(screen.queryByTestId('protected-content')).not.toBeInTheDocument()
    })
  })
})
