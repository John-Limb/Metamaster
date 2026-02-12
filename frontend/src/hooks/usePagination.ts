import { useState, useCallback } from 'react'

export interface PaginationState {
  page: number
  pageSize: number
  total: number
  totalPages: number
}

export interface UsePaginationReturn extends PaginationState {
  goToPage: (page: number) => void
  nextPage: () => void
  prevPage: () => void
  setPageSize: (size: number) => void
  reset: () => void
  canGoNext: boolean
  canGoPrev: boolean
}

/**
 * Hook to manage pagination state
 * @param initialPage - Initial page number (default: 1)
 * @param initialPageSize - Initial page size (default: 20)
 * @param total - Total number of items
 * @returns Pagination state and methods
 */
export const usePagination = (
  initialPage: number = 1,
  initialPageSize: number = 20,
  total: number = 0
): UsePaginationReturn => {
  const [page, setPage] = useState(initialPage)
  const [pageSize, setPageSizeState] = useState(initialPageSize)

  const totalPages = Math.ceil(total / pageSize) || 1

  const goToPage = useCallback((newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setPage(newPage)
    }
  }, [totalPages])

  const nextPage = useCallback(() => {
    if (page < totalPages) {
      setPage((prev) => prev + 1)
    }
  }, [page, totalPages])

  const prevPage = useCallback(() => {
    if (page > 1) {
      setPage((prev) => prev - 1)
    }
  }, [page])

  const setPageSize = useCallback((size: number) => {
    if (size > 0) {
      setPageSizeState(size)
      setPage(1) // Reset to first page when page size changes
    }
  }, [])

  const reset = useCallback(() => {
    setPage(initialPage)
    setPageSizeState(initialPageSize)
  }, [initialPage, initialPageSize])

  return {
    page,
    pageSize,
    total,
    totalPages,
    goToPage,
    nextPage,
    prevPage,
    setPageSize,
    reset,
    canGoNext: page < totalPages,
    canGoPrev: page > 1,
  }
}

/**
 * Hook to manage pagination with offset-based API
 * @param initialOffset - Initial offset (default: 0)
 * @param initialLimit - Initial limit (default: 20)
 * @param total - Total number of items
 * @returns Pagination state with offset/limit
 */
export const useOffsetPagination = (
  initialOffset: number = 0,
  initialLimit: number = 20,
  total: number = 0
) => {
  const [offset, setOffset] = useState(initialOffset)
  const [limit, setLimitState] = useState(initialLimit)

  const totalPages = Math.ceil(total / limit) || 1
  const currentPage = Math.floor(offset / limit) + 1

  const goToPage = useCallback(
    (page: number) => {
      if (page >= 1 && page <= totalPages) {
        setOffset((page - 1) * limit)
      }
    },
    [limit, totalPages]
  )

  const nextPage = useCallback(() => {
    if (currentPage < totalPages) {
      setOffset((prev) => prev + limit)
    }
  }, [currentPage, totalPages, limit])

  const prevPage = useCallback(() => {
    if (offset > 0) {
      setOffset((prev) => Math.max(0, prev - limit))
    }
  }, [offset, limit])

  const setLimit = useCallback((newLimit: number) => {
    if (newLimit > 0) {
      setLimitState(newLimit)
      setOffset(0) // Reset to beginning when limit changes
    }
  }, [])

  const reset = useCallback(() => {
    setOffset(initialOffset)
    setLimitState(initialLimit)
  }, [initialOffset, initialLimit])

  return {
    offset,
    limit,
    total,
    totalPages,
    currentPage,
    goToPage,
    nextPage,
    prevPage,
    setLimit,
    reset,
    canGoNext: currentPage < totalPages,
    canGoPrev: offset > 0,
  }
}

/**
 * Hook to manage cursor-based pagination
 * @param initialCursor - Initial cursor (default: null)
 * @param pageSize - Page size (default: 20)
 * @returns Pagination state with cursor
 */
export const useCursorPagination = (initialCursor: string | null = null, pageSize: number = 20) => {
  const [cursor, setCursor] = useState<string | null>(initialCursor)
  const [previousCursors, setPreviousCursors] = useState<(string | null)[]>([initialCursor])

  const goToNextPage = useCallback((nextCursor: string | null) => {
    setPreviousCursors((prev) => [...prev, cursor])
    setCursor(nextCursor)
  }, [cursor])

  const goToPreviousPage = useCallback(() => {
    setPreviousCursors((prev) => prev.slice(0, -1))
    setCursor(previousCursors[previousCursors.length - 2] || null)
  }, [previousCursors])

  const reset = useCallback(() => {
    setCursor(initialCursor)
    setPreviousCursors([initialCursor])
  }, [initialCursor])

  return {
    cursor,
    pageSize,
    goToNextPage,
    goToPreviousPage,
    reset,
    canGoPrev: previousCursors.length > 1,
  }
}
