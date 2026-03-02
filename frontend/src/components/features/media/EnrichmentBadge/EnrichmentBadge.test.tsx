import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { EnrichmentBadge } from './EnrichmentBadge';

describe('EnrichmentBadge', () => {
  it('shows green tick for fully_enriched', () => {
    render(<EnrichmentBadge status="fully_enriched" />);
    expect(screen.getByTitle('Fully enriched')).toBeInTheDocument();
  });

  it('shows amber Local only badge for local_only', () => {
    render(<EnrichmentBadge status="local_only" />);
    expect(screen.getByText('Local only')).toBeInTheDocument();
  });

  it('shows amber Local only badge for external_failed', () => {
    render(<EnrichmentBadge status="external_failed" />);
    expect(screen.getByText('Local only')).toBeInTheDocument();
  });

  it('shows red Manual needed badge for not_found', () => {
    render(<EnrichmentBadge status="not_found" />);
    expect(screen.getByText('Manual needed')).toBeInTheDocument();
  });

  it('shows spinner for pending_external', () => {
    render(<EnrichmentBadge status="pending_external" />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows spinner for pending_local', () => {
    render(<EnrichmentBadge status="pending_local" />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders nothing for null status', () => {
    const { container } = render(<EnrichmentBadge status={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders nothing for undefined status', () => {
    const { container } = render(<EnrichmentBadge status={undefined} />);
    expect(container.firstChild).toBeNull();
  });
});
