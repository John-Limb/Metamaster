import { create } from 'zustand'
import type { PlexConnection, PlexMismatchItem } from '../services/plexService'
import {
  deletePlexConnection,
  getMismatches,
  getPlexConnection,
  resolveMismatch,
  triggerPlexSync,
} from '../services/plexService'

interface PlexState {
  connection: PlexConnection | null
  isLoading: boolean
  error: string | null
  mismatches: PlexMismatchItem[]
  fetchConnection: () => Promise<void>
  disconnect: () => Promise<void>
  sync: () => Promise<string>
  fetchMismatches: () => Promise<void>
  resolveMismatch: (recordId: number, trust: 'metamaster' | 'plex') => Promise<void>
}

export const usePlexStore = create<PlexState>((set) => ({
  connection: null,
  isLoading: false,
  error: null,
  mismatches: [],

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

  fetchMismatches: async () => {
    try {
      const mismatches = await getMismatches()
      set({ mismatches })
    } catch {
      // silently fail — mismatches are supplementary
    }
  },

  resolveMismatch: async (recordId, trust) => {
    await resolveMismatch(recordId, trust)
    set((state) => ({
      mismatches: state.mismatches.filter((m) => m.id !== recordId),
    }))
  },
}))
