"""Unit tests for the pure ingest transforms.

Intentionally no DB. These tests verify shape, ordering, and EWKT formatting
without booting Postgres — they should run in milliseconds.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.geojson import (
    PointGeometry,
    TimelineFeature,
    TimelineFeatureCollection,
    TimelineFeatureProperties,
)
from app.services.ingest import features_to_orm


def _make_collection(points: list[tuple[float, float, datetime]]) -> TimelineFeatureCollection:
    return TimelineFeatureCollection(
        type="FeatureCollection",
        features=[
            TimelineFeature(
                type="Feature",
                geometry=PointGeometry(type="Point", coordinates=(lon, lat)),
                properties=TimelineFeatureProperties(timestamp=ts),
            )
            for lon, lat, ts in points
        ],
    )


def test_empty_collection_yields_track_and_no_points() -> None:
    collection = _make_collection([])

    track, points = features_to_orm("empty", "geojson", collection)

    assert track.label == "empty"
    assert track.source_format == "geojson"
    assert points == []


def test_points_preserve_input_order() -> None:
    samples = [
        (-122.4194, 37.7749, datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc)),
        (-73.9857, 40.7484, datetime(2026, 5, 28, 13, 0, tzinfo=timezone.utc)),
        (2.3522, 48.8566, datetime(2026, 5, 28, 14, 0, tzinfo=timezone.utc)),
    ]

    _, points = features_to_orm("trip", "geojson", _make_collection(samples))

    assert [p.observed_at for p in points] == [ts for *_, ts in samples]


def test_geometry_encoded_as_ewkt_srid_4326() -> None:
    samples = [(-122.4194, 37.7749, datetime(2026, 5, 28, tzinfo=timezone.utc))]

    _, points = features_to_orm("sf", "geojson", _make_collection(samples))

    assert points[0].geom == "SRID=4326;POINT(-122.4194 37.7749)"
