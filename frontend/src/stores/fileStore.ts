import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { FileItem, FileStats } from '@/types'
import { fileService } from '@/services/fileService'

interface FileState {
  // State
  files: FileItem[]
  selectedFiles: string[]
  currentPath: string
  isLoading: boolean
  error: string | null
  stats: FileStats | null
  recentPaths: string[]

  // File operations
  setFiles: (files: FileItem[]) => void
  addFile: (file: FileItem) => void
  removeFile: (id: string) => void
  updateFile: (id: string, updates: Partial<FileItem>) => void
  deleteFile: (id: string) => Promise<void>
  batchDeleteFiles: (ids: string[]) => Promise<void>
  batchMoveFiles: (ids: string[], newPath: string) => Promise<void>

  // Selection
  selectFile: (id: string) => void
  deselectFile: (id: string) => void
  selectMultiple: (ids: string[]) => void
  clearSelection: () => void
  toggleFileSelection: (id: string) => void

  // Navigation
  setCurrentPath: (path: string) => void
  navigateToPath: (path: string) => void
  addRecentPath: (path: string) => void
  getRecentPaths: () => string[]

  // Loading & Error
  setIsLoading: (loading: boolean) => void
  setError: (error: string | null) => void

  // Stats
  setStats: (stats: FileStats) => void
  fetchStats: () => Promise<void>

  // Fetch operations
  fetchFiles: (path: string, page?: number, pageSize?: number) => Promise<void>
}

export const useFileStore = create<FileState>()(
  persist(
    (set, get) => ({
      files: [],
      selectedFiles: [],
      currentPath: '/',
      isLoading: false,
      error: null,
      stats: null,
      recentPaths: [],

      // File operations
      setFiles: (files) => set({ files }),
      addFile: (file) =>
        set((state) => ({
          files: [...state.files, file],
        })),
      removeFile: (id) =>
        set((state) => ({
          files: state.files.filter((f) => f.id !== id),
        })),
      updateFile: (id, updates) =>
        set((state) => ({
          files: state.files.map((f) => (f.id === id ? { ...f, ...updates } : f)),
        })),
      deleteFile: async (id) => {
        try {
          set({ isLoading: true, error: null })
          await fileService.deleteFile(id)
          get().removeFile(id)
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to delete file' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      batchDeleteFiles: async (ids) => {
        try {
          set({ isLoading: true, error: null })
          await fileService.batchDeleteFiles(ids)
          set((state) => ({
            files: state.files.filter((f) => !ids.includes(f.id)),
            selectedFiles: state.selectedFiles.filter((id) => !ids.includes(id)),
          }))
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to delete files' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      batchMoveFiles: async (ids, newPath) => {
        try {
          set({ isLoading: true, error: null })
          await fileService.batchMoveFiles(ids, newPath)
          set((state) => ({
            files: state.files.filter((f) => !ids.includes(f.id)),
            selectedFiles: [],
          }))
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to move files' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },

      // Selection
      selectFile: (id) =>
        set((state) => ({
          selectedFiles: [...state.selectedFiles, id],
        })),
      deselectFile: (id) =>
        set((state) => ({
          selectedFiles: state.selectedFiles.filter((fid) => fid !== id),
        })),
      selectMultiple: (ids) => set({ selectedFiles: ids }),
      clearSelection: () => set({ selectedFiles: [] }),
      toggleFileSelection: (id) =>
        set((state) => ({
          selectedFiles: state.selectedFiles.includes(id)
            ? state.selectedFiles.filter((fid) => fid !== id)
            : [...state.selectedFiles, id],
        })),

      // Navigation
      setCurrentPath: (path) => set({ currentPath: path }),
      navigateToPath: (path) => set({ currentPath: path, selectedFiles: [] }),
      addRecentPath: (path) => {
        set((state) => {
          const filtered = state.recentPaths.filter((p) => p !== path)
          return {
            recentPaths: [path, ...filtered].slice(0, 10),
          }
        })
      },
      getRecentPaths: () => get().recentPaths,

      // Loading & Error
      setIsLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),

      // Stats
      setStats: (stats) => set({ stats }),
      fetchStats: async () => {
        try {
          set({ isLoading: true, error: null })
          const stats = await fileService.getFileStats()
          set({ stats })
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to fetch stats' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },

      // Fetch operations
      fetchFiles: async (path, page = 1, pageSize = 20) => {
        try {
          set({ isLoading: true, error: null })
          const response = await fileService.getFiles(path, page, pageSize)
          set({ files: response.items, currentPath: path })
          get().addRecentPath(path)
        } catch (error: unknown) {
          set({ error: error instanceof Error ? error.message : 'Failed to fetch files' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
    }),
    {
      name: 'file-store',
      partialize: (state) => ({
        recentPaths: state.recentPaths,
      }),
    }
  )
)
