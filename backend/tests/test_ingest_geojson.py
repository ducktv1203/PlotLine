"""End-to-end test for the GeoJSON ingest endpoint.

Exercises the full path: HTTP request → Pydantic validation → service →
async session → PostGIS. A failure here means the wire schema, the ORM
mapping, or the session lifecycle is broken.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from app.db.engine import SessionLocal
from app.main import app
from app.models.spatial import TimelinePoint, TimelineTrack


pytestmark = pytest.mark.asyncio


def _sample_collection(n: int) -> dict:
    """Build a FeatureCollection with `n` points along a synthetic path."""
    base_ts = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [-122.4194 + i * 0.0001, 37.7749 + i * 0.0001],
                },
                "properties": {
                    "timestamp": (base_ts + timedelta(seconds=i)).isoformat(),
                },
            }
            for i in range(n)
        ],
    }


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_ingest_geojson_persists_track_and_points(client: AsyncClient) -> None:
    payload = _sample_collection(5)

    response = await client.post(
        "/api/v1/ingest/geojson", params={"label": "smoke"}, json=payload
    )

    assert response.status_code == 200
    body = response.json()
    assert body["point_count"] == 5
    track_id = body["track_id"]

    async with SessionLocal() as session:
        track = await session.get(TimelineTrack, track_id)
        assert track is not None
        assert track.label == "smoke"

        count = await session.scalar(
            select(text("count(*)"))
            .select_from(TimelinePoint)
            .where(TimelinePoint.track_id == track_id)
        )
        assert count == 5


async def test_ingest_geojson_rejects_malformed_payload(client: AsyncClient) -> None:
    # Missing required `timestamp` in properties.
    bad = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
                "properties": {},
            }
        ],
    }

    response = await client.post("/api/v1/ingest/geojson", json=bad)

    assert response.status_code == 422
    assert "timestamp" in response.text


async def test_ingest_geojson_handles_10k_points(client: AsyncClient) -> None:
    payload = _sample_collection(10_000)

    response = await client.post(
        "/api/v1/ingest/geojson", params={"label": "bulk-10k"}, json=payload
    )

    assert response.status_code == 200
    assert response.json()["point_count"] == 10_000
