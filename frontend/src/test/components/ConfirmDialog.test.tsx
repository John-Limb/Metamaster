import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'

describe('ConfirmDialog Component', () => {
  const mockOnConfirm = vi.fn()
  const mockOnCancel = vi.fn()

  const renderDialog = (props: Partial<Parameters<typeof ConfirmDialog>[0]> = {}) => {
    return render(
      <ConfirmDialog
        isOpen={true}
        title="Test Dialog"
        message="Are you sure?"
        onConfirm={mockOnConfirm}
        onCancel={mockOnCancel}
        {...props}
      />
    )
  }

  it('should render dialog when isOpen is true', () => {
    renderDialog()

    expect(screen.getByText('Test Dialog')).toBeInTheDocument()
    expect(screen.getByText('Are you sure?')).toBeInTheDocument()
  })

  it('should not render when isOpen is false', () => {
    renderDialog({ isOpen: false })

    expect(screen.queryByRole('heading', { name: 'Test Dialog' })).not.toBeInTheDocument()
  })

  it('should render confirm and cancel buttons', () => {
    renderDialog()

    expect(screen.getByRole('button', { name: 'Confirm' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument()
  })

  it('should call onConfirm when confirm button is clicked', () => {
    renderDialog()

    const confirmButton = screen.getByRole('button', { name: 'Confirm' })
    fireEvent.click(confirmButton)

    expect(mockOnConfirm).toHaveBeenCalledTimes(1)
  })

  it('should call onCancel when cancel button is clicked', () => {
    renderDialog()

    const cancelButton = screen.getByRole('button', { name: 'Cancel' })
    fireEvent.click(cancelButton)

    expect(mockOnCancel).toHaveBeenCalledTimes(1)
  })

  it('should show warning icon when isDangerous is true', () => {
    renderDialog({ isDangerous: true })

    expect(screen.getByTestId('warning-icon')).toBeInTheDocument()
  })

  it('should change confirm button color when isDangerous is true', () => {
    renderDialog({ isDangerous: true })

    const confirmButton = screen.getByRole('button', { name: 'Confirm' })
    expect(confirmButton).toHaveClass('bg-red-600')
  })

  it('should show loading state when isLoading is true', () => {
    renderDialog({ isLoading: true })

    expect(screen.getByRole('button', { name: 'Loading...' })).toBeInTheDocument()
  })

  it('should disable buttons when isLoading is true', () => {
    renderDialog({ isLoading: true })

    const confirmButton = screen.getByRole('button', { name: 'Loading...' })
    const cancelButton = screen.getByRole('button', { name: 'Cancel' })

    expect(confirmButton).toBeDisabled()
    expect(cancelButton).toBeDisabled()
  })

  it('should render custom button text', () => {
    renderDialog({
      confirmText: 'Yes, Delete',
      cancelText: 'No, Keep',
    })

    expect(screen.getByRole('button', { name: 'Yes, Delete' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'No, Keep' })).toBeInTheDocument()
  })

  it('should close when backdrop is clicked', () => {
    renderDialog()

    const backdrop = screen.getByTestId('dialog-backdrop')
    fireEvent.click(backdrop)

    expect(mockOnCancel).toHaveBeenCalledTimes(1)
  })

  it('should not close when dialog content is clicked', () => {
    renderDialog()

    const dialogContent = screen.getByTestId('dialog-content')
    fireEvent.click(dialogContent)

    expect(mockOnCancel).not.toHaveBeenCalled()
  })
})
