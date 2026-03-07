import { create } from 'zustand'
import type { PlexConnection } from '../services/plexService'
import {
  getPlexConnection,
  deletePlexConnection,
  triggerPlexSync,
} from '../services/plexService'

interface PlexState {
  connection: PlexConnection | null
  isLoading: boolean
  error: string | null
  fetchConnection: () => Promise<void>
  disconnect: () => Promise<void>
  sync: () => Promise<string>
}

export const usePlexStore = create<PlexState>((set) => ({
  connection: null,
  isLoading: false,
  error: null,

  fetchConnection: async () => {
    set({ isLoading: true, error: null })
    try {
      const connection = await getPlexConnection()
      set({ connection, isLoading: false })
    } catch (err: unknown) {
      const axiosErr = err as { response?: { status: number } }
      if (axiosErr?.response?.status === 404) {
        set({ connection: null, isLoading: false })
      } else {
        set({ error: 'Failed to load Plex connection', isLoading: false })
      }
    }
  },

  disconnect: async () => {
    await deletePlexConnection()
    set({ connection: null })
  },

  sync: async () => {
    const result = await triggerPlexSync()
    return result.task_id
  },
}))
