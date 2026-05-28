"""Top-level API router.

Mounts the sub-routers exposed by this package. As capability surfaces
grow (spatial queries, exports, ...) add their routers here.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.ingest import router as ingest_router
from app.api.spatial import intersections_router, router as spatial_router


router = APIRouter()
router.include_router(ingest_router)
router.include_router(spatial_router)
router.include_router(intersections_router)
