import React, { useState } from 'react'
import { FaCog, FaPalette, FaBell, FaLock } from 'react-icons/fa'

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
  <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-primary-600">
    <div className="flex items-start gap-4 mb-4">
      <div className="text-primary-600 text-2xl mt-1">{icon}</div>
      <div>
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        <p className="text-gray-600 text-sm">{description}</p>
      </div>
    </div>
    <div className="mt-4">{children}</div>
  </div>
)

export const SettingsPage: React.FC = () => {
  const [theme, setTheme] = useState('light')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [notifications, setNotifications] = useState(true)

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Settings</h1>
        <p className="text-gray-600">Manage your preferences and configuration</p>
      </div>

      {/* General Settings */}
      <SettingsSection
        icon={<FaCog />}
        title="General Settings"
        description="Configure general application settings"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Items Per Page
            </label>
            <input
              type="number"
              defaultValue="20"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
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
              <span className="text-sm font-medium text-gray-700">Auto-refresh queue</span>
            </label>
          </div>
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
              <span className="text-sm font-medium text-gray-700 capitalize">{option}</span>
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
            <span className="text-sm font-medium text-gray-700">Enable notifications</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              defaultChecked
              className="w-4 h-4 text-primary-600 rounded"
            />
            <span className="text-sm font-medium text-gray-700">Sound enabled</span>
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
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API Base URL
            </label>
            <input
              type="text"
              defaultValue="http://localhost:8000/api/v1"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Request Timeout (ms)
            </label>
            <input
              type="number"
              defaultValue="30000"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Retry Attempts
            </label>
            <input
              type="number"
              defaultValue="3"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
        </div>
      </SettingsSection>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition font-medium">
          Save Settings
        </button>
        <button className="px-6 py-3 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition font-medium">
          Reset to Defaults
        </button>
      </div>
    </div>
  )
}
