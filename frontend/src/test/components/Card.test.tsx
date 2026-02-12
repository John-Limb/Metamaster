import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Card } from '@/components/common/Card'

describe('Card', () => {
  it('renders card with children', () => {
    render(<Card>Card content</Card>)
    const card = screen.getByText('Card content')
    expect(card).toBeInTheDocument()
  })

  it('applies default variant', () => {
    render(<Card>Default</Card>)
    const card = screen.getByText('Default')
    expect(card).toHaveClass('bg-white')
    expect(card).toHaveClass('border')
  })

  it('applies elevated variant', () => {
    render(<Card variant="elevated">Elevated</Card>)
    const card = screen.getByText('Elevated')
    expect(card).toHaveClass('shadow-medium')
  })

  it('applies outlined variant', () => {
    render(<Card variant="outlined">Outlined</Card>)
    const card = screen.getByText('Outlined')
    expect(card).toHaveClass('border-2')
    expect(card).toHaveClass('bg-transparent')
  })

  it('applies different padding sizes', () => {
    const { rerender } = render(<Card padding="none">None</Card>)
    let card = screen.getByText('None')
    expect(card).toHaveClass('p-0')

    rerender(<Card padding="sm">Small</Card>)
    card = screen.getByText('Small')
    expect(card).toHaveClass('p-3')

    rerender(<Card padding="md">Medium</Card>)
    card = screen.getByText('Medium')
    expect(card).toHaveClass('p-5')

    rerender(<Card padding="lg">Large</Card>)
    card = screen.getByText('Large')
    expect(card).toHaveClass('p-6')
  })

  it('shows loading state with shimmer', () => {
    render(<Card loading>Content</Card>)
    const card = screen.getByRole('button')
    expect(card).toBeInTheDocument()
    expect(card).toHaveClass('relative')
    expect(card).toHaveClass('overflow-hidden')
  })

  it('renders as button when onClick is provided', () => {
    render(<Card onClick={() => {}}>Clickable</Card>)
    const card = screen.getByRole('button')
    expect(card).toBeInTheDocument()
    expect(card).toHaveClass('cursor-pointer')
  })

  it('renders as button when hoverable is true', () => {
    render(<Card hoverable>Hoverable</Card>)
    const card = screen.getByRole('button')
    expect(card).toBeInTheDocument()
  })

  it('calls onClick handler', () => {
    const handleClick = vi.fn()
    render(<Card onClick={handleClick}>Click</Card>)
    const card = screen.getByRole('button')
    fireEvent.click(card)
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('applies hover lift effect', () => {
    render(<Card hoverable>Hover</Card>)
    const card = screen.getByRole('button')
    expect(card).toHaveClass('hover:-translate-y-0.5')
    expect(card).toHaveClass('transition-all')
  })

  it('applies custom className', () => {
    render(<Card className="custom-card">Custom</Card>)
    const card = screen.getByText('Custom')
    expect(card).toHaveClass('custom-card')
  })

  it('renders Card.Header', () => {
    render(
      <Card>
        <Card.Header>Header</Card.Header>
        Content
      </Card>
    )
    expect(screen.getByText('Header')).toBeInTheDocument()
    expect(screen.getByText('Header').parentElement).toHaveClass('border-b')
  })

  it('renders Card.Content', () => {
    render(
      <Card>
        <Card.Content>Content</Card.Content>
      </Card>
    )
    expect(screen.getByText('Content')).toBeInTheDocument()
  })

  it('renders Card.Footer', () => {
    render(
      <Card>
        <Card.Footer>Footer</Card.Footer>
      </Card>
    )
    expect(screen.getByText('Footer')).toBeInTheDocument()
    expect(screen.getByText('Footer').parentElement).toHaveClass('border-t')
  })

  it('has rounded corners', () => {
    render(<Card>Rounded</Card>)
    const card = screen.getByText('Rounded')
    expect(card).toHaveClass('rounded-lg')
  })

  it('supports dark mode', () => {
    document.documentElement.classList.add('dark')
    render(<Card>Dark</Card>)
    const card = screen.getByText('Dark')
    expect(card).toHaveClass('dark:bg-secondary-800')
    document.documentElement.classList.remove('dark')
  })

  it('has proper focus styles for interactive cards', () => {
    render(<Card onClick={() => {}}>Interactive</Card>)
    const card = screen.getByRole('button')
    expect(card).toHaveAttribute('tabIndex', '0')
  })
})
