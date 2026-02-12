import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'

describe('ErrorBoundary Component', () => {
  const mockRetry = vi.fn()

  const errorFallback = (error: Error, retry: () => void) => (
    <div data-testid="custom-fallback">
      <p>Custom error: {error.message}</p>
      <button onClick={retry}>Retry</button>
    </div>
  )

  beforeEach(() => {
    vi.clearAllMocks()
    console.error = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should render children when no error', () => {
    render(
      <ErrorBoundary>
        <div data-testid="children">Test Content</div>
      </ErrorBoundary>
    )

    expect(screen.getByTestId('children')).toBeInTheDocument()
  })

  it('should render error UI when error occurs', () => {
    const ThrowError = () => {
      throw new Error('Test error message')
    }

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('Test error message')).toBeInTheDocument()
  })

  it('should use custom fallback when provided', () => {
    const ThrowError = () => {
      throw new Error('Test error')
    }

    render(
      <ErrorBoundary fallback={errorFallback}>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument()
    expect(screen.getByText('Custom error: Test error')).toBeInTheDocument()
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
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(screen.getByText('Something went wrong')).toBeInTheDocument()

    const tryAgainButton = screen.getByRole('button', { name: 'Try Again' })
    fireEvent.click(tryAgainButton)

    shouldThrow = false
    rerender(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument()
  })

  it('should call onGoHome when Go Home button is clicked', () => {
    const goHomeMock = vi.fn()
    vi.spyOn(window.location, 'href', 'set')

    const ThrowError = () => {
      throw new Error('Test error')
    }

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    const goHomeButton = screen.getByRole('button', { name: 'Go Home' })
    fireEvent.click(goHomeButton)

    expect(window.location.href).toBe('/')
  })
})
