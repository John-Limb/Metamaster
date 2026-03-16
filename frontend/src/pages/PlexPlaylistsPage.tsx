import { useEffect } from 'react'
import { usePlexCollectionStore } from '../stores/plexCollectionStore'
import { PlaylistCard } from '../components/features/plex/PlaylistCard'
import { Button } from '@/components/common/Button'
import { EmptyState } from '@/components/common/EmptyState'
import { SkeletonCard } from '@/components/common/Skeleton'

export function PlexPlaylistsPage() {
  const {
    playlists,
    playlistsLoading,
    playlistsError,
    fetchPlaylists,
    updatePlaylist,
    deletePlaylist,
    pushPlaylist,
    pullPlaylists,
  } = usePlexCollectionStore()

  useEffect(() => {
    fetchPlaylists()
  }, [fetchPlaylists])

  const handleTogglePlaylist = (id: number, enabled: boolean) => {
    updatePlaylist(id, { enabled })
  }

  return (
    <div className="space-y-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Plex Playlists</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Manage playlists synced to your Plex server.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          disabled={playlistsLoading}
          onClick={() => pullPlaylists()}
        >
          Pull from Plex
        </Button>
      </div>

      {playlistsError && (
        <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3 text-sm text-red-700 dark:text-red-400">
          {playlistsError}
        </div>
      )}

      {playlistsLoading && playlists.length === 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      ) : playlists.length === 0 ? (
        <EmptyState
          variant="noData"
          title="No playlists yet"
          description="Pull from Plex to import your playlists."
          action={{
            label: 'Pull from Plex',
            onClick: pullPlaylists,
            disabled: playlistsLoading,
          }}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {playlists.map(pl => (
            <PlaylistCard
              key={pl.id}
              playlist={pl}
              onToggleEnabled={handleTogglePlaylist}
              onPush={pushPlaylist}
              onDelete={deletePlaylist}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default PlexPlaylistsPage
