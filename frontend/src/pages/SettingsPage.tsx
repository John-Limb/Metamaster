import React, { useState, useEffect } from 'react'
import { FaCog, FaPalette, FaBell, FaLock, FaSync } from 'react-icons/fa'
import { API_BASE_URL } from '@/utils/constants'
import { scanScheduleService } from '@/services/configurationService'

interface SettingsSectionProps {
  icon: React.ReactNode
  title: string
  description: string
  children: React.ReactNode
}

const SettingsSection: React.FC<SettingsSectionProps> = ({
  icon,
  title,
  description,
  children,
}) => (
  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border-l-4 border-primary-600">
    <div className="flex items-start gap-4 mb-4">
      <div className="text-primary-600 text-2xl mt-1">{icon}</div>
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
        <p className="text-gray-600 dark:text-gray-400 text-sm">{description}</p>
      </div>
    </div>
    <div className="mt-4">{children}</div>
  </div>
)

export const SettingsPage: React.FC = () => {
  const [theme, setTheme] = useState('light')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [notifications, setNotifications] = useState(true)
  const [scanSchedule, setScanSchedule] = useState('0 2 * * *')
  const [scanScheduleSaved, setScanScheduleSaved] = useState(false)
  const [scanScheduleError, setScanScheduleError] = useState('')

  useEffect(() => {
    scanScheduleService.getSchedule().then(setScanSchedule).catch(() => {})
  }, [])

  const handleSaveScanSchedule = async () => {
    setScanScheduleError('')
    setScanScheduleSaved(false)
    try {
      await scanScheduleService.setSchedule(scanSchedule)
      setScanScheduleSaved(true)
      setTimeout(() => setScanScheduleSaved(false), 3000)
    } catch {
      setScanScheduleError('Invalid cron expression or server error.')
    }
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Settings</h1>
        <p className="text-gray-600 dark:text-gray-400">Manage your preferences and configuration</p>
      </div>

      {/* General Settings */}
      <SettingsSection
        icon={<FaCog />}
        title="General Settings"
        description="Configure general application settings"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Items Per Page
            </label>
            <input
              type="number"
              defaultValue="20"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="w-4 h-4 text-primary-600 rounded"
              />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Auto-refresh queue</span>
            </label>
          </div>
        </div>
      </SettingsSection>

      {/* Media Scanning */}
      <SettingsSection
        icon={<FaSync />}
        title="Media Scanning"
        description="Configure automatic scanning for new media files"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Scan Schedule (cron expression)
            </label>
            <input
              type="text"
              value={scanSchedule}
              onChange={(e) => setScanSchedule(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono"
              placeholder="0 2 * * *"
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Examples: <code>0 2 * * *</code> = 2AM daily, <code>0 */6 * * *</code> = every 6 hours,{' '}
              <code>*/5 * * * *</code> = every 5 minutes
            </p>
            {scanScheduleError && (
              <p className="mt-1 text-xs text-red-600 dark:text-red-400">{scanScheduleError}</p>
            )}
            {scanScheduleSaved && (
              <p className="mt-1 text-xs text-green-600 dark:text-green-400">Schedule saved.</p>
            )}
          </div>
          <button
            onClick={handleSaveScanSchedule}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition text-sm font-medium"
          >
            Save Schedule
          </button>
        </div>
      </SettingsSection>

      {/* Theme Settings */}
      <SettingsSection
        icon={<FaPalette />}
        title="Theme"
        description="Customize the appearance of the application"
      >
        <div className="space-y-3">
          {['light', 'dark', 'auto'].map((option) => (
            <label key={option} className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="theme"
                value={option}
                checked={theme === option}
                onChange={(e) => setTheme(e.target.value)}
                className="w-4 h-4 text-primary-600"
              />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">{option}</span>
            </label>
          ))}
        </div>
      </SettingsSection>

      {/* Notification Settings */}
      <SettingsSection
        icon={<FaBell />}
        title="Notifications"
        description="Control how you receive notifications"
      >
        <div className="space-y-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={notifications}
              onChange={(e) => setNotifications(e.target.checked)}
              className="w-4 h-4 text-primary-600 rounded"
            />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Enable notifications</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              defaultChecked
              className="w-4 h-4 text-primary-600 rounded"
            />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Sound enabled</span>
          </label>
        </div>
      </SettingsSection>

      {/* API Settings */}
      <SettingsSection
        icon={<FaLock />}
        title="API Configuration"
        description="Configure API connection settings"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              API Base URL
            </label>
            <input
              type="text"
              defaultValue={API_BASE_URL}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Request Timeout (ms)
            </label>
            <input
              type="number"
              defaultValue="30000"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Retry Attempts
            </label>
            <input
              type="number"
              defaultValue="3"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </SettingsSection>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition font-medium">
          Save Settings
        </button>
        <button className="px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition font-medium">
          Reset to Defaults
        </button>
      </div>
    </div>
  )
}
