import { useEffect } from 'react'

/**
 * Calls `handler` when the Escape key is pressed.
 * @param handler - Stabilise with `useCallback` to avoid unnecessary listener churn.
 * @param enabled - Set to `false` to disable the listener (e.g. when dialog is closed).
 */
export function useEscapeKey(handler: () => void, enabled = true): void {
  useEffect(() => {
    if (!enabled) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handler()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [enabled, handler])
}
