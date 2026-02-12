import { useEffect, useCallback, useRef } from 'react'

/**
 * Hook for managing keyboard navigation within a component
 */
export function useKeyboardNavigation(options: {
  onEnter?: () => void
  onEscape?: () => void
  onArrowUp?: () => void
  onArrowDown?: () => void
  onHome?: () => void
  onEnd?: () => void
  itemCount: number
  getItemId: (index: number) => string
  circular?: boolean
}) {
  const {
    onEnter,
    onEscape,
    onArrowUp,
    onArrowDown,
    onHome,
    onEnd,
    itemCount,
    getItemId,
    circular = false,
  } = options

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      const target = event.target as HTMLElement
      const focusableElement = target.closest('[role="option"], [role="menuitem"], [tabindex]')

      if (!focusableElement) return

      const allItems = document.querySelectorAll('[role="option"], [role="menuitem"]')
      const currentIndex = Array.from(allItems).indexOf(focusableElement as HTMLElement)

      switch (event.key) {
        case 'Enter':
          event.preventDefault()
          onEnter?.()
          break

        case 'Escape':
          event.preventDefault()
          onEscape?.()
          break

        case 'ArrowUp':
          event.preventDefault()
          let newIndex = currentIndex - 1
          if (newIndex < 0) {
            newIndex = circular ? itemCount - 1 : 0
          }
          if (newIndex !== currentIndex) {
            onArrowUp?.()
            document.getElementById(getItemId(newIndex))?.focus()
          }
          break

        case 'ArrowDown':
          event.preventDefault()
          let nextIndex = currentIndex + 1
          if (nextIndex >= itemCount) {
            nextIndex = circular ? 0 : itemCount - 1
          }
          if (nextIndex !== currentIndex) {
            onArrowDown?.()
            document.getElementById(getItemId(nextIndex))?.focus()
          }
          break

        case 'Home':
          event.preventDefault()
          onHome?.()
          document.getElementById(getItemId(0))?.focus()
          break

        case 'End':
          event.preventDefault()
          onEnd?.()
          document.getElementById(getItemId(itemCount - 1))?.focus()
          break
      }
    },
    [onEnter, onEscape, onArrowUp, onArrowDown, onHome, onEnd, itemCount, getItemId, circular]
  )

  return { handleKeyDown }
}

/**
 * Hook for trap focus within a modal or dialog
 */
export function useFocusTrap(isActive: boolean = true) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!isActive) return

    const container = containerRef.current
    if (!container) return

    const focusableElements = container.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )

    const firstElement = focusableElements[0]
    const lastElement = focusableElements[focusableElements.length - 1]

    const handleTabKey = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return

      if (event.shiftKey) {
        if (document.activeElement === firstElement) {
          event.preventDefault()
          lastElement?.focus()
        }
      } else {
        if (document.activeElement === lastElement) {
          event.preventDefault()
          firstElement?.focus()
        }
      }
    }

    // Focus the first element when activated
    firstElement?.focus()

    container.addEventListener('keydown', handleTabKey)

    return () => {
      container.removeEventListener('keydown', handleTabKey)
    }
  }, [isActive])

  return containerRef
}

/**
 * Announce a message to screen readers
 */
export function announceToScreenReader(
  message: string,
  priority: 'polite' | 'assertive' = 'polite'
) {
  const announcement = document.createElement('div')
  announcement.setAttribute('role', 'status')
  announcement.setAttribute('aria-live', priority)
  announcement.setAttribute('aria-atomic', 'true')
  announcement.className = 'sr-only'
  announcement.textContent = message

  document.body.appendChild(announcement)

  // Remove after announcement
  setTimeout(() => {
    document.body.removeChild(announcement)
  }, 1000)
}

/**
 * Generate unique IDs for accessibility
 */
let idCounter = 0
export function generateA11yId(prefix: string = 'a11y'): string {
  return `${prefix}-${++idCounter}`
}

/**
 * Focus styles configuration
 */
export const focusStyles = {
  default: 'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
  inset: 'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 focus:ring-inset',
  none: 'focus:outline-none',
}

/**
 * Reduced motion preferences
 */
export function useReducedMotion(): boolean {
  const mediaQuery = typeof window !== 'undefined'
    ? window.matchMedia('(prefers-reduced-motion: reduce)')
    : null

  return mediaQuery?.matches ?? false
}

/**
 * High contrast mode detection
 */
export function useHighContrastMode(): boolean {
  const mediaQuery = typeof window !== 'undefined'
    ? window.matchMedia('(forced-colors: active)')
    : null

  return mediaQuery?.matches ?? false
}

export default {
  useKeyboardNavigation,
  useFocusTrap,
  announceToScreenReader,
  generateA11yId,
  focusStyles,
  useReducedMotion,
  useHighContrastMode,
}
