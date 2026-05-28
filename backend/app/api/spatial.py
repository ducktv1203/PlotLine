"""Spatial read endpoints — fetch tracks, time-windowed slices, and
space-time intersections across tracks."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.models.spatial import TimelinePoint, TimelineTrack


router = APIRouter(prefix="/tracks", tags=["spatial"])
intersections_router = APIRouter(prefix="/spatial", tags=["spatial"])


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


@router.get("")
async def list_tracks(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[dict]:
    """Return all tracks (id, label, source_format) ordered newest first."""
    rows = (
        await session.execute(
            select(TimelineTrack).order_by(TimelineTrack.id.desc())
        )
    ).scalars().all()
    return [
        {"id": t.id, "label": t.label, "source_format": t.source_format}
        for t in rows
    ]


# --- Intersections --- ----------------------------------------------------- #


@intersections_router.get("/intersections")
async def find_intersections(
    session: Annotated[AsyncSession, Depends(get_session)],
    track_ids: Annotated[list[int], Query(min_length=2)],
    tolerance_m: float = Query(default=50.0, gt=0.0),
    tolerance_s: float = Query(default=300.0, gt=0.0),
    limit: int = Query(default=500, gt=0, le=5000),
) -> dict:
    """Find space-time intersections among the given tracks.

    A pair (a, b) is an intersection iff their geographies are within
    `tolerance_m` meters AND their observation times differ by less than
    `tolerance_s` seconds. Results are deduped via `a.track_id < b.track_id`.
    """
    sql = text(
        """
        SELECT
            a.track_id AS track_a,
            b.track_id AS track_b,
            ST_X(a.geom) AS lon,
            ST_Y(a.geom) AS lat,
            a.observed_at AS t_a,
            b.observed_at AS t_b,
            ST_Distance(a.geom::geography, b.geom::geography) AS dist_m,
            ABS(EXTRACT(EPOCH FROM (a.observed_at - b.observed_at))) AS dt_s
        FROM timeline_points a
        JOIN timeline_points b
          ON a.track_id < b.track_id
         AND ST_DWithin(a.geom::geography, b.geom::geography, :tolerance_m)
         AND ABS(EXTRACT(EPOCH FROM (a.observed_at - b.observed_at))) < :tolerance_s
        WHERE a.track_id = ANY(:track_ids)
          AND b.track_id = ANY(:track_ids)
        ORDER BY a.observed_at
        LIMIT :limit
        """
    )

    rows = (
        await session.execute(
            sql,
            {
                "track_ids": track_ids,
                "tolerance_m": tolerance_m,
                "tolerance_s": tolerance_s,
                "limit": limit,
            },
        )
    ).mappings().all()

    return {
        "intersections": [
            {
                "track_a": r["track_a"],
                "track_b": r["track_b"],
                "lon": r["lon"],
                "lat": r["lat"],
                "t_a": r["t_a"].isoformat(),
                "t_b": r["t_b"].isoformat(),
                "distance_m": float(r["dist_m"]),
                "delta_s": float(r["dt_s"]),
            }
            for r in rows
        ],
        "count": len(rows),
    }
