import React, { useCallback } from 'react'

interface MonitoringSettingsProps {
  className?: string
}

export function MonitoringSettings({ className = '' }: MonitoringSettingsProps) {
  const [settings, setSettings] = React.useState({
    enablePerformanceMonitoring: true,
    enableErrorTracking: true,
    enableAnalytics: false,
    logLevel: 'info' as 'debug' | 'info' | 'warn' | 'error',
    reportErrors: true,
    autoRefreshStats: true,
    refreshInterval: 30,
  })

  const handleSettingChange = useCallback(
    (key: keyof typeof settings, value: boolean | string | number) => {
      setSettings((prev) => ({ ...prev, [key]: value }))
    },
    []
  )

  return (
    <div className={`space-y-6 ${className}`}>
      <div>
        <h3 className="text-lg font-medium text-body">Monitoring Settings</h3>
        <p className="text-sm text-hint mt-1">
          Configure monitoring and performance tracking.
        </p>
      </div>

      <div className="space-y-4">
        {/* Performance Monitoring */}
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="enablePerformanceMonitoring" className="text-sm font-medium text-dim">
              Performance Monitoring
            </label>
            <p className="text-sm text-hint">
              Track application performance metrics
            </p>
          </div>
          <button
            id="enablePerformanceMonitoring"
            onClick={() =>
              handleSettingChange('enablePerformanceMonitoring', !settings.enablePerformanceMonitoring)
            }
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
              settings.enablePerformanceMonitoring ? 'bg-primary-600' : 'bg-subtle'
            }`}
            role="switch"
            aria-checked={settings.enablePerformanceMonitoring}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-card shadow ring-0 transition duration-200 ease-in-out ${
                settings.enablePerformanceMonitoring ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Error Tracking */}
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="enableErrorTracking" className="text-sm font-medium text-dim">
              Error Tracking
            </label>
            <p className="text-sm text-hint">
              Track and log application errors
            </p>
          </div>
          <button
            id="enableErrorTracking"
            onClick={() => handleSettingChange('enableErrorTracking', !settings.enableErrorTracking)}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
              settings.enableErrorTracking ? 'bg-primary-600' : 'bg-subtle'
            }`}
            role="switch"
            aria-checked={settings.enableErrorTracking}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-card shadow ring-0 transition duration-200 ease-in-out ${
                settings.enableErrorTracking ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Analytics */}
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="enableAnalytics" className="text-sm font-medium text-dim">
              Usage Analytics
            </label>
            <p className="text-sm text-hint">
              Collect anonymous usage statistics
            </p>
          </div>
          <button
            id="enableAnalytics"
            onClick={() => handleSettingChange('enableAnalytics', !settings.enableAnalytics)}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
              settings.enableAnalytics ? 'bg-primary-600' : 'bg-subtle'
            }`}
            role="switch"
            aria-checked={settings.enableAnalytics}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-card shadow ring-0 transition duration-200 ease-in-out ${
                settings.enableAnalytics ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Log Level */}
        <div>
          <label
            htmlFor="logLevel"
            className="block text-sm font-medium text-dim mb-1"
          >
            Log Level
          </label>
          <select
            id="logLevel"
            value={settings.logLevel}
            onChange={(e) => handleSettingChange('logLevel', e.target.value)}
            className="block w-full border border-edge rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
          >
            <option value="debug">Debug</option>
            <option value="info">Info</option>
            <option value="warn">Warning</option>
            <option value="error">Error</option>
          </select>
        </div>

        {/* Auto Refresh Stats */}
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="autoRefreshStats" className="text-sm font-medium text-dim">
              Auto Refresh Statistics
            </label>
            <p className="text-sm text-hint">
              Automatically refresh dashboard statistics
            </p>
          </div>
          <button
            id="autoRefreshStats"
            onClick={() => handleSettingChange('autoRefreshStats', !settings.autoRefreshStats)}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
              settings.autoRefreshStats ? 'bg-primary-600' : 'bg-subtle'
            }`}
            role="switch"
            aria-checked={settings.autoRefreshStats}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-card shadow ring-0 transition duration-200 ease-in-out ${
                settings.autoRefreshStats ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Refresh Interval */}
        {settings.autoRefreshStats && (
          <div>
            <label
              htmlFor="refreshInterval"
              className="block text-sm font-medium text-dim mb-1"
            >
              Stats Refresh Interval (seconds)
            </label>
            <input
              type="number"
              id="refreshInterval"
              value={settings.refreshInterval}
              onChange={(e) => handleSettingChange('refreshInterval', Number(e.target.value))}
              min={10}
              max={300}
              className="block w-full border border-edge rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default MonitoringSettings
