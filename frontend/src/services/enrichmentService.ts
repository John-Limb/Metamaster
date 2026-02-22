import { apiClient } from '@/utils/api'

export interface PendingEnrichmentItem {
  id: number
  title: string
  year?: number
  enrichment_status: string
  enrichment_error?: string | null
  detected_external_id?: string | null
  manual_external_id?: string | null
}

export interface PendingEnrichmentResponse {
  movies: PendingEnrichmentItem[]
  tv_shows: PendingEnrichmentItem[]
  total: number
}

export const enrichmentService = {
  getPending: async (): Promise<PendingEnrichmentResponse> => {
    const { data } = await apiClient.get<PendingEnrichmentResponse>('/enrichment/pending')
    return data
  },

  setMovieExternalId: async (id: number, externalId: string): Promise<void> => {
    await apiClient.patch(`/movies/${id}/external-id`, { external_id: externalId })
  },

  setTvShowExternalId: async (id: number, externalId: string): Promise<void> => {
    await apiClient.patch(`/tv-shows/${id}/external-id`, { external_id: externalId })
  },

  triggerMovieEnrich: async (id: number): Promise<void> => {
    await apiClient.post(`/movies/${id}/enrich`)
  },

  triggerTvShowEnrich: async (id: number): Promise<void> => {
    await apiClient.post(`/tv-shows/${id}/enrich`)
  },
}
