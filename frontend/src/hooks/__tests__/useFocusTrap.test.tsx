import { render, screen, fireEvent } from '@testing-library/react'
import { useRef } from 'react'
import { useFocusTrap } from '../useFocusTrap'

function TrapFixture({ enabled }: { enabled: boolean }) {
  const ref = useRef<HTMLDivElement>(null)
  useFocusTrap(ref, enabled)
  return (
    <div ref={ref}>
      <button data-testid="btn1">First</button>
      <button data-testid="btn2">Second</button>
    </div>
  )
}

describe('useFocusTrap', () => {
  it('focuses the first focusable element when enabled', () => {
    render(<TrapFixture enabled={true} />)
    expect(document.activeElement).toBe(screen.getByTestId('btn1'))
  })

  it('does not move focus when disabled', () => {
    const before = document.activeElement
    render(<TrapFixture enabled={false} />)
    expect(document.activeElement).toBe(before)
  })

  it('wraps Tab from last to first element', () => {
    render(<TrapFixture enabled={true} />)
    const last = screen.getByTestId('btn2')
    last.focus()
    fireEvent.keyDown(document, { key: 'Tab' })
    expect(document.activeElement).toBe(screen.getByTestId('btn1'))
  })

  it('wraps Shift+Tab from first to last element', () => {
    render(<TrapFixture enabled={true} />)
    const first = screen.getByTestId('btn1')
    first.focus()
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true })
    expect(document.activeElement).toBe(screen.getByTestId('btn2'))
  })
})
