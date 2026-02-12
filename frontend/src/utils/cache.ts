// Memory cache utility for API responses
class MemoryCache {
  private cache: Map<string, { value: unknown; expiry: number }> = new Map()
  private maxSize = 100
  private defaultTTL = 5 * 60 * 1000 // 5 minutes

  set<T>(key: string, value: T, ttl = this.defaultTTL): void {
    // Evict oldest entries if cache is full
    if (this.cache.size >= this.maxSize) {
      const keys = Array.from(this.cache.keys())
      if (keys.length > 0) {
        this.cache.delete(keys[0])
      }
    }

    this.cache.set(key, {
      value,
      expiry: Date.now() + ttl,
    })
  }

  get<T>(key: string): T | null {
    const entry = this.cache.get(key)

    if (!entry) {
      return null
    }

    if (Date.now() > entry.expiry) {
      this.cache.delete(key)
      return null
    }

    return entry.value as T
  }

  has(key: string): boolean {
    const entry = this.cache.get(key)
    if (!entry) return false
    if (Date.now() > entry.expiry) {
      this.cache.delete(key)
      return false
    }
    return true
  }

  delete(key: string): boolean {
    return this.cache.delete(key)
  }

  clear(): void {
    this.cache.clear()
  }

  prune(): void {
    const now = Date.now()
    for (const [key, entry] of this.cache) {
      if (now > entry.expiry) {
        this.cache.delete(key)
      }
    }
  }

  get size(): number {
    return this.cache.size
  }
}

// Singleton instance
export const apiCache = new MemoryCache()

// Cache decorator for functions
export function cached<T extends (...args: unknown[]) => unknown>(
  fn: T,
  ttl = 5 * 60 * 1000
): T {
  return ((...args: Parameters<T>) => {
    const key = JSON.stringify(args)
    const cachedValue = apiCache.get(key)

    if (cachedValue !== null) {
      return cachedValue as ReturnType<T>
    }

    const result = fn(...args)
    apiCache.set(key, result, ttl)

    return result
  }) as T
}

// Stale-while-revalidate pattern
export async function staleWhileRevalidate<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl = 5 * 60 * 1000
): Promise<T> {
  const cachedValue = apiCache.get<T>(key)

  if (cachedValue !== null) {
    // Return cached value immediately
    // Trigger revalidation in background
    fetcher().then((freshValue) => {
      apiCache.set(key, freshValue, ttl)
    }).catch(() => {
      // Silently fail revalidation
    })

    return cachedValue
  }

  // No cache, fetch fresh data
  const freshValue = await fetcher()
  apiCache.set(key, freshValue, ttl)

  return freshValue
}

export default {
  MemoryCache,
  apiCache,
  cached,
  staleWhileRevalidate,
}
