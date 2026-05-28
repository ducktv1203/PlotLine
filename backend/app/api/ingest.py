"""Ingestion endpoints.

The router persists validated payloads through the async session and
returns the created track id + a sanity count. Validation lives in the
Pydantic schema; persistence lives in the service.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.schemas.geojson import TimelineFeatureCollection
from app.services.ingest import features_to_orm


router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/geojson")
async def ingest_geojson(
    collection: TimelineFeatureCollection,
    label: str = Query(default="untitled", max_length=255),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int | str]:
    track, points = features_to_orm(label, "geojson", collection)

    session.add(track)
    await session.flush()  # populate track.id for the FK on each point
    for point in points:
        point.track_id = track.id

    session.add_all(points)
    await session.commit()

    return {"track_id": track.id, "point_count": len(points)}
