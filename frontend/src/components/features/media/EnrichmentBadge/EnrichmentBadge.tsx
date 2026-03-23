import React from 'react';

export type EnrichmentStatus =
  | 'pending_local'
  | 'local_only'
  | 'pending_external'
  | 'fully_enriched'
  | 'external_failed'
  | 'not_found'
  | null
  | undefined;

interface EnrichmentBadgeProps {
  status: EnrichmentStatus;
  className?: string;
}

export const EnrichmentBadge: React.FC<EnrichmentBadgeProps> = ({ status, className = '' }: EnrichmentBadgeProps) => {
  if (!status) return null;

  if (status === 'fully_enriched') {
    return (
      <span
        title="Fully enriched"
        aria-label="Fully enriched"
        className={`inline-flex items-center justify-center w-5 h-5 rounded-full bg-green-500 text-white text-xs font-bold ${className}`}
      >
        ✓
      </span>
    );
  }

  if (status === 'not_found') {
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 ${className}`}>
        Manual needed
      </span>
    );
  }

  if (status === 'local_only' || status === 'external_failed') {
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 ${className}`}>
        Local only
      </span>
    );
  }

  // pending_local or pending_external
  return (
    <span
      role="status"
      aria-label="Enrichment pending"
      className={`inline-block w-4 h-4 border-2 border-edge border-t-blue-500 rounded-full animate-spin ${className}`}
    />
  );
};

export default EnrichmentBadge;
