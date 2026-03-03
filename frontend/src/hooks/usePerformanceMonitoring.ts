import { useEffect, useRef, useCallback, useState } from 'react'

interface PerformanceMetrics {
  fcp: number | null // First Contentful Paint
  lcp: number | null // Largest Contentful Paint
  fid: number | null // First Input Delay
  cls: number | null // Cumulative Layout Shift
  ttfb: number | null // Time to First Byte
}

interface UsePerformanceMonitoringOptions {
  enabled?: boolean
  onReport?: (metrics: PerformanceMetrics) => void
}

interface LayoutShiftEntry extends PerformanceEntry {
  hadRecentInput: boolean
  value: number
}

export function usePerformanceMonitoring(options: UsePerformanceMonitoringOptions = {}) {
  const { enabled = true, onReport } = options
  const metricsRef = useRef<PerformanceMetrics>({
    fcp: null,
    lcp: null,
    fid: null,
    cls: null,
    ttfb: null,
  })
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fcp: null,
    lcp: null,
    fid: null,
    cls: null,
    ttfb: null,
  })

  const reportMetrics = useCallback(() => {
    setMetrics({ ...metricsRef.current })
    if (onReport) {
      onReport(metricsRef.current)
    }
    // Log to console in development
    if (import.meta.env.DEV) {
      console.log('Performance Metrics:', metricsRef.current)
    }
  }, [onReport])

  useEffect(() => {
    if (!enabled) return

    // Time to First Byte (TTFB)
    const navigationEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined
    if (navigationEntry) {
      metricsRef.current.ttfb = navigationEntry.responseStart - navigationEntry.requestStart
    }

    // First Contentful Paint (FCP)
    const fcpEntry = performance.getEntriesByType('paint').find((entry) => entry.name === 'first-contentful-paint')
    if (fcpEntry) {
      metricsRef.current.fcp = fcpEntry.startTime
    }

    // Largest Contentful Paint (LCP)
    const observer = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      const lastEntry = entries[entries.length - 1] as PerformanceEntry
      metricsRef.current.lcp = lastEntry.startTime
    })

    try {
      observer.observe({ type: 'largest-contentful-paint', buffered: true })
    } catch {
      // LCP not supported
    }

    // First Input Delay (FID)
    const fidObserver = new PerformanceObserver((list) => {
      const firstInput = list.getEntries()[0] as PerformanceEventTiming
      if (firstInput) {
        metricsRef.current.fid = firstInput.processingStart - firstInput.startTime
      }
    })

    try {
      fidObserver.observe({ type: 'first-input', buffered: true })
    } catch {
      // FID not supported
    }

    // Cumulative Layout Shift (CLS)
    let clsValue = 0
    const clsObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries()
      entries.forEach((entry) => {
        const layoutEntry = entry as LayoutShiftEntry
        if (!layoutEntry.hadRecentInput) {
          clsValue += layoutEntry.value
        }
      })
      metricsRef.current.cls = clsValue
    })

    try {
      clsObserver.observe({ type: 'layout-shift', buffered: true })
    } catch {
      // CLS not supported
    }

    // Report metrics when page is hidden or after a delay
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden') {
        reportMetrics()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    // Also report after a delay to capture LCP
    const timeoutId = setTimeout(reportMetrics, 5000)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      clearTimeout(timeoutId)
      observer.disconnect()
      fidObserver.disconnect()
      clsObserver.disconnect()
    }
  }, [enabled, reportMetrics])

  return metrics
}

export default usePerformanceMonitoring
