import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Breadcrumb } from '@/components/common/Breadcrumb'

describe('Breadcrumb Component', () => {
  const renderBreadcrumb = (items: { label: string; path?: string; onClick?: () => void }[]) => {
    return render(
      <BrowserRouter>
        <Breadcrumb items={items} />
      </BrowserRouter>
    )
  }

  it('should render breadcrumb items', () => {
    renderBreadcrumb([
      { label: 'Home', path: '/' },
      { label: 'Movies', path: '/movies' },
      { label: 'Action' },
    ])

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Movies')).toBeInTheDocument()
    expect(screen.getByText('Action')).toBeInTheDocument()
  })

  it('should render links for items with path', () => {
    renderBreadcrumb([
      { label: 'Home', path: '/' },
      { label: 'Movies', path: '/movies' },
    ])

    const homeLink = screen.getByText('Home')
    expect(homeLink.closest('a')).toHaveAttribute('href', '/')
    
    const moviesLink = screen.getByText('Movies')
    expect(moviesLink.closest('a')).toHaveAttribute('href', '/movies')
  })

  it('should render buttons for items with onClick', () => {
    const handleClick = vi.fn()
    renderBreadcrumb([
      { label: 'Home', path: '/' },
      { label: 'Action', onClick: handleClick },
    ])

    const actionButton = screen.getByText('Action')
    fireEvent.click(actionButton)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('should show home icon when showHome is true', () => {
    render(
      <BrowserRouter>
        <Breadcrumb items={[{ label: 'Movies' }]} showHome={true} />
      </BrowserRouter>
    )

    expect(screen.getByTestId('home-icon')).toBeInTheDocument()
  })

  it('should render custom separator', () => {
    render(
      <BrowserRouter>
        <Breadcrumb
          items={[
            { label: 'Home' },
            { label: 'Movies' },
          ]}
          separator={<span data-testid="custom-separator">/</span>}
        />
      </BrowserRouter>
    )

    expect(screen.getByTestId('custom-separator')).toBeInTheDocument()
  })

  it('should apply custom className', () => {
    render(
      <BrowserRouter>
        <Breadcrumb
          items={[{ label: 'Test' }]}
          className="custom-class"
        />
      </BrowserRouter>
    )

    expect(screen.getByRole('navigation')).toHaveClass('custom-class')
  })

  it('should handle empty items array', () => {
    render(
      <BrowserRouter>
        <Breadcrumb items={[]} />
      </BrowserRouter>
    )

    expect(screen.getByRole('navigation')).toBeInTheDocument()
    expect(screen.queryByRole('listitem')).not.toBeInTheDocument()
  })
})
