import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Toast, Modal, UserSettings } from '@/types'

interface UIState {
  // Toast notifications
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => string
  removeToast: (id: string) => void
  clearToasts: () => void

  // Modals
  modals: Modal[]
  openModal: (modal: Omit<Modal, 'id'>) => string
  closeModal: (id: string) => void
  closeAllModals: () => void

  // Sidebar
  sidebarOpen: boolean
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void

  // Loading states
  globalLoading: boolean
  setGlobalLoading: (loading: boolean) => void
  loadingStack: string[]
  pushLoading: (id: string) => void
  popLoading: (id: string) => void

  // Theme
  theme: 'light' | 'dark' | 'auto'
  setTheme: (theme: 'light' | 'dark' | 'auto') => void

  // User settings (persisted)
  settings: UserSettings
  updateSettings: (settings: Partial<UserSettings>) => void
  resetSettings: () => void

  // Breadcrumbs
  breadcrumbs: { label: string; path?: string }[]
  setBreadcrumbs: (breadcrumbs: { label: string; path?: string }[]) => void

  // View preferences (persisted)
  fileViewMode: 'grid' | 'list'
  setFileViewMode: (mode: 'grid' | 'list') => void
  queueViewMode: 'compact' | 'detailed'
  setQueueViewMode: (mode: 'compact' | 'detailed') => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      // Toast notifications
      toasts: [],
      addToast: (toast) => {
        const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        set((state) => ({
          toasts: [...state.toasts, { ...toast, id }],
        }))
        // Auto-remove after duration
        if (toast.duration !== 0) {
          setTimeout(() => {
            get().removeToast(id)
          }, toast.duration || 5000)
        }
        return id
      },
      removeToast: (id) =>
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        })),
      clearToasts: () => set({ toasts: [] }),

      // Modals
      modals: [],
      openModal: (modal) => {
        const id = `modal-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
        set((state) => ({
          modals: [...state.modals, { ...modal, id }],
        }))
        return id
      },
      closeModal: (id) =>
        set((state) => ({
          modals: state.modals.filter((m) => m.id !== id),
        })),
      closeAllModals: () => set({ modals: [] }),

      // Sidebar
      sidebarOpen: true,
      toggleSidebar: () =>
        set((state) => ({
          sidebarOpen: !state.sidebarOpen,
        })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),

      // Loading states
      globalLoading: false,
      setGlobalLoading: (loading) => set({ globalLoading: loading }),
      loadingStack: [],
      pushLoading: (id) =>
        set((state) => ({
          loadingStack: [...state.loadingStack, id],
          globalLoading: true,
        })),
      popLoading: (id) =>
        set((state) => ({
          loadingStack: state.loadingStack.filter((item) => item !== id),
          globalLoading: state.loadingStack.length > 1,
        })),

      // Theme
      theme: 'light',
      setTheme: (theme) => set({ theme }),

      // User settings
      settings: {
        theme: 'light',
        itemsPerPage: 20,
        autoRefresh: true,
        autoRefreshInterval: 30000,
        notifications: true,
        soundEnabled: true,
      },
      updateSettings: (newSettings) =>
        set((state) => ({
          settings: { ...state.settings, ...newSettings },
        })),
      resetSettings: () =>
        set({
          settings: {
            theme: 'light',
            itemsPerPage: 20,
            autoRefresh: true,
            autoRefreshInterval: 30000,
            notifications: true,
            soundEnabled: true,
          },
        }),

      // Breadcrumbs
      breadcrumbs: [],
      setBreadcrumbs: (breadcrumbs) => set({ breadcrumbs }),

      // View preferences
      fileViewMode: 'grid',
      setFileViewMode: (mode) => set({ fileViewMode: mode }),
      queueViewMode: 'detailed',
      setQueueViewMode: (mode) => set({ queueViewMode: mode }),
    }),
    {
      name: 'ui-store',
      partialize: (state) => ({
        theme: state.theme,
        settings: state.settings,
        fileViewMode: state.fileViewMode,
        queueViewMode: state.queueViewMode,
        sidebarOpen: state.sidebarOpen,
      }),
    }
  )
)
