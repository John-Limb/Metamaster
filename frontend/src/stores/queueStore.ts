import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { QueueTask, QueueStats } from '@/types'
import { queueService } from '@/services/queueService'

interface QueueState {
  tasks: QueueTask[]
  stats: QueueStats | null
  isLoading: boolean
  error: string | null
  statusFilter: string | null
  pollingEnabled: boolean
  pollingInterval: number

  // Task operations
  setTasks: (tasks: QueueTask[]) => void
  addTask: (task: QueueTask) => void
  updateTask: (id: string, updates: Partial<QueueTask>) => void
  removeTask: (id: string) => void
  clearCompletedTasks: () => Promise<void>
  retryTask: (id: string) => Promise<void>
  cancelTask: (id: string) => Promise<void>

  // Stats
  setStats: (stats: QueueStats) => void
  fetchStats: () => Promise<void>

  // Loading & Error
  setIsLoading: (loading: boolean) => void
  setError: (error: string | null) => void

  // Filters
  setStatusFilter: (status: string | null) => void

  // Getters
  getPendingTasks: () => QueueTask[]
  getProcessingTasks: () => QueueTask[]
  getFailedTasks: () => QueueTask[]
  getTaskById: (id: string) => QueueTask | undefined

  // Fetch operations
  fetchTasks: (page?: number, pageSize?: number, status?: string) => Promise<void>
  fetchTaskDetails: (id: string) => Promise<QueueTask>
  fetchTaskProgress: (id: string) => Promise<{ progress: number; status: string }>

  // Polling
  setPollingEnabled: (enabled: boolean) => void
  setPollingInterval: (interval: number) => void
}

export const useQueueStore = create<QueueState>()(
  persist(
    (set, get) => ({
      tasks: [],
      stats: null,
      isLoading: false,
      error: null,
      statusFilter: null,
      pollingEnabled: true,
      pollingInterval: 5000,

      // Task operations
      setTasks: (tasks) => set({ tasks }),
      addTask: (task) =>
        set((state) => ({
          tasks: [...state.tasks, task],
        })),
      updateTask: (id, updates) =>
        set((state) => ({
          tasks: state.tasks.map((t) => (t.id === id ? { ...t, ...updates } : t)),
        })),
      removeTask: (id) =>
        set((state) => ({
          tasks: state.tasks.filter((t) => t.id !== id),
        })),
      clearCompletedTasks: async () => {
        try {
          set({ isLoading: true, error: null })
          await queueService.clearCompletedTasks()
          set((state) => ({
            tasks: state.tasks.filter((t) => t.status !== 'completed'),
          }))
        } catch (error: any) {
          set({ error: error.message || 'Failed to clear completed tasks' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      retryTask: async (id) => {
        try {
          set({ isLoading: true, error: null })
          const task = await queueService.retryTask(id)
          set((state) => ({
            tasks: state.tasks.map((t) => (t.id === id ? task : t)),
          }))
        } catch (error: any) {
          set({ error: error.message || 'Failed to retry task' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      cancelTask: async (id) => {
        try {
          set({ isLoading: true, error: null })
          await queueService.cancelTask(id)
          set((state) => ({
            tasks: state.tasks.filter((t) => t.id !== id),
          }))
        } catch (error: any) {
          set({ error: error.message || 'Failed to cancel task' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },

      // Stats
      setStats: (stats) => set({ stats }),
      fetchStats: async () => {
        try {
          set({ isLoading: true, error: null })
          const stats = await queueService.getStats()
          set({ stats })
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch queue stats' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },

      // Loading & Error
      setIsLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),

      // Filters
      setStatusFilter: (status) => set({ statusFilter: status }),

      // Getters
      getPendingTasks: () => get().tasks.filter((t) => t.status === 'pending'),
      getProcessingTasks: () => get().tasks.filter((t) => t.status === 'processing'),
      getFailedTasks: () => get().tasks.filter((t) => t.status === 'failed'),
      getTaskById: (id) => get().tasks.find((t) => t.id === id),

      // Fetch operations
      fetchTasks: async (page = 1, pageSize = 20, status) => {
        try {
          set({ isLoading: true, error: null })
          const response = await queueService.getTasks(page, pageSize, status)
          set({ tasks: response.items })
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch tasks' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      fetchTaskDetails: async (id) => {
        try {
          set({ isLoading: true, error: null })
          const task = await queueService.getTaskDetails(id)
          set((state) => ({
            tasks: state.tasks.map((t) => (t.id === id ? task : t)),
          }))
          return task
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch task details' })
          throw error
        } finally {
          set({ isLoading: false })
        }
      },
      fetchTaskProgress: async (id) => {
        try {
          const progress = await queueService.getTaskProgress(id)
          set((state) => ({
            tasks: state.tasks.map((t) =>
              t.id === id
                ? { ...t, progress: progress.progress, status: progress.status as QueueTask['status'] }
                : t
            ),
          }))
          return progress
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch task progress' })
          throw error
        }
      },

      // Polling
      setPollingEnabled: (enabled) => set({ pollingEnabled: enabled }),
      setPollingInterval: (interval) => set({ pollingInterval: interval }),
    }),
    {
      name: 'queue-store',
      partialize: (state) => ({
        pollingEnabled: state.pollingEnabled,
        pollingInterval: state.pollingInterval,
        statusFilter: state.statusFilter,
      }),
    }
  )
)
