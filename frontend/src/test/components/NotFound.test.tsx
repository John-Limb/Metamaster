import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { NotFound } from '@/components/common/NotFound'

describe('NotFound Component', () => {
  const renderNotFound = (props: Partial<Parameters<typeof NotFound>[0]> = {}) => {
    return render(
      <MemoryRouter>
        <NotFound {...props} />
      </MemoryRouter>
    )
  }

  it('should render 404 text', () => {
    renderNotFound()

    expect(screen.getByText('404')).toBeInTheDocument()
  })

  it('should render default title', () => {
    renderNotFound()

    expect(screen.getByText('Page Not Found')).toBeInTheDocument()
  })

  it('should render custom title', () => {
    renderNotFound({ title: 'Custom Not Found' })

    expect(screen.getByText('Custom Not Found')).toBeInTheDocument()
  })

  it('should render default message', () => {
    renderNotFound()

    expect(screen.getByText('The page you are looking for does not exist.')).toBeInTheDocument()
  })

  it('should render custom message', () => {
    renderNotFound({ message: 'Custom error message' })

    expect(screen.getByText('Custom error message')).toBeInTheDocument()
  })

  it('should render Go Home button by default', () => {
    renderNotFound()

    expect(screen.getByRole('button', { name: 'Go Home' })).toBeInTheDocument()
  })

  it('should render Go Back button by default', () => {
    renderNotFound()

    expect(screen.getByRole('button', { name: 'Go Back' })).toBeInTheDocument()
  })

  it('should hide Go Back button when showBackButton is false', () => {
    renderNotFound({ showBackButton: false })

    expect(screen.queryByRole('button', { name: 'Go Back' })).not.toBeInTheDocument()
  })

  it('should render SVG icon', () => {
    renderNotFound()

    const icon = screen.getByTestId('not-found-icon')
    expect(icon).toBeInTheDocument()
  })

  it('should navigate to home when Go Home is clicked', () => {
    renderNotFound()

    const goHomeButton = screen.getByRole('button', { name: 'Go Home' })
    fireEvent.click(goHomeButton)

    // Should navigate to home page
    expect(window.location.pathname).toBe('/')
  })
})
