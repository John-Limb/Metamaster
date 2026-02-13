import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { LoginForm } from '../LoginForm'

// Mock useAuth hook - default values
const mockLogin = vi.fn()
const mockClearError = vi.fn()

const defaultAuthContext = {
  login: mockLogin,
  clearError: mockClearError,
  error: null as string | null,
  isLoading: false,
  requiresPasswordChange: false,
}

let authContextOverrides = { ...defaultAuthContext }

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => authContextOverrides,
}))

// Mock useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Helper to render with router
function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>)
}

// Helper to reset auth context
function resetAuthContext(overrides: Partial<typeof defaultAuthContext> = {}) {
  authContextOverrides = { ...defaultAuthContext, ...overrides }
}

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    resetAuthContext()
  })

  describe('rendering', () => {
    it('should render with username and password fields', () => {
      renderWithRouter(<LoginForm />)

      // Use more specific selectors to avoid matching the "Show password" button
      expect(screen.getByRole('textbox', { name: /username/i })).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Enter your password')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })

    it('should render the welcome heading', () => {
      renderWithRouter(<LoginForm />)

      expect(screen.getByText('Welcome back')).toBeInTheDocument()
      expect(screen.getByText(/sign in to your account/i)).toBeInTheDocument()
    })

    it('should render link to registration page', () => {
      renderWithRouter(<LoginForm />)

      expect(screen.getByText(/don't have an account/i)).toBeInTheDocument()
      expect(screen.getByRole('link', { name: /create one/i })).toHaveAttribute('href', '/register')
    })

    it('should have required attribute on form fields', () => {
      renderWithRouter(<LoginForm />)

      const usernameInput = screen.getByRole('textbox', { name: /username/i })
      const passwordInput = screen.getByPlaceholderText('Enter your password')

      expect(usernameInput).toBeRequired()
      expect(passwordInput).toBeRequired()
    })
  })

  describe('error display', () => {
    it('should display error from context', () => {
      resetAuthContext({ error: 'Invalid credentials' })

      renderWithRouter(<LoginForm />)

      expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })

    it('should not display error when error is null', () => {
      resetAuthContext({ error: null })

      renderWithRouter(<LoginForm />)

      // Check that no alert is displayed
      const alerts = screen.queryAllByRole('alert')
      // The only alerts should be from validation, not from context error
      expect(alerts.length).toBe(0)
    })
  })

  describe('form structure', () => {
    it('should have a form element', () => {
      renderWithRouter(<LoginForm />)

      // The form should be present
      const form = document.querySelector('form')
      expect(form).toBeInTheDocument()
    })

    it('should have username input with correct attributes', () => {
      renderWithRouter(<LoginForm />)

      const usernameInput = screen.getByRole('textbox', { name: /username/i })
      expect(usernameInput).toHaveAttribute('name', 'username')
      expect(usernameInput).toHaveAttribute('type', 'text')
      expect(usernameInput).toHaveAttribute('autocomplete', 'username')
    })

    it('should have password input with correct attributes', () => {
      renderWithRouter(<LoginForm />)

      const passwordInput = screen.getByPlaceholderText('Enter your password')
      expect(passwordInput).toHaveAttribute('name', 'password')
      expect(passwordInput).toHaveAttribute('type', 'password')
      expect(passwordInput).toHaveAttribute('autocomplete', 'current-password')
    })

    it('should have submit button', () => {
      renderWithRouter(<LoginForm />)

      const submitButton = screen.getByRole('button', { name: /sign in/i })
      expect(submitButton).toHaveAttribute('type', 'submit')
    })
  })
})
