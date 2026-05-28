"""End-to-end tests for the /spatial/intersections endpoint."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


pytestmark = pytest.mark.asyncio


def _line(
    start_lon: float, start_lat: float, base_ts: datetime, n: int
) -> dict:
    """Build a track that walks east at 0.0001 deg/min from (start_lon, start_lat)."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [start_lon + i * 0.0001, start_lat],
                },
                "properties": {
                    "timestamp": (base_ts + timedelta(minutes=i)).isoformat(),
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


async def test_intersections_finds_overlapping_tracks(client: AsyncClient) -> None:
    base_ts = datetime(2026, 5, 28, 14, 0, tzinfo=timezone.utc)

    # Track A walks east through a fixed point at t=10.
    a = await client.post(
        "/api/v1/ingest/geojson",
        params={"label": "A"},
        json=_line(-122.40, 37.78, base_ts, 30),
    )
    # Track B walks east through the same area, arriving at t=11 (1 min later).
    b = await client.post(
        "/api/v1/ingest/geojson",
        params={"label": "B"},
        json=_line(-122.40, 37.78, base_ts + timedelta(minutes=1), 30),
    )
    a_id = a.json()["track_id"]
    b_id = b.json()["track_id"]

    response = await client.get(
        "/api/v1/spatial/intersections",
        params={
            "track_ids": [a_id, b_id],
            "tolerance_m": 50,
            "tolerance_s": 120,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] > 0
    # All hits should pair the two tracks in canonical (min,max) order.
    for hit in body["intersections"]:
        assert hit["track_a"] == min(a_id, b_id)
        assert hit["track_b"] == max(a_id, b_id)
        assert hit["distance_m"] <= 50
        assert hit["delta_s"] < 120


async def test_intersections_empty_when_tracks_far_apart(
    client: AsyncClient,
) -> None:
    base_ts = datetime(2026, 5, 28, 15, 0, tzinfo=timezone.utc)

    a = await client.post(
        "/api/v1/ingest/geojson",
        params={"label": "A"},
        json=_line(-122.40, 37.78, base_ts, 10),
    )
    # Track B is in New York — far outside any reasonable tolerance.
    b = await client.post(
        "/api/v1/ingest/geojson",
        params={"label": "B"},
        json=_line(-73.99, 40.75, base_ts, 10),
    )

    response = await client.get(
        "/api/v1/spatial/intersections",
        params={
            "track_ids": [a.json()["track_id"], b.json()["track_id"]],
            "tolerance_m": 50,
            "tolerance_s": 60,
        },
    )

    assert response.status_code == 200
    assert response.json()["count"] == 0


async def test_intersections_requires_at_least_two_tracks(
    client: AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/spatial/intersections", params={"track_ids": [1]}
    )
    assert response.status_code == 422


async def test_list_tracks_returns_recent_first(client: AsyncClient) -> None:
    response = await client.get("/api/v1/tracks")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    if len(body) >= 2:
        # ordered by id desc
        assert body[0]["id"] >= body[1]["id"]
