import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { StoragePage } from '../StoragePage'
import { storageService } from '@/services/storageService'

vi.mock('@/services/storageService')
const mockService = vi.mocked(storageService)

const baseSummary = {
  disk: { total_bytes: 4_000_000_000_000, used_bytes: 2_000_000_000_000, available_bytes: 2_000_000_000_000 },
  library: { movies_bytes: 1_000_000_000_000, tv_bytes: 500_000_000_000, other_bytes: 0 },
  potential_savings_bytes: 200_000_000_000,
  files_analyzed: 10,
  files_pending_analysis: 0,
  unwatched_movie_size_bytes: 300_000_000_000,
  unwatched_tv_size_bytes: 100_000_000_000,
}

const baseFilesResponse = { total: 0, items: [] }

beforeEach(() => {
  vi.clearAllMocks()
  mockService.getSummary = vi.fn().mockResolvedValue(baseSummary)
  mockService.getFiles = vi.fn().mockResolvedValue(baseFilesResponse)
  mockService.triggerScan = vi.fn().mockResolvedValue(undefined)
})

describe('StoragePage — watched status filter', () => {
  it('renders watched status filter with All option selected by default', async () => {
    render(<StoragePage />)
    await waitFor(() => expect(mockService.getFiles).toHaveBeenCalled())
    const select = screen.getByLabelText(/watched status/i)
    expect(select).toBeInTheDocument()
    expect((select as HTMLSelectElement).value).toBe('')
  })

  it('shows recoverable space banner when unwatched filter is active', async () => {
    render(<StoragePage />)
    await waitFor(() => expect(mockService.getFiles).toHaveBeenCalled())
    const select = screen.getByLabelText(/watched status/i)
    fireEvent.change(select, { target: { value: 'unwatched' } })
    await waitFor(() => {
      expect(screen.getByText(/potentially recoverable/i)).toBeInTheDocument()
    })
  })

  it('hides recoverable banner when filter is not unwatched', async () => {
    render(<StoragePage />)
    await waitFor(() => expect(mockService.getFiles).toHaveBeenCalled())
    expect(screen.queryByText(/potentially recoverable/i)).not.toBeInTheDocument()
  })

  it('passes watchedStatus to getFiles when filter changes', async () => {
    render(<StoragePage />)
    await waitFor(() => expect(mockService.getFiles).toHaveBeenCalled())
    const select = screen.getByLabelText(/watched status/i)
    fireEvent.change(select, { target: { value: 'unwatched' } })
    await waitFor(() => {
      const calls = mockService.getFiles.mock.calls
      const lastCall = calls[calls.length - 1][0]
      expect(lastCall.watchedStatus).toBe('unwatched')
    })
  })
})

describe('StoragePage — TV show grouping', () => {
  it('renders TV show group header for episodes with show_title when unwatched filter active', async () => {
    const episodeItem = {
      id: 1,
      name: 's01e01.mkv',
      media_type: 'tv',
      size_bytes: 500_000_000,
      duration_seconds: 2700,
      video_codec: 'h264',
      video_width: 1920,
      video_height: 1080,
      mb_per_min: 11.1,
      resolution_tier: '1080p',
      efficiency_tier: 'efficient' as const,
      estimated_savings_bytes: 0,
      is_watched: false,
      show_title: 'Breaking Bad',
      show_fully_unwatched: true,
    }
    mockService.getFiles = vi.fn().mockResolvedValue({ total: 1, items: [episodeItem] })
    render(<StoragePage />)
    await waitFor(() => expect(mockService.getFiles).toHaveBeenCalled())
    const select = screen.getByLabelText(/watched status/i)
    fireEvent.change(select, { target: { value: 'unwatched' } })
    await waitFor(() => {
      expect(screen.getByText('Breaking Bad')).toBeInTheDocument()
      expect(screen.getByText(/never watched/i)).toBeInTheDocument()
    })
  })
})
