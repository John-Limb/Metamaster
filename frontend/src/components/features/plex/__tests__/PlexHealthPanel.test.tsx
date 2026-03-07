import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { PlexHealthPanel } from '../PlexHealthPanel'
import * as plexService from '../../../../services/plexService'

vi.mock('../../../../services/plexService')

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider
      client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}
    >
      {children}
    </QueryClientProvider>
  )
}

describe('PlexHealthPanel', () => {
  it('shows not_found items with resync button', async () => {
    vi.mocked(plexService.getPlexHealth).mockResolvedValue({
      connected: true,
      not_found_count: 1,
      not_found_items: [{ id: 5, item_type: 'movie', item_id: 42, last_error: null }],
    })
    vi.mocked(plexService.resyncPlexItem).mockResolvedValue(undefined)
    render(<PlexHealthPanel />, { wrapper })
    expect(await screen.findByText(/movie #42/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /re-sync/i })).toBeInTheDocument()
  })

  it('shows healthy state when no issues', async () => {
    vi.mocked(plexService.getPlexHealth).mockResolvedValue({
      connected: true,
      not_found_count: 0,
      not_found_items: [],
    })
    render(<PlexHealthPanel />, { wrapper })
    expect(await screen.findByText(/all items matched/i)).toBeInTheDocument()
  })
})
