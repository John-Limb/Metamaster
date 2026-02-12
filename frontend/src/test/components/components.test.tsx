import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { Toast } from '@/components/common/Toast'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { ErrorModal } from '@/components/common/ErrorModal'

describe('Component Tests', () => {
  describe('LoadingSpinner', () => {
    it('should render with default props', () => {
      render(<LoadingSpinner />)
      const spinner = screen.getByRole('status')
      expect(spinner).toBeInTheDocument()
    })

    it('should render with custom size', () => {
      render(<LoadingSpinner size="lg" />)
      const spinner = screen.getByRole('status')
      expect(spinner).toBeInTheDocument()
    })

    it('should render with message', () => {
      render(<LoadingSpinner message="Loading..." />)
      expect(screen.getByText('Loading...')).toBeInTheDocument()
    })
  })

  describe('Toast', () => {
    it('should render success toast', () => {
      render(<Toast id="1" type="success" message="Test message" onClose={() => {}} />)
      expect(screen.getByText('Test message')).toBeInTheDocument()
    })

    it('should render error toast', () => {
      render(<Toast id="1" type="error" message="Test error message" onClose={() => {}} />)
      expect(screen.getByRole('status')).toBeInTheDocument()
    })

    it('should call onClose when close button is clicked', () => {
      const onClose = vi.fn()
      render(<Toast id="1" type="success" message="Test message" onClose={onClose} />)
      
      fireEvent.click(screen.getByRole('button'))
      expect(onClose).toHaveBeenCalled()
    })
  })

  describe('ConfirmDialog', () => {
    it('should render dialog with title and message', () => {
      render(
        <ConfirmDialog
          isOpen={true}
          title="Delete File"
          message="Are you sure you want to delete this file?"
          onConfirm={() => {}}
          onCancel={() => {}}
        />
      )
      expect(screen.getByText('Delete File')).toBeInTheDocument()
      expect(screen.getByText('Are you sure you want to delete this file?')).toBeInTheDocument()
    })

    it('should call onConfirm when confirm button is clicked', () => {
      const onConfirm = vi.fn()
      render(
        <ConfirmDialog
          isOpen={true}
          title="Test"
          message="Test message"
          onConfirm={onConfirm}
          onCancel={() => {}}
        />
      )
      
      fireEvent.click(screen.getByText('Confirm'))
      expect(onConfirm).toHaveBeenCalled()
    })

    it('should call onCancel when cancel button is clicked', () => {
      const onCancel = vi.fn()
      render(
        <ConfirmDialog
          isOpen={true}
          title="Test"
          message="Test message"
          onConfirm={() => {}}
          onCancel={onCancel}
        />
      )
      
      fireEvent.click(screen.getByText('Cancel'))
      expect(onCancel).toHaveBeenCalled()
    })
  })

  describe('ErrorBoundary', () => {
    const ErrorComponent = () => {
      throw new Error('Test error')
    }

    it('should render children when no error', () => {
      render(
        <ErrorBoundary>
          <div>Working content</div>
        </ErrorBoundary>
      )
      expect(screen.getByText('Working content')).toBeInTheDocument()
    })

    it('should render error message when child throws', () => {
      render(
        <ErrorBoundary>
          <ErrorComponent />
        </ErrorBoundary>
      )
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })
  })

  describe('ErrorModal', () => {
    it('should render modal when open', () => {
      render(
        <ErrorModal
          isOpen={true}
          title="Error"
          message="An error occurred"
          onClose={() => {}}
        />
      )
      expect(screen.getByText('Error')).toBeInTheDocument()
      expect(screen.getByText('An error occurred')).toBeInTheDocument()
    })

    it('should not render when closed', () => {
      render(
        <ErrorModal
          isOpen={false}
          title="Error"
          message="An error occurred"
          onClose={() => {}}
        />
      )
      expect(screen.queryByText('Error')).not.toBeInTheDocument()
    })
  })
})
