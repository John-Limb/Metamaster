# Plex Integration — Phase 6: Frontend — Connection Settings

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Plex connection settings panel to the MetaMaster admin/settings UI. Supports OAuth flow (primary) and manual token entry (fallback). Shows connection status and disconnect button.

**Architecture:** New `PlexSettings` component under `frontend/src/components/features/plex/`. New `plexService.ts` API client. New `plexStore` Zustand store. Wired into the existing settings page.

**Tech Stack:** React, TypeScript, Zustand, TanStack Query, Vitest, axios

**Prerequisite:** Phases 1–5 complete (API endpoints exist).

---

### Task 1: Plex API service

**Files:**
- Create: `frontend/src/services/plexService.ts`
- Create: `frontend/src/services/__tests__/plexService.test.ts`

**Step 1: Write failing tests**

```typescript
// frontend/src/services/__tests__/plexService.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { getPlexConnection, createPlexConnection, deletePlexConnection, triggerPlexSync, initiatePlexOAuth } from '../plexService'

vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('plexService', () => {
  beforeEach(() => vi.clearAllMocks())

  it('getPlexConnection calls correct endpoint', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { id: 1, server_url: 'http://plex:32400', is_active: true } })
    const result = await getPlexConnection()
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/plex/connection')
    expect(result.id).toBe(1)
  })

  it('createPlexConnection posts server_url and token', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({ data: { id: 1 } })
    await createPlexConnection('http://plex:32400', 'my-token')
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/v1/plex/connection', {
      server_url: 'http://plex:32400',
      token: 'my-token',
    })
  })

  it('triggerPlexSync posts to sync endpoint', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({ data: { task_id: 'abc', message: 'ok' } })
    const result = await triggerPlexSync()
    expect(result.task_id).toBe('abc')
  })

  it('initiatePlexOAuth returns oauth_url and pin_id', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { oauth_url: 'https://plex.tv', pin_id: 42 } })
    const result = await initiatePlexOAuth('http://localhost/callback')
    expect(result.pin_id).toBe(42)
  })
})
```

**Step 2: Run to verify failure**

```bash
cd frontend && npm run test -- plexService --run
```
Expected: Cannot find module `../plexService`

**Step 3: Implement service**

```typescript
// frontend/src/services/plexService.ts
import axios from 'axios'

export interface PlexConnection {
  id: number
  server_url: string
  is_active: boolean
  movie_library_id: string | null
  tv_library_id: string | null
  created_at: string
  last_connected_at: string | null
}

export interface PlexSyncResponse {
  task_id: string
  message: string
}

export interface PlexOAuthInitResponse {
  oauth_url: string
  pin_id: number
}

export async function getPlexConnection(): Promise<PlexConnection> {
  const { data } = await axios.get<PlexConnection>('/api/v1/plex/connection')
  return data
}

export async function createPlexConnection(
  serverUrl: string,
  token: string
): Promise<PlexConnection> {
  const { data } = await axios.post<PlexConnection>('/api/v1/plex/connection', {
    server_url: serverUrl,
    token,
  })
  return data
}

export async function deletePlexConnection(): Promise<void> {
  await axios.delete('/api/v1/plex/connection')
}

export async function triggerPlexSync(): Promise<PlexSyncResponse> {
  const { data } = await axios.post<PlexSyncResponse>('/api/v1/plex/sync')
  return data
}

export async function initiatePlexOAuth(
  redirectUri: string
): Promise<PlexOAuthInitResponse> {
  const { data } = await axios.get<PlexOAuthInitResponse>(
    '/api/v1/plex/oauth/initiate',
    { params: { redirect_uri: redirectUri } }
  )
  return data
}

export async function pollPlexOAuthCallback(
  pinId: number,
  serverUrl: string
): Promise<PlexConnection> {
  const { data } = await axios.get<PlexConnection>('/api/v1/plex/oauth/callback', {
    params: { pin_id: pinId, server_url: serverUrl },
  })
  return data
}
```

**Step 4: Run tests**

```bash
cd frontend && npm run test -- plexService --run
```
Expected: All PASSED.

**Step 5: Commit**

