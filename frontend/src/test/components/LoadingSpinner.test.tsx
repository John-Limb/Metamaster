import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

describe('LoadingSpinner Component', () => {
  it('should render spinner with default size', () => {
    render(<LoadingSpinner />)

    const spinner = screen.getByRole('status')
    expect(spinner).toBeInTheDocument()
  })

  it('should render spinner with small size', () => {
    render(<LoadingSpinner size="sm" />)

    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('w-6 h-6')
  })

  it('should render spinner with medium size', () => {
    render(<LoadingSpinner size="md" />)

    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('w-12 h-12')
  })

  it('should render spinner with large size', () => {
    render(<LoadingSpinner size="lg" />)

    const spinner = screen.getByRole('status')
    expect(spinner).toHaveClass('w-16 h-16')
  })

  it('should render fullscreen spinner', () => {
    render(<LoadingSpinner fullScreen />)

    const fullscreenContainer = screen.getByTestId('loading-fullscreen')
    expect(fullscreenContainer).toBeInTheDocument()
    expect(fullscreenContainer).toHaveClass('fixed inset-0')
  })

  it('should render fullscreen spinner with overlay', () => {
    render(<LoadingSpinner fullScreen overlay={true} />)

    const fullscreenContainer = screen.getByTestId('loading-fullscreen')
    expect(fullscreenContainer).toHaveClass('bg-opacity-75')
  })

  it('should render fullscreen spinner without overlay', () => {
    render(<LoadingSpinner fullScreen overlay={false} />)

    const fullscreenContainer = screen.getByTestId('loading-fullscreen')
    expect(fullscreenContainer).not.toHaveClass('bg-opacity-75')
  })

  it('should render message when provided', () => {
    render(<LoadingSpinner message="Loading data..." />)

    expect(screen.getByText('Loading data...')).toBeInTheDocument()
  })

  it('should not render message when not provided', () => {
    render(<LoadingSpinner />)

    expect(screen.queryByRole('paragraph')).not.toBeInTheDocument()
  })

  it('should have animation class', () => {
    render(<LoadingSpinner />)

    const spinnerInner = screen.getByTestId('spinner-inner')
    expect(spinnerInner).toHaveClass('animate-spin')
  })
})
