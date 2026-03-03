"""File Organisation API endpoints"""

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.organisation.service import (
    VALID_PRESETS,
    apply_renames,
    get_conformance_stats,
    get_preview,
    get_saved_preset,
    save_preset,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/organisation", tags=["Organisation"])


# ---------------------------------------------------------------------------
# Response / request models
# ---------------------------------------------------------------------------


class PresetPayload(BaseModel):
    preset: str


class PresetResponse(BaseModel):
    preset: str


class ConformanceStatsResponse(BaseModel):
    movies_match: int
    movies_need_rename: int
    movies_unenriched: int
    episodes_match: int
    episodes_need_rename: int
    episodes_unenriched: int


class RenamePreviewItem(BaseModel):
    file_id: int
    file_type: str
    current_path: str
    target_path: str
    show_title: str | None = None
    season_number: int | None = None


class PreviewResponse(BaseModel):
    movies: list[RenamePreviewItem]
    episodes: list[RenamePreviewItem]


class RenameItem(BaseModel):
    file_id: int
    file_type: Literal["movie", "episode"]
    target_path: str


class ApplyPayload(BaseModel):
    items: list[RenameItem]


class ApplyResult(BaseModel):
    success: int
    failed: int
    errors: list[str]


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@router.get("/settings", response_model=PresetResponse)
def get_organisation_settings(db: Session = Depends(get_db)):
    return {"preset": get_saved_preset(db)}


@router.put("/settings", response_model=PresetResponse)
def update_organisation_settings(payload: PresetPayload, db: Session = Depends(get_db)):
    if payload.preset not in VALID_PRESETS:
        raise HTTPException(status_code=400, detail=f"preset must be one of: {list(VALID_PRESETS)}")
    save_preset(db, payload.preset)
    return {"preset": payload.preset}


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


@router.get("/stats", response_model=ConformanceStatsResponse)
def get_stats(preset: str | None = None, db: Session = Depends(get_db)):
    active_preset = preset or get_saved_preset(db)
    if active_preset not in VALID_PRESETS:
        raise HTTPException(status_code=400, detail=f"preset must be one of: {list(VALID_PRESETS)}")
    return get_conformance_stats(db, active_preset)


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------


@router.get("/preview", response_model=PreviewResponse)
def preview_renames(preset: str | None = None, db: Session = Depends(get_db)):
    active_preset = preset or get_saved_preset(db)
    if active_preset not in VALID_PRESETS:
        raise HTTPException(status_code=400, detail=f"preset must be one of: {list(VALID_PRESETS)}")
    return get_preview(db, active_preset)


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


@router.post("/apply", response_model=ApplyResult)
def apply_organisation(payload: ApplyPayload, db: Session = Depends(get_db)):
    items = [item.model_dump() for item in payload.items]
    result = apply_renames(db, items)
    return result
