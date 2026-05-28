"""API router skeleton.

Placeholder endpoints for the two principal capability surfaces:
  - ingestion  (CSV / custom GeoJSON timeline upload)
  - spatial    (intersections, path resolution, temporal range queries)

No handlers are implemented in Phase 0.
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.post("/ingest", tags=["ingestion"])
async def ingest_placeholder() -> dict[str, str]:
    return {"status": "not_implemented"}


@router.get("/spatial/query", tags=["spatial"])
async def spatial_query_placeholder() -> dict[str, str]:
    return {"status": "not_implemented"}
