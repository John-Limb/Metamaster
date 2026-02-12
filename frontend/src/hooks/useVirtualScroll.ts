import { useState, useCallback, useRef, useEffect, useMemo } from 'react'

interface UseVirtualScrollOptions {
  itemHeight: number
  overscan?: number
  useWindow?: boolean
}

interface VirtualScrollResult {
  containerStyle: React.CSSProperties
  scrollToIndex: (index: number, align?: 'start' | 'center' | 'end') => void
  scrollToTop: () => void
}

export function useVirtualScroll<T extends HTMLElement>(
  itemCount: number,
  options: UseVirtualScrollOptions
): VirtualScrollResult {
  const { itemHeight, overscan = 3, useWindow = false } = options
  const containerRef = useRef<T>(null)
  const scrollTopRef = useRef(0)
  const [viewportHeight, setViewportHeight] = useState(0)

  // Update viewport height
  useEffect(() => {
    const updateViewportHeight = () => {
      if (useWindow) {
        setViewportHeight(window.innerHeight)
      } else if (containerRef.current) {
        setViewportHeight(containerRef.current.clientHeight)
      }
    }

    updateViewportHeight()
    window.addEventListener('resize', updateViewportHeight)
    return () => window.removeEventListener('resize', updateViewportHeight)
  }, [useWindow])

  // Calculate visible range
  const { startIndex, endIndex } = useMemo(() => {
    if (viewportHeight === 0 || itemCount === 0) {
      return { startIndex: 0, endIndex: 0 }
    }

    const scrollTop = useWindow ? window.scrollY : scrollTopRef.current
    const startNode = scrollTop - itemHeight * overscan
    const endNode = scrollTop + viewportHeight + itemHeight * overscan

    const startIndex = Math.max(0, Math.floor(startNode / itemHeight))
    const endIndex = Math.min(
      itemCount - 1,
      Math.floor(endNode / itemHeight)
    )

    return { startIndex, endIndex }
  }, [viewportHeight, itemCount, itemHeight, overscan, useWindow])

  // Track scroll position
  useEffect(() => {
    const handleScroll = () => {
      if (useWindow) {
        scrollTopRef.current = window.scrollY
      }
    }

    if (useWindow) {
      window.addEventListener('scroll', handleScroll, { passive: true })
      return () => window.removeEventListener('scroll', handleScroll)
    }
  }, [useWindow])

  const scrollToIndex = useCallback(
    (index: number, align: 'start' | 'center' | 'end' = 'start') => {
      if (!containerRef.current) return

      const container = containerRef.current
      const maxScrollTop = (itemCount - 1) * itemHeight
      let targetScrollTop: number

      switch (align) {
        case 'center':
          targetScrollTop = index * itemHeight - viewportHeight / 2 + itemHeight / 2
          break
        case 'end':
          targetScrollTop = index * itemHeight - viewportHeight + itemHeight
          break
        default:
          targetScrollTop = index * itemHeight
      }

      targetScrollTop = Math.max(0, Math.min(targetScrollTop, maxScrollTop))

      if (useWindow) {
        window.scrollTo({ top: targetScrollTop, behavior: 'smooth' })
      } else {
        container.scrollTo({ top: targetScrollTop, behavior: 'smooth' })
      }
    },
    [itemCount, itemHeight, viewportHeight, useWindow]
  )

  const scrollToTop = useCallback(() => {
    if (useWindow) {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } else if (containerRef.current) {
      containerRef.current.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }, [useWindow])

  const containerStyle: React.CSSProperties = {
    position: 'relative',
    height: itemCount * itemHeight,
    width: '100%',
  }

  const innerStyle: React.CSSProperties = {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    transform: `translateY(${startIndex * itemHeight}px)`,
  }

  return {
    containerStyle: useWindow ? {} : containerStyle,
    scrollToIndex,
    scrollToTop,
  }
}

export default useVirtualScroll
