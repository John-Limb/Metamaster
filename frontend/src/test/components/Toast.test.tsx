import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { Toast, ToastContainer } from '@/components/common/Toast'
import type { Toast as ToastType } from '@/types'

describe('Toast Component', () => {
  const mockOnClose = vi.fn()

  const renderToast = (props: Partial<Parameters<typeof Toast>[0]> = {}) => {
    return render(
      <Toast
        id="test-toast"
        type="success"
        message="Test message"
        onClose={mockOnClose}
        {...props}
      />
    )
  }

  it('should render success toast', () => {
    renderToast({ type: 'success' })

    expect(screen.getByRole('alert')).toHaveClass('bg-green-50')
    expect(screen.getByTestId('toast-icon')).toBeInTheDocument()
  })

  it('should render error toast', () => {
    renderToast({ type: 'error' })

    expect(screen.getByRole('alert')).toHaveClass('bg-red-50')
  })

  it('should render warning toast', () => {
    renderToast({ type: 'warning' })

    expect(screen.getByRole('alert')).toHaveClass('bg-yellow-50')
  })

  it('should render info toast', () => {
    renderToast({ type: 'info' })

    expect(screen.getByRole('alert')).toHaveClass('bg-blue-50')
  })

  it('should display message', () => {
    renderToast({ message: 'Custom message' })

    expect(screen.getByText('Custom message')).toBeInTheDocument()
  })

  it('should call onClose when close button is clicked', () => {
    renderToast()

    const closeButton = screen.getByRole('button', { name: 'Close notification' })
    fireEvent.click(closeButton)

    expect(mockOnClose).toHaveBeenCalledTimes(1)
  })

  it('should auto-close after duration', () => {
    vi.useFakeTimers()
    renderToast({ duration: 100 })

    expect(mockOnClose).not.toHaveBeenCalled()

    act(() => {
      vi.advanceTimersByTime(100)
    })

    expect(mockOnClose).toHaveBeenCalledTimes(1)

    vi.useRealTimers()
  })

  it('should not auto-close when duration is 0', () => {
    vi.useFakeTimers()
    renderToast({ duration: 0 })

    act(() => {
      vi.advanceTimersByTime(10000)
    })

    expect(mockOnClose).not.toHaveBeenCalled()

    vi.useRealTimers()
  })

  it('should have animation class', () => {
    renderToast()

    expect(screen.getByRole('alert')).toHaveClass('animate-slide-in')
  })
})

describe('ToastContainer Component', () => {
  const toasts: ToastType[] = [
    { id: '1', type: 'success', message: 'Success message' },
    { id: '2', type: 'error', message: 'Error message' },
    { id: '3', type: 'warning', message: 'Warning message' },
  ]

  const mockOnRemoveToast = vi.fn()

  it('should render multiple toasts', () => {
    render(<ToastContainer toasts={toasts} onRemoveToast={mockOnRemoveToast} />)

    expect(screen.getByText('Success message')).toBeInTheDocument()
    expect(screen.getByText('Error message')).toBeInTheDocument()
    expect(screen.getByText('Warning message')).toBeInTheDocument()
  })

  it('should render empty container when no toasts', () => {
    render(<ToastContainer toasts={[]} onRemoveToast={mockOnRemoveToast} />)

    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('should have correct positioning', () => {
    render(<ToastContainer toasts={toasts} onRemoveToast={mockOnRemoveToast} />)

    const container = screen.getByTestId('toast-container')
    expect(container).toHaveClass('fixed bottom-4 right-4')
  })

  it('should render toasts in vertical stack', () => {
    render(<ToastContainer toasts={toasts} onRemoveToast={mockOnRemoveToast} />)

    const container = screen.getByTestId('toast-container')
    expect(container).toHaveClass('flex flex-col gap-2')
  })
})
