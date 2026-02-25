import { apiClient } from '@/utils/api'
import { errorHandler } from '@/utils/errorHandler'

export type OrganisationPreset = 'plex' | 'jellyfin'

export interface OrganisationStats {
  movies_match: number
  movies_need_rename: number
  movies_unenriched: number
  episodes_match: number
  episodes_need_rename: number
  episodes_unenriched: number
}

export interface RenameProposal {
  file_id: number
  file_type: 'movie' | 'episode'
  current_path: string
  target_path: string
  show_title?: string
  season_number?: number
}

export interface OrganisationPreview {
  movies: RenameProposal[]
  episodes: RenameProposal[]
}

export interface ApplyResult {
  success: number
  failed: number
  errors: string[]
}

export const organisationService = {
  getSettings: async (): Promise<{ preset: OrganisationPreset }> => {
    try {
      const response = await apiClient.get<{ preset: OrganisationPreset }>('/organisation/settings')
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'getOrganisationSettings')
      throw error
    }
  },

  saveSettings: async (preset: OrganisationPreset): Promise<void> => {
    try {
      await apiClient.put('/organisation/settings', { preset })
    } catch (error: any) {
      errorHandler.handleError(error, 'saveOrganisationSettings')
      throw error
    }
  },

  getStats: async (preset: OrganisationPreset): Promise<OrganisationStats> => {
    try {
      const response = await apiClient.get<OrganisationStats>(
        `/organisation/stats?preset=${preset}`
      )
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'getOrganisationStats')
      throw error
    }
  },

  getPreview: async (preset: OrganisationPreset): Promise<OrganisationPreview> => {
    try {
      const response = await apiClient.get<OrganisationPreview>(
        `/organisation/preview?preset=${preset}`
      )
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'getOrganisationPreview')
      throw error
    }
  },

  applyRenames: async (items: RenameProposal[]): Promise<ApplyResult> => {
    try {
      const response = await apiClient.post<ApplyResult>('/organisation/apply', { items })
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'applyOrganisationRenames')
      throw error
    }
  },
}
