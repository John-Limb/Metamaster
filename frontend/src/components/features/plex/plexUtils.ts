export const BUILDER_LABELS: Record<string, string> = {
  tmdb_collection: 'TMDB',
  static_items: 'Static',
  genre: 'Genre',
  decade: 'Decade',
}

export function formatSyncDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString()
}
