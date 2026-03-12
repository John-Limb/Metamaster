import { describe, it, expect, vi, beforeEach } from 'vitest'
import { storageService } from '../storageService'

vi.mock('@/utils/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import { apiClient } from '@/utils/api'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('storageService.getFiles', () => {
  it('passes watchedStatus param', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: { total: 0, items: [] },
    })
    await storageService.getFiles({ watchedStatus: 'unwatched' })
    expect(apiClient.get).toHaveBeenCalledWith(
      '/storage/files',
      expect.objectContaining({
        params: expect.objectContaining({ watchedStatus: 'unwatched' }),
      })
    )
  })

  it('includes new fields in StorageFileItem — is_watched null for unlibrary file', async () => {
    const item = {
      id: 1,
      name: 'test.mkv',
      media_type: 'movie',
      size_bytes: 1_000_000_000,
      duration_seconds: 7200,
      video_codec: 'h264',
      video_width: 1920,
      video_height: 1080,
      mb_per_min: 23.1,
      resolution_tier: '1080p',
      efficiency_tier: 'efficient',
      estimated_savings_bytes: 0,
      is_watched: null,
      show_title: null,
      show_fully_unwatched: null,
    }
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: { total: 1, items: [item] } })
    const result = await storageService.getFiles({})
    expect(result.items[0].is_watched).toBeNull()
    expect(result.items[0].show_title).toBeNull()
  })
})

describe('storageService.getSummary', () => {
  it('returns unwatched size fields', async () => {
    const summary = {
      disk: { total_bytes: 1000, used_bytes: 500, available_bytes: 500 },
      library: { movies_bytes: 0, tv_bytes: 0, other_bytes: 0 },
      potential_savings_bytes: 0,
      files_analyzed: 0,
      files_pending_analysis: 0,
      unwatched_movie_size_bytes: 400_000_000_000,
      unwatched_tv_size_bytes: 100_000_000_000,
    }
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: summary })
    const result = await storageService.getSummary()
    expect(result.unwatched_movie_size_bytes).toBe(400_000_000_000)
    expect(result.unwatched_tv_size_bytes).toBe(100_000_000_000)
  })
})
