"""Seed default PlexCollectionSet rows for franchise/genre/decade."""

import logging

from sqlalchemy.orm import Session

from app.domain.plex.collection_models import PlexCollectionSet, SetType
from app.domain.plex.models import PlexConnection

logger = logging.getLogger(__name__)


def seed_collection_sets(db: Session) -> None:
    """Create PlexCollectionSet rows for all SetType values if missing.

    Finds the active connection and ensures one row per SetType exists.
    All seeded sets default to enabled=False.
    """
    conn = db.query(PlexConnection).filter(PlexConnection.is_active.is_(True)).first()
    if conn is None:
        return

    for set_type in SetType:
        existing = (
            db.query(PlexCollectionSet)
            .filter(
                PlexCollectionSet.connection_id == conn.id,
                PlexCollectionSet.set_type == set_type,
            )
            .first()
        )
        if existing is None:
            db.add(PlexCollectionSet(connection_id=conn.id, set_type=set_type, enabled=False))
            logger.info("Plex: seeded collection set type=%s", set_type.value)

    db.commit()
