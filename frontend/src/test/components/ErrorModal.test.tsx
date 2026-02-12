import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ErrorModal } from '@/components/common/ErrorModal'

describe('ErrorModal Component', () => {
  const mockOnClose = vi.fn()
  const mockOnRetry = vi.fn()

  const renderModal = (props: Partial<Parameters<typeof ErrorModal>[0]> = {}) => {
    return render(
      <ErrorModal
        isOpen={true}
        message="An error occurred"
        onClose={mockOnClose}
        {...props}
      />
    )
  }

  it('should render modal when isOpen is true', () => {
    renderModal()

    expect(screen.getByText('Error')).toBeInTheDocument()
    expect(screen.getByText('An error occurred')).toBeInTheDocument()
  })

  it('should not render when isOpen is false', () => {
    renderModal({ isOpen: false })

    expect(screen.queryByRole('heading', { name: 'Error' })).not.toBeInTheDocument()
  })

  it('should render custom title', () => {
    renderModal({ title: 'Custom Title' })

    expect(screen.getByText('Custom Title')).toBeInTheDocument()
  })

  it('should render error details when provided', () => {
    renderModal({ details: 'Error details here' })

    expect(screen.getByText('Error Details')).toBeInTheDocument()
  })

  it('should hide error details by default', () => {
    renderModal({ details: 'Error details here' })

    const detailsElement = screen.getByText('Error Details')
    fireEvent.click(detailsElement.closest('details')!)

    expect(screen.getByText('Error details here')).toBeInTheDocument()
  })

  it('should render Close button', () => {
    renderModal()

    expect(screen.getByRole('button', { name: 'Close' })).toBeInTheDocument()
  })

  it('should render Retry button when onRetry is provided', () => {
    renderModal({ onRetry: mockOnRetry })

    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
  })

  it('should hide Retry button when onRetry is not provided', () => {
    renderModal()

    expect(screen.queryByRole('button', { name: 'Retry' })).not.toBeInTheDocument()
  })

  it('should call onRetry when Retry button is clicked', () => {
    renderModal({ onRetry: mockOnRetry })

    const retryButton = screen.getByRole('button', { name: 'Retry' })
    fireEvent.click(retryButton)

    expect(mockOnRetry).toHaveBeenCalledTimes(1)
  })

  it('should show retry loading state', () => {
    renderModal({ onRetry: mockOnRetry, isRetrying: true })

    expect(screen.getByRole('button', { name: 'Retrying...' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retrying...' })).toBeDisabled()
  })

  it('should close when Close button is clicked', () => {
    renderModal()

    const closeButton = screen.getByRole('button', { name: 'Close' })
    fireEvent.click(closeButton)

    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('should close when backdrop is clicked', () => {
    renderModal()

    const backdrop = screen.getByTestId('modal-backdrop')
    fireEvent.click(backdrop)

    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('should have error styling', () => {
    renderModal()

    expect(screen.getByTestId('modal-header')).toHaveClass('bg-red-50')
    expect(screen.getByTestId('error-icon')).toBeInTheDocument()
  })
})
