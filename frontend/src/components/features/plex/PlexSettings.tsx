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

  useEffect(() => {
    fetchConnection()
  }, [fetchConnection])

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
    <div className="space-y-4">
      {error && <div role="alert" className="text-red-600 dark:text-red-400 text-sm">{error}</div>}

      {connection ? (
        <div className="space-y-3">
          <p className="text-sm text-gray-700 dark:text-gray-300">
            Connected to: <strong>{connection.server_url}</strong>
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => sync()}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition text-sm font-medium"
            >
              Sync Now
            </button>
            <button
              onClick={disconnect}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm font-medium"
            >
              Disconnect
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">Not connected</p>
          <div role="tablist" className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
            <button
              role="tab"
              aria-selected={authMode === 'oauth'}
              onClick={() => setAuthMode('oauth')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
                authMode === 'oauth'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Connect via Plex.tv
            </button>
            <button
              role="tab"
              aria-selected={authMode === 'manual'}
              onClick={() => setAuthMode('manual')}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition ${
                authMode === 'manual'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Manual Token
            </button>
          </div>

          {authMode === 'oauth' && (
            <button
              onClick={handleOAuthConnect}
              disabled={saving}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition text-sm font-medium"
            >
              Open Plex.tv to Authorise
            </button>
          )}

          {authMode === 'manual' && (
            <form onSubmit={handleManualConnect} className="space-y-3">
              <div>
                <label
                  htmlFor="server-url"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                >
                  Server URL
                </label>
                <input
                  id="server-url"
                  type="url"
                  value={serverUrl}
                  onChange={(e) => setServerUrl(e.target.value)}
                  placeholder="http://192.168.1.x:32400"
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div>
                <label
                  htmlFor="plex-token"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                >
                  Plex Token
                </label>
                <input
                  id="plex-token"
                  type="text"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <button
                type="submit"
                disabled={saving}
                className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition text-sm font-medium"
              >
                Connect
              </button>
            </form>
          )}

          {saveError && (
            <p role="alert" className="text-sm text-red-600 dark:text-red-400">
              {saveError}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