```bash
git add frontend/src/services/plexService.ts frontend/src/services/__tests__/plexService.test.ts
git commit -m "feat(plex): add Plex API service client"
```

---

### Task 2: Plex Zustand store

**Files:**
- Create: `frontend/src/stores/plexStore.ts`
- Create: `frontend/src/stores/__tests__/plexStore.test.ts`

**Step 1: Write failing tests**

```typescript
// frontend/src/stores/__tests__/plexStore.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { usePlexStore } from '../plexStore'
import * as plexService from '../../services/plexService'

vi.mock('../../services/plexService')

describe('plexStore', () => {
  beforeEach(() => {
    usePlexStore.setState({ connection: null, isLoading: false, error: null })
    vi.clearAllMocks()
  })

  it('fetchConnection sets connection on success', async () => {
    vi.mocked(plexService.getPlexConnection).mockResolvedValue({
      id: 1, server_url: 'http://plex:32400', is_active: true,
      movie_library_id: '1', tv_library_id: '2',
      created_at: '2026-03-05T00:00:00', last_connected_at: null,
    })
    await usePlexStore.getState().fetchConnection()
    expect(usePlexStore.getState().connection?.id).toBe(1)
    expect(usePlexStore.getState().isLoading).toBe(false)
  })

  it('fetchConnection sets null on 404', async () => {
    vi.mocked(plexService.getPlexConnection).mockRejectedValue({ response: { status: 404 } })
    await usePlexStore.getState().fetchConnection()
    expect(usePlexStore.getState().connection).toBeNull()
  })

  it('disconnect calls deletePlexConnection and clears state', async () => {
    vi.mocked(plexService.deletePlexConnection).mockResolvedValue(undefined)
    usePlexStore.setState({ connection: { id: 1 } as any })
    await usePlexStore.getState().disconnect()
    expect(usePlexStore.getState().connection).toBeNull()
  })
})
```

**Step 2: Run to verify failure**

```bash
cd frontend && npm run test -- plexStore --run
```
Expected: Cannot find module `../plexStore`

**Step 3: Implement store**

```typescript
// frontend/src/stores/plexStore.ts
import { create } from 'zustand'
import {
  PlexConnection,
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
    } catch (err: any) {
      if (err?.response?.status === 404) {
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
```

**Step 4: Run tests**

```bash
cd frontend && npm run test -- plexStore --run
```
Expected: All PASSED.

**Step 5: Commit**

```bash
git add frontend/src/stores/plexStore.ts frontend/src/stores/__tests__/plexStore.test.ts
git commit -m "feat(plex): add Plex Zustand store"
```

---

### Task 3: PlexSettings component

**Files:**
- Create: `frontend/src/components/features/plex/PlexSettings.tsx`
- Create: `frontend/src/components/features/plex/__tests__/PlexSettings.test.tsx`

**Step 1: Write failing tests**

```typescript
// frontend/src/components/features/plex/__tests__/PlexSettings.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PlexSettings } from '../PlexSettings'
import { usePlexStore } from '../../../../stores/plexStore'

vi.mock('../../../../stores/plexStore')

describe('PlexSettings', () => {
  beforeEach(() => vi.clearAllMocks())

  it('shows "Not connected" when no connection', () => {
    vi.mocked(usePlexStore).mockReturnValue({
      connection: null, isLoading: false, error: null,
      fetchConnection: vi.fn(), disconnect: vi.fn(), sync: vi.fn(),
    } as any)
    render(<PlexSettings />)
    expect(screen.getByText(/not connected/i)).toBeInTheDocument()
  })

  it('shows server URL and disconnect button when connected', () => {
    vi.mocked(usePlexStore).mockReturnValue({
      connection: { id: 1, server_url: 'http://plex:32400', is_active: true } as any,
      isLoading: false, error: null,
      fetchConnection: vi.fn(), disconnect: vi.fn(), sync: vi.fn(),
    } as any)
    render(<PlexSettings />)
    expect(screen.getByText('http://plex:32400')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /disconnect/i })).toBeInTheDocument()
  })

  it('shows manual token form when OAuth tab not selected', () => {
    vi.mocked(usePlexStore).mockReturnValue({
      connection: null, isLoading: false, error: null,
      fetchConnection: vi.fn(), disconnect: vi.fn(), sync: vi.fn(),
    } as any)
    render(<PlexSettings />)
    fireEvent.click(screen.getByRole('tab', { name: /manual token/i }))
    expect(screen.getByLabelText(/plex token/i)).toBeInTheDocument()
  })
})
```

