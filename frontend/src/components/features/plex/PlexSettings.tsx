import React, { useEffect, useRef, useState } from 'react'
import { usePlexStore } from '../../../stores/plexStore'
import {
  createPlexConnection,
  initiatePlexOAuth,
  pollPlexOAuthCallback,
} from '../../../services/plexService'
import { MismatchesPanel } from './MismatchesPanel'

type AuthMode = 'oauth' | 'manual'

const INPUT_CLASS =
  'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500'

const PRIMARY_BTN_CLASS =
  'px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition text-sm font-medium'

const LABEL_CLASS = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1'

function tabClass(active: boolean) {
  return `px-4 py-2 text-sm font-medium border-b-2 transition ${
    active
      ? 'border-primary-600 text-primary-600'
      : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
  }`
}

// ---------------------------------------------------------------------------

function ConnectedView({
  serverUrl,
  onSync,
  onDisconnect,
}: {
  serverUrl: string
  onSync: () => void
  onDisconnect: () => void
}) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-700 dark:text-gray-300">
        Connected to: <strong>{serverUrl}</strong>
      </p>
      <div className="flex gap-3">
        <button type="button" onClick={onSync} className={PRIMARY_BTN_CLASS}>
          Sync Now
        </button>
        <button
          type="button"
          onClick={onDisconnect}
          className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm font-medium"
        >
          Disconnect
        </button>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------

function OAuthTab({ onConnected }: { onConnected: () => void }) {
  const [serverUrl, setServerUrl] = useState('')
  const [pinId, setPinId] = useState<number | null>(null)
  const [pending, setPending] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!pending || pinId === null) return
    pollRef.current = setInterval(async () => {
      try {
        const result = await pollPlexOAuthCallback(pinId, serverUrl)
        if (result !== null) {
          setPending(false)
          setPinId(null)
          onConnected()
        }
      } catch {
        // Network error — keep trying
      }
    }, 3000)
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [pending, pinId, serverUrl, onConnected])

  const handleConnect = async () => {
    if (!serverUrl.trim()) {
      setError('Please enter your Plex server URL first')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const redirectUri = `${window.location.origin}/settings`
      const { oauth_url, pin_id } = await initiatePlexOAuth(redirectUri)
      window.open(oauth_url, '_blank', 'width=800,height=600')
      setPinId(pin_id)
      setPending(true)
    } catch {
      setError('Failed to initiate Plex OAuth')
    } finally {
      setSaving(false)
    }
  }

  const handleCancel = () => {
    setPending(false)
    setPinId(null)
    if (pollRef.current) clearInterval(pollRef.current)
  }

  return (
    <div className="space-y-3">
      <div>
        <label htmlFor="oauth-server-url" className={LABEL_CLASS}>
          Plex Server URL
        </label>
        <input
          id="oauth-server-url"
          type="url"
          value={serverUrl}
          onChange={(e) => setServerUrl(e.target.value)}
          placeholder="http://192.168.1.x:32400"
          disabled={pending}
          className={`${INPUT_CLASS} disabled:opacity-50`}
        />
      </div>
      {pending ? (
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full animate-spin flex-shrink-0" />
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Waiting for authorisation on Plex.tv…
          </span>
          <button
            type="button"
            onClick={handleCancel}
            className="ml-auto px-3 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition"
          >
            Cancel
          </button>
        </div>
      ) : (
        <button type="button" onClick={handleConnect} disabled={saving} className={PRIMARY_BTN_CLASS}>
          Open Plex.tv to Authorise
        </button>
      )}
      {error && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------

function ManualTab({ onConnected }: { onConnected: () => void }) {
  const [serverUrl, setServerUrl] = useState('')
  const [token, setToken] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await createPlexConnection(serverUrl, token)
      onConnected()
    } catch {
      setError('Failed to connect. Check your server URL and token.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div>
        <label htmlFor="server-url" className={LABEL_CLASS}>
          Server URL
        </label>
        <input
          id="server-url"
          type="url"
          value={serverUrl}
          onChange={(e) => setServerUrl(e.target.value)}
          placeholder="http://192.168.1.x:32400"
          required
          className={INPUT_CLASS}
        />
      </div>
      <div>
        <label htmlFor="plex-token" className={LABEL_CLASS}>
          Plex Token
        </label>
        <input
          id="plex-token"
          type="text"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          required
          className={INPUT_CLASS}
        />
      </div>
      <button type="submit" disabled={saving} className={PRIMARY_BTN_CLASS}>
        Connect
      </button>
      {error && (
        <p role="alert" className="text-sm text-red-600 dark:text-red-400">
          {error}
        </p>
      )}
    </form>
  )
}

// ---------------------------------------------------------------------------

export function PlexSettings() {
  const {
    connection,
    isLoading,
    error,
    mismatches,
    fetchConnection,
    disconnect,
    sync,
    fetchMismatches,
    resolveMismatch,
  } = usePlexStore()
  const [authMode, setAuthMode] = useState<AuthMode>('oauth')

  useEffect(() => {
    fetchConnection()
    fetchMismatches()
  }, [fetchConnection, fetchMismatches])

  if (isLoading) return <div>Loading...</div>

  return (
    <div className="space-y-4">
      {error && (
        <div role="alert" className="text-red-600 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {connection ? (
        <>
          <ConnectedView
            serverUrl={connection.server_url}
            onSync={sync}
            onDisconnect={disconnect}
          />
          <MismatchesPanel mismatches={mismatches} onResolve={resolveMismatch} />
        </>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">Not connected</p>
          <div role="tablist" className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
            <button
              type="button"
              role="tab"
              aria-selected={authMode === 'oauth'}
              onClick={() => setAuthMode('oauth')}
              className={tabClass(authMode === 'oauth')}
            >
              Connect via Plex.tv
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={authMode === 'manual'}
              onClick={() => setAuthMode('manual')}
              className={tabClass(authMode === 'manual')}
            >
              Manual Token
            </button>
          </div>

          {authMode === 'oauth' && <OAuthTab onConnected={fetchConnection} />}
          {authMode === 'manual' && <ManualTab onConnected={fetchConnection} />}
        </div>
      )}
    </div>
  )
}
