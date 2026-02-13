import React, { useCallback, useState } from 'react'
import { useSettingsStore } from '@/stores/settingsStore'

interface CacheSettingsProps {
  className?: string
}

export function CacheSettings({ className = '' }: CacheSettingsProps) {
  const { clearCache, clearLocalStorage } = useSettingsStore()
  const [isClearing, setIsClearing] = useState<'cache' | 'storage' | null>(null)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const handleClearCache = useCallback(async () => {
    setIsClearing('cache')
    try {
      clearCache()
      setMessage({ type: 'success', text: 'Cache cleared successfully' })
    } catch {
      setMessage({ type: 'error', text: 'Failed to clear cache' })
    } finally {
      setIsClearing(null)
      setTimeout(() => setMessage(null), 3000)
    }
  }, [clearCache])

  const handleClearStorage = useCallback(async () => {
    setIsClearing('storage')
    try {
      clearLocalStorage()
      setMessage({ type: 'success', text: 'Local storage cleared successfully' })
    } catch {
      setMessage({ type: 'error', text: 'Failed to clear local storage' })
    } finally {
      setIsClearing(null)
      setTimeout(() => setMessage(null), 3000)
    }
  }, [clearLocalStorage])

  const [cacheSettings, setCacheSettings] = useState({
    enableApiCache: true,
    apiCacheMaxAge: 300,
    enableImageCache: true,
    imageCacheMaxAge: 86400,
    maxCacheSize: 100,
  })

  const handleCacheSettingChange = useCallback(
    (key: keyof typeof cacheSettings, value: any) => {
      setCacheSettings((prev) => ({ ...prev, [key]: value }))
    },
    []
  )

  return (
    <div className={`space-y-6 ${className}`}>
      <div>
        <h3 className="text-lg font-medium text-gray-900">Cache Settings</h3>
        <p className="text-sm text-gray-500 mt-1">
          Configure caching behavior and storage management.
        </p>
      </div>

      {/* Status Message */}
      {message && (
        <div
          className={`p-4 rounded-md ${
            message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
          }`}
          role="alert"
        >
          {message.text}
        </div>
      )}

      <div className="space-y-4">
        {/* Enable API Cache */}
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="enableApiCache" className="text-sm font-medium text-gray-700">
              API Response Cache
            </label>
            <p className="text-sm text-gray-500">
              Cache API responses for faster loading
            </p>
          </div>
          <button
            id="enableApiCache"
            onClick={() => handleCacheSettingChange('enableApiCache', !cacheSettings.enableApiCache)}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
              cacheSettings.enableApiCache ? 'bg-primary-600' : 'bg-gray-200'
            }`}
            role="switch"
            aria-checked={cacheSettings.enableApiCache}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                cacheSettings.enableApiCache ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* API Cache Max Age */}
        {cacheSettings.enableApiCache && (
          <div>
            <label
              htmlFor="apiCacheMaxAge"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              API Cache Max Age (seconds)
            </label>
            <input
              type="number"
              id="apiCacheMaxAge"
              value={cacheSettings.apiCacheMaxAge}
              onChange={(e) => handleCacheSettingChange('apiCacheMaxAge', Number(e.target.value))}
              min={60}
              max={3600}
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>
        )}

        {/* Enable Image Cache */}
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="enableImageCache" className="text-sm font-medium text-gray-700">
              Image Cache
            </label>
            <p className="text-sm text-gray-500">
              Cache images and thumbnails
            </p>
          </div>
          <button
            id="enableImageCache"
            onClick={() => handleCacheSettingChange('enableImageCache', !cacheSettings.enableImageCache)}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
              cacheSettings.enableImageCache ? 'bg-primary-600' : 'bg-gray-200'
            }`}
            role="switch"
            aria-checked={cacheSettings.enableImageCache}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                cacheSettings.enableImageCache ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Image Cache Max Age */}
        {cacheSettings.enableImageCache && (
          <div>
            <label
              htmlFor="imageCacheMaxAge"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Image Cache Max Age (seconds)
            </label>
            <input
              type="number"
              id="imageCacheMaxAge"
              value={cacheSettings.imageCacheMaxAge}
              onChange={(e) => handleCacheSettingChange('imageCacheMaxAge', Number(e.target.value))}
              min={3600}
              max={604800}
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>
        )}

        {/* Max Cache Size */}
        <div>
          <label
            htmlFor="maxCacheSize"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Maximum Cache Size (MB)
          </label>
          <input
            type="number"
            id="maxCacheSize"
            value={cacheSettings.maxCacheSize}
            onChange={(e) => handleCacheSettingChange('maxCacheSize', Number(e.target.value))}
            min={10}
            max={1000}
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
          />
        </div>

        {/* Clear Cache Button */}
        <div className="pt-4 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Clear Cached Data</h4>
          <div className="flex gap-3">
            <button
              onClick={handleClearCache}
              disabled={isClearing !== null}
              className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 disabled:opacity-50"
            >
              {isClearing === 'cache' ? 'Clearing...' : 'Clear Cache'}
            </button>
            <button
              onClick={handleClearStorage}
              disabled={isClearing !== null}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
            >
              {isClearing === 'storage' ? 'Clearing...' : 'Clear Local Storage'}
            </button>
          </div>
          <p className="mt-2 text-xs text-gray-500">
            Clearing cache may temporarily slow down the application until data is re-cached.
          </p>
        </div>
      </div>
    </div>
  )
}

export default CacheSettings
