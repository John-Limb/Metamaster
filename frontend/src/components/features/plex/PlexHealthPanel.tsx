import React from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getPlexHealth, resyncPlexItem } from '../../../services/plexService'

export function PlexHealthPanel() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({
    queryKey: ['plex-health'],
    queryFn: getPlexHealth,
  })

  const resync = useMutation({
    mutationFn: resyncPlexItem,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['plex-health'] }),
  })

  if (isLoading || !data) return <div className="text-sm text-gray-500">Loading Plex health...</div>

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Plex Sync Status</h4>

      {data.not_found_count === 0 ? (
        <p className="text-sm text-emerald-600 dark:text-emerald-400">All items matched in Plex.</p>
      ) : (
        <div className="space-y-2">
          <p className="text-sm text-amber-600 dark:text-amber-400">
            {data.not_found_count} item(s) not found in Plex
          </p>
          <ul className="space-y-1">
            {data.not_found_items.map((item) => (
              <li
                key={item.id}
                className="flex items-center gap-3 text-sm text-gray-700 dark:text-gray-300"
              >
                <span>
                  {item.item_type} #{item.item_id}
                  {item.last_error && (
                    <span className="text-red-500 ml-1">— {item.last_error}</span>
                  )}
                </span>
                <button
                  onClick={() => resync.mutate(item.id)}
                  disabled={resync.isPending}
                  className="px-2 py-1 text-xs bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50 transition"
                >
                  Re-sync
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
