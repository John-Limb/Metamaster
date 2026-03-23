import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { FaCog, FaPalette, FaBell, FaSync, FaFolder, FaServer } from 'react-icons/fa'
import { Button, CheckboxInput, RadioInput } from '@/components/common'
import { organisationService, type OrganisationPreset } from '@/services/organisationService'
import { scanScheduleService } from '@/services/configurationService'
import { useSettingsStore } from '@/stores/settingsStore'
import { useUIStore } from '@/stores/uiStore'
import { PlexSettings } from '@/components/features/plex/PlexSettings'
import { useTheme } from '@/context/ThemeContext'

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
  <div className="bg-card rounded-lg shadow-md p-6 border-l-4 border-primary-600">
    <div className="flex items-start gap-4 mb-4">
      <div className="text-primary-600 text-2xl mt-1">{icon}</div>
      <div>
        <h3 className="text-lg font-semibold text-body">{title}</h3>
        <p className="text-dim text-sm">{description}</p>
      </div>
    </div>
    <div className="mt-4">{children}</div>
  </div>
)

interface SwatchProps {
  label: string
  chips: [string, string, string]
  active: boolean
  onClick: () => void
}

function ColourThemeSwatch({ label, chips, active, onClick }: SwatchProps) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={`flex items-center gap-3 px-3 py-2 rounded-lg border-2 transition-colors text-left w-full ${
        active
          ? 'border-primary-600 bg-primary-50 dark:bg-primary-900/20'
          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
      }`}
    >
      <div className="flex gap-1">
        {chips.map((c, i) => (
          <span key={i} className="w-4 h-4 rounded-full border border-white/20" style={{ background: c }} />
        ))}
      </div>
      <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{label}</span>
      {active && <span className="ml-auto text-xs text-primary-600 font-semibold">Active</span>}
    </button>
  )
}