**Step 2: Run to verify failure**

```bash
cd frontend && npm run test -- PlexSettings --run
```
Expected: Cannot find module `../PlexSettings`

**Step 3: Implement component**

```tsx
// frontend/src/components/features/plex/PlexSettings.tsx
import React, { useEffect, useState } from 'react'
import { usePlexStore } from '../../../stores/plexStore'
import { createPlexConnection, initiatePlexOAuth } from '../../../services/plexService'

type AuthMode = 'oauth' | 'manual'

export function PlexSettings() {
  const { connection, isLoading, error, fetchConnection, disconnect, sync } = usePlexStore()
  const [authMode, setAuthMode] = useState<AuthMode>('oauth')
  const [serverUrl, setServerUrl] = useState('')
  const [token, setToken] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  useEffect(() => { fetchConnection() }, [fetchConnection])

  const handleOAuthConnect = async () => {
    setSaving(true)
    setSaveError(null)
    try {
      const redirectUri = `${window.location.origin}/plex/callback`
      const { oauth_url } = await initiatePlexOAuth(redirectUri)
      window.open(oauth_url, '_blank', 'width=800,height=600')
    } catch {
      setSaveError('Failed to initiate Plex OAuth')
    } finally {
      setSaving(false)
    }
  }

  const handleManualConnect = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setSaveError(null)
    try {
      await createPlexConnection(serverUrl, token)
      await fetchConnection()
    } catch {
      setSaveError('Failed to connect. Check your server URL and token.')
    } finally {
      setSaving(false)
    }
  }

  if (isLoading) return <div>Loading...</div>

  return (
    <div>
      <h3>Plex Integration</h3>
      {error && <div role="alert">{error}</div>}

      {connection ? (
        <div>
          <p>Connected to: <strong>{connection.server_url}</strong></p>
          <button onClick={() => sync()}>Sync Now</button>
          <button onClick={disconnect}>Disconnect</button>
        </div>
      ) : (
        <div>
          <p>Not connected</p>
          <div role="tablist">
            <button role="tab" onClick={() => setAuthMode('oauth')}
              aria-selected={authMode === 'oauth'}>
              Connect via Plex.tv
            </button>
            <button role="tab" onClick={() => setAuthMode('manual')}
              aria-selected={authMode === 'manual'}>
              Manual Token
            </button>
          </div>

          {authMode === 'oauth' && (
            <button onClick={handleOAuthConnect} disabled={saving}>
              Open Plex.tv to Authorise
            </button>
          )}

          {authMode === 'manual' && (
            <form onSubmit={handleManualConnect}>
              <label htmlFor="server-url">Server URL</label>
              <input id="server-url" value={serverUrl}
                onChange={e => setServerUrl(e.target.value)}
                placeholder="http://192.168.1.x:32400" required />
              <label htmlFor="plex-token">Plex Token</label>
              <input id="plex-token" value={token}
                onChange={e => setToken(e.target.value)} required />
              <button type="submit" disabled={saving}>Connect</button>
            </form>
          )}

          {saveError && <p role="alert">{saveError}</p>}
        </div>
      )}
    </div>
  )
}
```

**Step 4: Run tests**

```bash
cd frontend && npm run test -- PlexSettings --run
```
Expected: All PASSED.

**Step 5: Wire into existing settings page**

Find the settings page (search for it):
```bash
grep -rl "Settings\|settings" frontend/src/pages/ | head -5
```

Import and add `<PlexSettings />` in an appropriate section.

**Step 6: Type check**

```bash
cd frontend && npm run type-check
```
Expected: No errors.

**Step 7: Lint**

```bash
cd frontend && npm run lint
```

**Step 8: Commit**

```bash
git add frontend/src/components/features/plex/ frontend/src/stores/plexStore.ts frontend/src/services/plexService.ts
git commit -m "feat(plex): add Plex connection settings UI"
```
