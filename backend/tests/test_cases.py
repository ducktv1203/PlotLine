"""End-to-end tests for the /cases endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


pytestmark = pytest.mark.asyncio


def _sample_collection(n: int) -> dict:
    base_ts = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [-122.0 + i * 0.001, 37.5],
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


async def _seed_tracks(client: AsyncClient, count: int) -> list[int]:
    ids: list[int] = []
    for i in range(count):
        res = await client.post(
            "/api/v1/ingest/geojson",
            params={"label": f"case-test-{i}"},
            json=_sample_collection(5),
        )
        ids.append(int(res.json()["track_id"]))
    return ids


async def test_create_case_with_tracks(client: AsyncClient) -> None:
    track_ids = await _seed_tracks(client, 2)

    res = await client.post(
        "/api/v1/cases",
        json={
            "name": "Test Investigation",
            "description": "round-trip",
            "track_ids": track_ids,
        },
    )

    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "Test Investigation"
    assert sorted(body["track_ids"]) == sorted(track_ids)


async def test_get_case_returns_track_ids(client: AsyncClient) -> None:
    track_ids = await _seed_tracks(client, 1)
    created = (
        await client.post(
            "/api/v1/cases",
            json={"name": "Single", "track_ids": track_ids},
        )
    ).json()

    res = await client.get(f"/api/v1/cases/{created['id']}")
    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "Single"
    assert body["track_ids"] == track_ids


async def test_create_case_rejects_unknown_track(client: AsyncClient) -> None:
    res = await client.post(
        "/api/v1/cases",
        json={"name": "Bad", "track_ids": [999_999]},
    )
    assert res.status_code == 422


async def test_list_cases_returns_track_count(client: AsyncClient) -> None:
    track_ids = await _seed_tracks(client, 3)
    await client.post(
        "/api/v1/cases",
        json={"name": "Triple", "track_ids": track_ids},
    )

    res = await client.get("/api/v1/cases")
    assert res.status_code == 200
    body = res.json()
    # Most recent first.
    assert body[0]["name"] == "Triple"
    assert body[0]["track_count"] == 3


async def test_delete_case(client: AsyncClient) -> None:
    created = (
        await client.post("/api/v1/cases", json={"name": "Ephemeral"})
    ).json()

    deleted = await client.delete(f"/api/v1/cases/{created['id']}")
    assert deleted.status_code == 204

    follow_up = await client.get(f"/api/v1/cases/{created['id']}")
    assert follow_up.status_code == 404
