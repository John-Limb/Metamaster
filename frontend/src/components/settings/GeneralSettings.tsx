import React, { useCallback } from 'react'
import { useSettingsStore } from '@/stores/settingsStore'

interface GeneralSettingsProps {
  className?: string
}

export function GeneralSettings({ className = '' }: GeneralSettingsProps) {
  const { userSettings, updateUserSettings } = useSettingsStore()

  const handleThemeChange = useCallback(
    (theme: 'light' | 'dark' | 'auto') => {
      updateUserSettings({ theme })
      // Apply theme to document
      document.documentElement.classList.remove('light', 'dark')
      if (theme === 'auto') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        document.documentElement.classList.add(prefersDark ? 'dark' : 'light')
      } else {
        document.documentElement.classList.add(theme)
      }
    },
    [updateUserSettings]
  )

  const handleItemsPerPageChange = useCallback(
    (itemsPerPage: number) => {
      updateUserSettings({ itemsPerPage })
    },
    [updateUserSettings]
  )

  const handleAutoRefreshChange = useCallback(
    (autoRefresh: boolean) => {
      updateUserSettings({ autoRefresh })
    },
    [updateUserSettings]
  )

  const handleAutoRefreshIntervalChange = useCallback(
    (autoRefreshInterval: number) => {
      updateUserSettings({ autoRefreshInterval })
    },
    [updateUserSettings]
  )

  const handleNotificationsChange = useCallback(
    (notifications: boolean) => {
      updateUserSettings({ notifications })
    },
    [updateUserSettings]
  )

  const handleSoundEnabledChange = useCallback(
    (soundEnabled: boolean) => {
      updateUserSettings({ soundEnabled })
    },
    [updateUserSettings]
  )

  return (
    <div className={`space-y-6 ${className}`}>
      <div>
        <h3 className="text-lg font-medium text-gray-900">General Settings</h3>
        <p className="text-sm text-gray-500 mt-1">
          Configure your general application preferences.
        </p>
      </div>

      <div className="space-y-4">
        {/* Theme */}
        <div>
          <label
            htmlFor="theme"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Theme
          </label>
          <select
            id="theme"
            value={userSettings.theme}
            onChange={(e) => handleThemeChange(e.target.value as 'light' | 'dark' | 'auto')}
            className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="auto">System Default</option>
          </select>
        </div>

        {/* Items Per Page */}
        <div>
          <label
            htmlFor="itemsPerPage"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Items Per Page
          </label>
          <select
            id="itemsPerPage"
            value={userSettings.itemsPerPage}
            onChange={(e) => handleItemsPerPageChange(Number(e.target.value))}
            className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
          >
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>

        {/* Auto Refresh */}
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="autoRefresh" className="text-sm font-medium text-gray-700">
              Auto Refresh
            </label>
            <p className="text-sm text-gray-500">
              Automatically refresh data at specified intervals
            </p>
          </div>
          <button
            id="autoRefresh"
            onClick={() => handleAutoRefreshChange(!userSettings.autoRefresh)}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
              userSettings.autoRefresh ? 'bg-primary-600' : 'bg-gray-200'
            }`}
            role="switch"
            aria-checked={userSettings.autoRefresh}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                userSettings.autoRefresh ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Auto Refresh Interval */}
        {userSettings.autoRefresh && (
          <div>
            <label
              htmlFor="autoRefreshInterval"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Refresh Interval (seconds)
            </label>
            <input
              type="number"
              id="autoRefreshInterval"
              value={userSettings.autoRefreshInterval / 1000}
              onChange={(e) => handleAutoRefreshIntervalChange(Number(e.target.value) * 1000)}
              min={5}
              max={300}
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>
        )}

        {/* Notifications */}
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="notifications" className="text-sm font-medium text-gray-700">
              Notifications
            </label>
            <p className="text-sm text-gray-500">
              Show desktop notifications for important events
            </p>
          </div>
          <button
            id="notifications"
            onClick={() => handleNotificationsChange(!userSettings.notifications)}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
              userSettings.notifications ? 'bg-primary-600' : 'bg-gray-200'
            }`}
            role="switch"
            aria-checked={userSettings.notifications}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                userSettings.notifications ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>

        {/* Sound Enabled */}
        <div className="flex items-center justify-between">
          <div>
            <label htmlFor="soundEnabled" className="text-sm font-medium text-gray-700">
              Sound Effects
            </label>
            <p className="text-sm text-gray-500">
              Play sound effects for notifications
            </p>
          </div>
          <button
            id="soundEnabled"
            onClick={() => handleSoundEnabledChange(!userSettings.soundEnabled)}
            className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
              userSettings.soundEnabled ? 'bg-primary-600' : 'bg-gray-200'
            }`}
            role="switch"
            aria-checked={userSettings.soundEnabled}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                userSettings.soundEnabled ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
        </div>
      </div>
    </div>
  )
}

export default GeneralSettings
