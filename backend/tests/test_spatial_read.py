"""End-to-end tests for track read endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


pytestmark = pytest.mark.asyncio


def _sample_collection(n: int, base_lon: float = -122.4) -> dict:
    base_ts = datetime(2026, 5, 28, 12, 0, 0, tzinfo=timezone.utc)
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [base_lon + i * 0.001, 37.77 + i * 0.001],
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


@pytest.fixture
async def seeded_track(client: AsyncClient) -> int:
    response = await client.post(
        "/api/v1/ingest/geojson",
        params={"label": "read-test"},
        json=_sample_collection(10),
    )
    assert response.status_code == 200
    return int(response.json()["track_id"])


async def test_get_track_returns_feature_collection(
    client: AsyncClient, seeded_track: int
) -> None:
    response = await client.get(f"/api/v1/tracks/{seeded_track}")

    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "FeatureCollection"
    assert len(body["features"]) == 10
    assert body["track"]["label"] == "read-test"

    # Coords should round-trip cleanly (no reprojection).
    first = body["features"][0]
    assert first["geometry"]["type"] == "Point"
    assert pytest.approx(first["geometry"]["coordinates"][0], abs=1e-6) == -122.4


async def test_get_track_404_when_missing(client: AsyncClient) -> None:
    response = await client.get("/api/v1/tracks/9999999")
    assert response.status_code == 404


async def test_window_filters_by_time(
    client: AsyncClient, seeded_track: int
) -> None:
    # Window the middle 3 minutes (points 2..4 inclusive).
    start = datetime(2026, 5, 28, 12, 2, tzinfo=timezone.utc).isoformat()
    end = datetime(2026, 5, 28, 12, 4, tzinfo=timezone.utc).isoformat()

    response = await client.get(
        f"/api/v1/tracks/{seeded_track}/window",
        params={"start": start, "end": end},
    )

    assert response.status_code == 200
    features = response.json()["features"]
    assert len(features) == 3
