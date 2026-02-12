import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { UserSettings, ApiSettings } from '@/types'

interface AuthState {
  token: string | null
  refreshToken: string | null
  user: { id: string; email: string; name: string } | null
  isAuthenticated: boolean

  // Auth actions
  setToken: (token: string) => void
  setRefreshToken: (refreshToken: string) => void
  setUser: (user: { id: string; email: string; name: string }) => void
  logout: () => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,

      setToken: (token) =>
        set({
          token,
          isAuthenticated: true,
        }),
      setRefreshToken: (refreshToken) => set({ refreshToken }),
      setUser: (user) => set({ user }),
      logout: () =>
        set({
          token: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        }),
      clearAuth: () =>
        set({
          token: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({
        token: state.token,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
      storage: createJSONStorage(() => localStorage),
    }
  )
)

interface SettingsState {
  // User settings
  userSettings: UserSettings
  updateUserSettings: (settings: Partial<UserSettings>) => void
  resetUserSettings: () => void

  // API settings
  apiSettings: ApiSettings
  updateApiSettings: (settings: Partial<ApiSettings>) => void
  resetApiSettings: () => void

  // Export/Import
  exportSettings: () => string
  importSettings: (settingsJson: string) => boolean

  // Cache management
  clearCache: () => void
  clearLocalStorage: () => void
}

const defaultUserSettings: UserSettings = {
  theme: 'light',
  itemsPerPage: 20,
  autoRefresh: true,
  autoRefreshInterval: 30000,
  notifications: true,
  soundEnabled: true,
}

const defaultApiSettings: ApiSettings = {
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set, get) => ({
      // User settings
      userSettings: defaultUserSettings,
      updateUserSettings: (settings) =>
        set((state) => ({
          userSettings: { ...state.userSettings, ...settings },
        })),
      resetUserSettings: () => set({ userSettings: defaultUserSettings }),

      // API settings
      apiSettings: defaultApiSettings,
      updateApiSettings: (settings) =>
        set((state) => ({
          apiSettings: { ...state.apiSettings, ...settings },
        })),
      resetApiSettings: () => set({ apiSettings: defaultApiSettings }),

      // Export/Import
      exportSettings: () => {
        const { userSettings, apiSettings } = get()
        return JSON.stringify(
          {
            userSettings,
            apiSettings,
            exportedAt: new Date().toISOString(),
          },
          null,
          2
        )
      },
      importSettings: (settingsJson) => {
        try {
          const settings = JSON.parse(settingsJson)
          if (settings.userSettings && settings.apiSettings) {
            set({
              userSettings: { ...defaultUserSettings, ...settings.userSettings },
              apiSettings: { ...defaultApiSettings, ...settings.apiSettings },
            })
            return true
          }
          return false
        } catch {
          return false
        }
      },

      // Cache management
      clearCache: () => {
        // Clear all Zustand persist stores
        Object.keys(localStorage)
          .filter((key) => key.startsWith('zustand'))
          .forEach((key) => localStorage.removeItem(key))
      },
      clearLocalStorage: () => {
        localStorage.clear()
      },
    }),
    {
      name: 'settings-store',
      partialize: (state) => ({
        userSettings: state.userSettings,
        apiSettings: state.apiSettings,
      }),
    }
  )
)
