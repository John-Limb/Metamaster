import { renderHook } from '@testing-library/react'
import { fireEvent } from '@testing-library/dom'
import { useEscapeKey } from '../useEscapeKey'

describe('useEscapeKey', () => {
  it('calls handler when Escape is pressed and enabled is true', () => {
    const handler = vi.fn()
    renderHook(() => useEscapeKey(handler, true))
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(handler).toHaveBeenCalledTimes(1)
  })

  it('does not call handler when disabled', () => {
    const handler = vi.fn()
    renderHook(() => useEscapeKey(handler, false))
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(handler).not.toHaveBeenCalled()
  })

  it('does not call handler for non-Escape keys', () => {
    const handler = vi.fn()
    renderHook(() => useEscapeKey(handler))
    fireEvent.keyDown(document, { key: 'Enter' })
    expect(handler).not.toHaveBeenCalled()
  })

  it('removes event listener on unmount', () => {
    const handler = vi.fn()
    const spy = vi.spyOn(document, 'removeEventListener')
    const { unmount } = renderHook(() => useEscapeKey(handler))
    unmount()
    expect(spy).toHaveBeenCalledWith('keydown', expect.any(Function))
  })
})
