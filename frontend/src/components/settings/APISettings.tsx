import React, { useCallback, useState } from 'react'
import { useSettingsStore } from '@/stores/settingsStore'

interface APISettingsProps {
  className?: string
}

export function APISettings({ className = '' }: APISettingsProps) {
  const { apiSettings, updateApiSettings, resetApiSettings } = useSettingsStore()
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle')

  const handleBaseUrlChange = useCallback(
    (baseUrl: string) => {
      updateApiSettings({ baseUrl })
    },
    [updateApiSettings]
  )

  const handleTimeoutChange = useCallback(
    (timeout: number) => {
      updateApiSettings({ timeout })
    },
    [updateApiSettings]
  )

  const handleRetryAttemptsChange = useCallback(
    (retryAttempts: number) => {
      updateApiSettings({ retryAttempts })
    },
    [updateApiSettings]
  )

  const handleRetryDelayChange = useCallback(
    (retryDelay: number) => {
      updateApiSettings({ retryDelay })
    },
    [updateApiSettings]
  )

  const handleTestConnection = useCallback(async () => {
    setTestStatus('testing')
    try {
      const response = await fetch(`${apiSettings.baseUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(apiSettings.timeout),
      })
      if (response.ok) {
        setTestStatus('success')
      } else {
        setTestStatus('error')
      }
    } catch {
      setTestStatus('error')
    } finally {
      setTimeout(() => setTestStatus('idle'), 3000)
    }
  }, [apiSettings.baseUrl, apiSettings.timeout])

  const getTestStatusIcon = () => {
    switch (testStatus) {
      case 'testing':
        return (
          <svg className="animate-spin h-5 w-5 text-blue-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )
      case 'success':
        return (
          <svg className="h-5 w-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        )
      case 'error':
        return (
          <svg className="h-5 w-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        )
      default:
        return null
    }
  }

  return (
    <div className={`space-y-6 ${className}`}>
      <div>
        <h3 className="text-lg font-medium text-gray-900">API Settings</h3>
        <p className="text-sm text-gray-500 mt-1">
          Configure the API connection settings.
        </p>
      </div>

      <div className="space-y-4">
        {/* Base URL */}
        <div>
          <label
            htmlFor="baseUrl"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            API Base URL
          </label>
          <div className="flex gap-2">
            <input
              type="url"
              id="baseUrl"
              value={apiSettings.baseUrl}
              onChange={(e) => handleBaseUrlChange(e.target.value)}
              className="block flex-1 border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
              placeholder="https://api.example.com"
            />
            <button
              onClick={handleTestConnection}
              disabled={testStatus === 'testing'}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 flex items-center gap-2"
            >
              {getTestStatusIcon()}
              Test
            </button>
          </div>
        </div>

        {/* Timeout */}
        <div>
          <label
            htmlFor="timeout"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Request Timeout (ms)
          </label>
          <input
            type="number"
            id="timeout"
            value={apiSettings.timeout}
            onChange={(e) => handleTimeoutChange(Number(e.target.value))}
            min={1000}
            max={60000}
            step={1000}
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
          />
        </div>

        {/* Retry Attempts */}
        <div>
          <label
            htmlFor="retryAttempts"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Retry Attempts
          </label>
          <input
            type="number"
            id="retryAttempts"
            value={apiSettings.retryAttempts}
            onChange={(e) => handleRetryAttemptsChange(Number(e.target.value))}
            min={0}
            max={10}
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
          />
        </div>

        {/* Retry Delay */}
        <div>
          <label
            htmlFor="retryDelay"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Retry Delay (ms)
          </label>
          <input
            type="number"
            id="retryDelay"
            value={apiSettings.retryDelay}
            onChange={(e) => handleRetryDelayChange(Number(e.target.value))}
            min={100}
            max={10000}
            step={100}
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
          />
        </div>

        {/* Reset to Defaults */}
        <div className="pt-4 border-t border-gray-200">
          <button
            onClick={resetApiSettings}
            className="text-sm text-gray-600 hover:text-gray-900 font-medium"
          >
            Reset to Defaults
          </button>
        </div>
      </div>
    </div>
  )
}

export default APISettings
