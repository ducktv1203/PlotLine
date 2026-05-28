"""Ingestion endpoints.

The router persists validated payloads through the async session and
returns the created track id + a sanity count. Validation lives in the
Pydantic schema; persistence lives in the service.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.engine import get_session
from app.schemas.geojson import TimelineFeatureCollection
from app.services.ingest import CsvColumnMap, csv_to_collection, features_to_orm


router = APIRouter(prefix="/ingest", tags=["ingestion"])


async def _persist(
    label: str,
    source_format: str,
    collection: TimelineFeatureCollection,
    session: AsyncSession,
) -> dict[str, int]:
    track, points = features_to_orm(label, source_format, collection)

    session.add(track)
    await session.flush()  # populate track.id for the FK on each point
    for point in points:
        point.track_id = track.id

    session.add_all(points)
    await session.commit()

    return {"track_id": track.id, "point_count": len(points)}


@router.post("/geojson")
async def ingest_geojson(
    collection: TimelineFeatureCollection,
    label: str = Query(default="untitled", max_length=255),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    return await _persist(label, "geojson", collection, session)


@router.post("/csv")
async def ingest_csv(
    file: UploadFile = File(...),
    label: str = Query(default="untitled", max_length=255),
    timestamp_col: str = Query(default="timestamp"),
    lat_col: str = Query(default="lat"),
    lon_col: str = Query(default="lon"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    raw_bytes = await file.read()
    try:
        raw = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="file must be utf-8") from exc

    try:
        collection = csv_to_collection(
            raw, CsvColumnMap(timestamp_col, lat_col, lon_col)
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return await _persist(label, "csv", collection, session)