export const SettingsPage: React.FC = () => {
  const {
    userSettings,
    updateUserSettings,
    resetUserSettings,
  } = useSettingsStore()
  const { addToast } = useUIStore()
  const { setTheme: applyTheme, colourTheme, setColourTheme } = useTheme()

  // Map between settings store ('auto') and ThemeContext ('system')
  const toThemeContext = (t: string) => (t === 'auto' ? 'system' : t) as 'light' | 'dark' | 'system'

  const [itemsPerPage, setItemsPerPage] = useState(userSettings.itemsPerPage)
  const [autoRefresh, setAutoRefresh] = useState(userSettings.autoRefresh)
  const [theme, setTheme] = useState(userSettings.theme)
  const [notifications, setNotifications] = useState(userSettings.notifications)
  const [soundEnabled, setSoundEnabled] = useState(userSettings.soundEnabled)
  const [scanSchedule, setScanSchedule] = useState('0 2 * * *')

  const [orgPreset, setOrgPreset] = useState<OrganisationPreset>('plex')

  useEffect(() => {
    scanScheduleService.getSchedule().then(setScanSchedule).catch(() => {})
  }, [])

  useEffect(() => {
    organisationService.getSettings()
      .then(({ preset }) => setOrgPreset(preset))
      .catch(() => {})
  }, [])

  const handleSaveSettings = () => {
    updateUserSettings({
      theme,
      itemsPerPage,
      autoRefresh,
      notifications,
      soundEnabled,
    })
    applyTheme(toThemeContext(theme))
    addToast({ type: 'success', message: 'Settings saved', duration: 3000 })
  }

  const handleResetToDefaults = () => {
    resetUserSettings()
    const defaults = useSettingsStore.getState()
    setItemsPerPage(defaults.userSettings.itemsPerPage)
    setAutoRefresh(defaults.userSettings.autoRefresh)
    setTheme(defaults.userSettings.theme)
    setNotifications(defaults.userSettings.notifications)
    setSoundEnabled(defaults.userSettings.soundEnabled)
    applyTheme(toThemeContext(defaults.userSettings.theme))
  }

  const handleSaveScanSchedule = async () => {
    try {
      await scanScheduleService.setSchedule(scanSchedule)
      addToast({ type: 'success', message: 'Scan schedule saved', duration: 3000 })
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Failed to save schedule'
      addToast({ type: 'error', message, duration: 4000 })
    }
  }

  const handleOrgPresetChange = async (preset: OrganisationPreset) => {
    setOrgPreset(preset)
    try {
      await organisationService.saveSettings(preset)
    } catch {
      // non-fatal
    }
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-body mb-2">Settings</h1>
        <p className="text-dim">Manage your preferences and configuration</p>
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
              <span aria-hidden="true" className="text-red-500 ml-0.5">*</span>
            </label>
            <input
              type="number"
              value={itemsPerPage}
              onChange={(e) => setItemsPerPage(Number(e.target.value))}
              aria-required="true"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="flex items-center gap-2 cursor-pointer">
              <CheckboxInput
                checked={autoRefresh}
                onChange={(checked) => setAutoRefresh(checked)}
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
              <span aria-hidden="true" className="text-red-500 ml-0.5">*</span>
            </label>
            <input
              type="text"
              value={scanSchedule}
              onChange={(e) => setScanSchedule(e.target.value)}
              aria-required="true"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono"
              placeholder="0 2 * * *"
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Examples: <code>0 2 * * *</code> = 2AM daily, <code>0 */6 * * *</code> = every 6 hours,{' '}
              <code>*/5 * * * *</code> = every 5 minutes
            </p>
          </div>
          <Button variant="primary" size="sm" onClick={handleSaveScanSchedule}>
            Save Schedule
          </Button>
        </div>
      </SettingsSection>

      {/* Theme Settings */}
      <SettingsSection
        icon={<FaPalette />}
        title="Theme"
        description="Customize the appearance of the application"
      >
        <div className="space-y-4">
          {/* Colour theme */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Colour Theme</p>
            <div className="space-y-2">
              <ColourThemeSwatch
                label="Default"
                chips={['#1e293b', '#4f46e5', '#f1f5f9']}
                active={colourTheme === 'default'}
                onClick={() => setColourTheme('default')}
              />
              <ColourThemeSwatch
                label="Matrix"
                chips={['#000000', '#00ff41', '#00b835']}
                active={colourTheme === 'matrix'}
                onClick={() => setColourTheme('matrix')}
              />
              <ColourThemeSwatch
                label="Synthwave"
                chips={['#0d0117', '#c84dff', '#e8d5ff']}
                active={colourTheme === 'synthwave'}
                onClick={() => setColourTheme('synthwave')}
              />
            </div>
          </div>

          {/* Light / dark mode — only relevant for Default theme */}
          <div className={colourTheme !== 'default' ? 'opacity-40 pointer-events-none select-none' : ''}>
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Light / Dark Mode
              {colourTheme !== 'default' && (
                <span className="ml-2 text-xs font-normal text-gray-400">(not available for this theme)</span>
              )}
            </p>
            <div className="space-y-2">
              {(['light', 'dark', 'auto'] as const).map((option) => (
                <label key={option} className="flex items-center gap-2 cursor-pointer">
                  <RadioInput
                    name="theme"
                    value={option}
                    checked={theme === option}
                    onChange={(val) => setTheme(val as 'light' | 'dark' | 'auto')}
                  />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">{option}</span>
                </label>
              ))}
            </div>
          </div>
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
            <CheckboxInput
              checked={notifications}
              onChange={(checked) => setNotifications(checked)}
            />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Enable notifications</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <CheckboxInput
              checked={soundEnabled}
              onChange={(checked) => setSoundEnabled(checked)}
            />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Sound enabled</span>
          </label>
        </div>
      </SettingsSection>

      {/* File Organisation */}
      <SettingsSection
        icon={<FaFolder />}
        title="File Organisation"
        description="Choose the naming convention for your media server"
      >
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Naming Preset
            </label>
            <select
              value={orgPreset}
              onChange={(e) => handleOrgPresetChange(e.target.value as OrganisationPreset)}
              className="w-full sm:w-48 px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="plex">Plex</option>
              <option value="jellyfin">Jellyfin</option>
            </select>
          </div>
          <p className="text-sm text-hint">
            To rename and organise files, visit the{' '}
            <Link to="/organisation" className="text-primary-600 dark:text-primary-400 hover:underline">
              Organisation page
            </Link>
            .
          </p>
        </div>
      </SettingsSection>

      {/* Plex Integration */}
      <SettingsSection
        icon={<FaServer />}
        title="Plex Integration"
        description="Connect your Plex Media Server to sync watch status and trigger library refreshes"
      >
        <PlexSettings />
      </SettingsSection>

      {/* Action Buttons */}
      <div className="flex items-center gap-4">
        <Button variant="primary" size="md" onClick={handleSaveSettings}>
          Save Settings
        </Button>
        <Button variant="secondary" size="md" onClick={handleResetToDefaults}>
          Reset to Defaults
        </Button>
      </div>
    </div>
  )
}
