import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ApiErrorBoundary } from '@/components/common/ApiErrorBoundary'
import { errorNotificationManager } from '@/utils/errorNotification'

// Mock the error notification manager
vi.mock('@/utils/errorNotification', () => ({
  errorNotificationManager: {
    showError: vi.fn(),
  },
}))

describe('ApiErrorBoundary Component', () => {
  const mockOnError = vi.fn()
  const mockRetry = vi.fn()

  const errorFallback = (error: any, retry: () => void) => (
    <div data-testid="error-fallback">
      <p>Error: {error.message}</p>
      <button onClick={retry}>Retry</button>
    </div>
  )

  beforeEach(() => {
    vi.clearAllMocks()
    console.error = vi.fn() // Suppress console.error in tests
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should render children when no error', () => {
    render(
      <ApiErrorBoundary>
        <div data-testid="children">Test Content</div>
      </ApiErrorBoundary>
    )

    expect(screen.getByTestId('children')).toBeInTheDocument()
  })

  it('should render error UI when error occurs', () => {
    const ThrowError = () => {
      throw new Error('Test error')
    }

    render(
      <ApiErrorBoundary onError={mockOnError}>
        <ThrowError />
      </ApiErrorBoundary>
    )

    expect(screen.getByText('API Error')).toBeInTheDocument()
    expect(screen.getByText('Test error')).toBeInTheDocument()
    expect(mockOnError).toHaveBeenCalled()
  })

  it('should use custom fallback when provided', () => {
    const ThrowError = () => {
      throw new Error('Test error')
    }

    render(
      <ApiErrorBoundary fallback={errorFallback}>
        <ThrowError />
      </ApiErrorBoundary>
    )

    expect(screen.getByTestId('error-fallback')).toBeInTheDocument()
    expect(screen.getByText('Error: Test error')).toBeInTheDocument()
  })

  it('should reset error when Try Again is clicked', () => {
    let shouldThrow = true
    const ThrowError = () => {
      if (shouldThrow) {
        throw new Error('Test error')
      }
      return <div data-testid="recovered">Recovered</div>
    }

    const { rerender } = render(
      <ApiErrorBoundary>
        <ThrowError />
      </ApiErrorBoundary>
    )

    expect(screen.getByText('API Error')).toBeInTheDocument()

    const tryAgainButton = screen.getByText('Try Again')
    fireEvent.click(tryAgainButton)

    shouldThrow = false
    rerender(
      <ApiErrorBoundary>
        <ThrowError />
      </ApiErrorBoundary>
    )

    expect(screen.queryByText('API Error')).not.toBeInTheDocument()
  })

  it('should track error count', () => {
    const ThrowError = () => {
      throw new Error('Test error')
    }

    const { rerender } = render(
      <ApiErrorBoundary>
        <ThrowError />
      </ApiErrorBoundary>
    )

    expect(screen.getByText('API Error')).toBeInTheDocument()

    // Trigger another error
    const tryAgainButton = screen.getByText('Try Again')
    fireEvent.click(tryAgainButton)

    rerender(
      <ApiErrorBoundary>
        <ThrowError />
      </ApiErrorBoundary>
    )

    // Error count warning should appear after 3 errors
    expect(screen.queryByText('Multiple errors detected')).not.toBeInTheDocument()
  })
})
