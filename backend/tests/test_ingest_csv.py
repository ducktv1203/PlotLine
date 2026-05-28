"""End-to-end test for the CSV ingest endpoint."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from app.db.engine import SessionLocal
from app.main import app
from app.models.spatial import TimelinePoint, TimelineTrack


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_ingest_csv_persists_track(client: AsyncClient) -> None:
    csv_text = (
        "ts,lat,lon\n"
        "2026-05-28T12:00:00+00:00,37.7749,-122.4194\n"
        "2026-05-28T12:01:00+00:00,40.7484,-73.9857\n"
        "2026-05-28T12:02:00+00:00,48.8566,2.3522\n"
    )

    response = await client.post(
        "/api/v1/ingest/csv",
        params={"label": "csv-smoke", "timestamp_col": "ts"},
        files={"file": ("track.csv", csv_text, "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["point_count"] == 3
    track_id = body["track_id"]

    async with SessionLocal() as session:
        track = await session.get(TimelineTrack, track_id)
        assert track is not None
        assert track.source_format == "csv"

        count = await session.scalar(
            select(text("count(*)"))
            .select_from(TimelinePoint)
            .where(TimelinePoint.track_id == track_id)
        )
        assert count == 3


async def test_ingest_csv_missing_column_returns_422(client: AsyncClient) -> None:
    # `lon` column missing entirely.
    csv_text = "ts,lat\n2026-05-28T12:00:00+00:00,37.7749\n"

    response = await client.post(
        "/api/v1/ingest/csv",
        params={"timestamp_col": "ts"},
        files={"file": ("bad.csv", csv_text, "text/csv")},
    )

    assert response.status_code == 422
    assert "missing required column" in response.text


async def test_ingest_csv_rejects_non_utf8(client: AsyncClient) -> None:
    payload = b"\xff\xfe not utf-8 \x00"

    response = await client.post(
        "/api/v1/ingest/csv",
        files={"file": ("binary.csv", payload, "text/csv")},
    )

    assert response.status_code == 422
    assert "utf-8" in response.text
