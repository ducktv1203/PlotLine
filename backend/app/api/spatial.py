"""Spatial read endpoints — fetch tracks and time-windowed slices."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.models.spatial import TimelinePoint, TimelineTrack


router = APIRouter(prefix="/tracks", tags=["spatial"])


async def _serialize_points(
    session: AsyncSession, track_id: int, start: datetime | None, end: datetime | None
) -> dict:
    track = await session.get(TimelineTrack, track_id)
    if track is None:
        raise HTTPException(status_code=404, detail=f"track {track_id} not found")

    # Pull lon/lat directly from PostGIS in one round-trip — avoids the
    # N+1 of fetching ORM rows then asking the DB for ST_AsText per row.
    stmt = (
        select(
            TimelinePoint.observed_at,
            TimelinePoint.geom.ST_X().label("lon"),
            TimelinePoint.geom.ST_Y().label("lat"),
        )
        .where(TimelinePoint.track_id == track_id)
        .order_by(TimelinePoint.observed_at)
    )
    if start is not None:
        stmt = stmt.where(TimelinePoint.observed_at >= start)
    if end is not None:
        stmt = stmt.where(TimelinePoint.observed_at <= end)

    rows = (await session.execute(stmt)).all()

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {"timestamp": observed_at.isoformat()},
        }
        for observed_at, lon, lat in rows
    ]

    return {
        "type": "FeatureCollection",
        "features": features,
        "track": {
            "id": track.id,
            "label": track.label,
            "source_format": track.source_format,
        },
    }


@router.get("/{track_id}")
async def get_track(
    track_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    return await _serialize_points(session, track_id, None, None)


@router.get("/{track_id}/window")
async def get_track_window(
    track_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
) -> dict:
    return await _serialize_points(session, track_id, start, end)
