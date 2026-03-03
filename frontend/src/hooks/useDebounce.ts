import { useState, useEffect } from 'react'

/**
 * Hook to debounce a value
 * @param value - The value to debounce
 * @param delay - The delay in milliseconds
 * @returns The debounced value
 */
export const useDebounce = <T>(value: T, delay: number = 500): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])

  return debouncedValue
}

/**
 * Hook to debounce a callback function
 * @param callback - The callback function to debounce
 * @param delay - The delay in milliseconds
 * @returns The debounced callback function
 */
export const useDebouncedCallback = <T extends (...args: Parameters<T>) => ReturnType<T>>(
  callback: T,
  delay: number = 500
): ((...args: Parameters<T>) => void) => {
  const [timeoutId, setTimeoutId] = useState<ReturnType<typeof setTimeout> | null>(null)

  const debouncedCallback = (...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }

    const newTimeoutId = setTimeout(() => {
      callback(...args)
    }, delay)

    setTimeoutId(newTimeoutId)
  }

  return debouncedCallback
}

/**
 * Hook to debounce a search query
 * @param query - The search query
 * @param delay - The delay in milliseconds
 * @returns The debounced query
 */
export const useDebouncedSearch = (query: string, delay: number = 300): string => {
  return useDebounce(query, delay)
}

/**
 * Hook to debounce a filter
 * @param filter - The filter object
 * @param delay - The delay in milliseconds
 * @returns The debounced filter
 */
export const useDebouncedFilter = <T extends Record<string, unknown>>(
  filter: T,
  delay: number = 500
): T => {
  return useDebounce(filter, delay)
}
