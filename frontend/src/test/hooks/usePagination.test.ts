import { describe, it, expect, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { usePagination, useOffsetPagination, useCursorPagination } from '@/hooks/usePagination'

describe('usePagination Hook', () => {
  beforeEach(() => {
    // Reset localStorage before each test
    localStorage.clear()
  })

  describe('usePagination', () => {
    it('should return initial pagination state', () => {
      const { result } = renderHook(() => usePagination(1, 20, 100))

      expect(result.current.page).toBe(1)
      expect(result.current.pageSize).toBe(20)
      expect(result.current.total).toBe(100)
      expect(result.current.totalPages).toBe(5)
      expect(result.current.canGoNext).toBe(true)
      expect(result.current.canGoPrev).toBe(false)
    })

    it('should go to specific page', () => {
      const { result } = renderHook(() => usePagination(1, 20, 100))

      act(() => {
        result.current.goToPage(3)
      })

      expect(result.current.page).toBe(3)
      expect(result.current.canGoNext).toBe(true)
      expect(result.current.canGoPrev).toBe(true)
    })

    it('should not go to invalid page', () => {
      const { result } = renderHook(() => usePagination(1, 20, 100))

      act(() => {
        result.current.goToPage(0)
      })

      expect(result.current.page).toBe(1)

      act(() => {
        result.current.goToPage(6)
      })

      expect(result.current.page).toBe(1)
    })

    it('should navigate to next page', () => {
      const { result } = renderHook(() => usePagination(1, 20, 100))

      act(() => {
        result.current.nextPage()
      })

      expect(result.current.page).toBe(2)
    })

    it('should not navigate past last page', () => {
      const { result } = renderHook(() => usePagination(5, 20, 100))

      act(() => {
        result.current.nextPage()
      })

      expect(result.current.page).toBe(5)
    })

    it('should navigate to previous page', () => {
      const { result } = renderHook(() => usePagination(3, 20, 100))

      act(() => {
        result.current.prevPage()
      })

      expect(result.current.page).toBe(2)
    })

    it('should not navigate past first page', () => {
      const { result } = renderHook(() => usePagination(1, 20, 100))

      act(() => {
        result.current.prevPage()
      })

      expect(result.current.page).toBe(1)
    })

    it('should change page size', () => {
      const { result } = renderHook(() => usePagination(3, 20, 100))

      act(() => {
        result.current.setPageSize(50)
      })

      expect(result.current.pageSize).toBe(50)
      expect(result.current.page).toBe(1) // Should reset to first page
      expect(result.current.totalPages).toBe(2)
    })

    it('should reset to initial state', () => {
      const { result } = renderHook(() => usePagination(1, 20, 100))

      act(() => {
        result.current.goToPage(5)
        result.current.setPageSize(10)
      })

      act(() => {
        result.current.reset()
      })

      expect(result.current.page).toBe(1)
      expect(result.current.pageSize).toBe(20)
    })

    it('should handle zero total items', () => {
      const { result } = renderHook(() => usePagination(1, 20, 0))

      expect(result.current.totalPages).toBe(1)
    })
  })

  describe('useOffsetPagination', () => {
    it('should return initial offset pagination state', () => {
      const { result } = renderHook(() => useOffsetPagination(0, 20, 100))

      expect(result.current.offset).toBe(0)
      expect(result.current.limit).toBe(20)
      expect(result.current.currentPage).toBe(1)
      expect(result.current.totalPages).toBe(5)
    })

    it('should calculate offset from page', () => {
      const { result } = renderHook(() => useOffsetPagination(0, 20, 100))

      act(() => {
        result.current.goToPage(3)
      })

      expect(result.current.offset).toBe(40)
      expect(result.current.currentPage).toBe(3)
    })

    it('should set limit and reset offset', () => {
      const { result } = renderHook(() => useOffsetPagination(40, 20, 100))

      act(() => {
        result.current.setLimit(50)
      })

      expect(result.current.limit).toBe(50)
      expect(result.current.offset).toBe(0)
    })
  })

  describe('useCursorPagination', () => {
    it('should return initial cursor pagination state', () => {
      const { result } = renderHook(() => useCursorPagination('cursor-1', 20))

      expect(result.current.cursor).toBe('cursor-1')
      expect(result.current.pageSize).toBe(20)
      expect(result.current.canGoPrev).toBe(false)
    })

    it('should go to next page', () => {
      const { result } = renderHook(() => useCursorPagination('cursor-1', 20))

      act(() => {
        result.current.goToNextPage('cursor-2')
      })

      expect(result.current.cursor).toBe('cursor-2')
      expect(result.current.canGoPrev).toBe(true)
    })

    it('should go to previous page', () => {
      const { result } = renderHook(() => useCursorPagination('cursor-2', 20))

      act(() => {
        result.current.goToPreviousPage()
      })

      expect(result.current.cursor).toBe('cursor-1')
      expect(result.current.canGoPrev).toBe(false)
    })

    it('should reset to initial cursor', () => {
      const { result } = renderHook(() => useCursorPagination('cursor-1', 20))

      act(() => {
        result.current.goToNextPage('cursor-2')
        result.current.goToNextPage('cursor-3')
      })

      act(() => {
        result.current.reset()
      })

      expect(result.current.cursor).toBe('cursor-1')
    })
  })
})
