import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useDebounce, useDebouncedCallback, useDebouncedSearch, useDebouncedFilter } from '@/hooks/useDebounce'

describe('useDebounce Hook', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('useDebounce', () => {
    it('should return initial value immediately', () => {
      const { result } = renderHook(() => useDebounce('initial', 100))
      expect(result.current).toBe('initial')
    })

    it('should update value after delay', () => {
      const { result, rerender } = renderHook(({ value }) => useDebounce(value, 100), {
        initialProps: { value: 'initial' },
      })

      rerender({ value: 'updated' })
      expect(result.current).toBe('initial')

      vi.advanceTimersByTime(100)
      expect(result.current).toBe('updated')
    })

    it('should use default delay of 500ms', () => {
      const { result, rerender } = renderHook(({ value }) => useDebounce(value), {
        initialProps: { value: 'initial' },
      })

      rerender({ value: 'updated' })

      vi.advanceTimersByTime(499)
      expect(result.current).toBe('initial')

      vi.advanceTimersByTime(1)
      expect(result.current).toBe('updated')
    })
  })

  describe('useDebouncedCallback', () => {
    it('should debounce callback execution', () => {
      const callback = vi.fn()
      const { result } = renderHook(() => useDebouncedCallback(callback, 100))

      result.current('arg1')
      expect(callback).not.toHaveBeenCalled()

      result.current('arg2')
      expect(callback).not.toHaveBeenCalled()

      vi.advanceTimersByTime(100)
      expect(callback).toHaveBeenCalledTimes(1)
      expect(callback).toHaveBeenCalledWith('arg2')
    })
  })

  describe('useDebouncedSearch', () => {
    it('should debounce search query', () => {
      const { result, rerender } = renderHook(({ query }) => useDebouncedSearch(query, 200), {
        initialProps: { query: '' },
      })

      rerender({ query: 'test' })
      expect(result.current).toBe('')

      vi.advanceTimersByTime(200)
      expect(result.current).toBe('test')
    })
  })

  describe('useDebouncedFilter', () => {
    it('should debounce filter object', () => {
      const filter = { search: '', category: 'all' }
      const { result, rerender } = renderHook(({ filter }) => useDebouncedFilter(filter, 100), {
        initialProps: { filter },
      })

      const newFilter = { search: 'new', category: 'all' }
      rerender({ filter: newFilter })
      expect(result.current).toEqual(filter)

      vi.advanceTimersByTime(100)
      expect(result.current).toEqual(newFilter)
    })
  })
})
