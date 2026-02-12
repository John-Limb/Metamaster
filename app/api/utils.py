"""Shared helpers for API endpoints."""

from __future__ import annotations

from math import ceil
from typing import Optional, Tuple


def resolve_pagination(
    *,
    limit: int,
    skip: int,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
) -> Tuple[int, int, int]:
    """Return normalized (limit, skip, current_page).

    Args:
        limit: Original `limit` query parameter (defaults to 10 in routes).
        skip: Original `skip` query parameter (defaults to 0 in routes).
        page: Optional page number provided by clients.
        page_size: Optional page size provided by clients.

    Returns:
        Tuple of (limit, skip, current_page) guaranteed to be >= 1.
    """

    effective_limit = page_size or limit
    if effective_limit <= 0:
        effective_limit = 1

    if page is not None and page >= 1:
        effective_skip = (page - 1) * effective_limit
        current_page = page
    else:
        effective_skip = skip
        current_page = (effective_skip // effective_limit) + 1

    return effective_limit, effective_skip, current_page


def pagination_metadata(*, total: int, limit: int, skip: int) -> dict:
    """Build metadata block used by paginated responses."""

    safe_limit = limit if limit > 0 else 1
    current_page = (skip // safe_limit) + 1
    total_pages = ceil(total / safe_limit) if safe_limit else 1

    return {
        "limit": safe_limit,
        "offset": skip,
        "page": current_page,
        "pageSize": safe_limit,
        "totalPages": total_pages,
    }
