"""Ingestion service — pure transforms from wire types to ORM rows.

No database access lives here by design: the endpoint layer wraps these
helpers in a session, calls commit, and returns IDs. Keeping the transforms
pure means they can be unit-tested without spinning up Postgres.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import NamedTuple

from app.models.spatial import TimelinePoint, TimelineTrack
from app.schemas.geojson import (
    PointGeometry,
    TimelineFeature,
    TimelineFeatureCollection,
    TimelineFeatureProperties,
)


class CsvColumnMap(NamedTuple):
    """Names of the source CSV columns that hold the three required fields."""

    timestamp_col: str
    lat_col: str
    lon_col: str


def features_to_orm(
    label: str,
    source_format: str,
    collection: TimelineFeatureCollection,
) -> tuple[TimelineTrack, list[TimelinePoint]]:
    """Build a (track, points) pair from a validated feature collection.

    The track has no `id` yet — the caller must `session.add(track)` then
    `session.flush()` before persisting points, because each point needs the
    parent's primary key as its FK.

    Geometry is encoded as an EWKT string ("SRID=4326;POINT(lon lat)") which
    GeoAlchemy2 transparently parses into a PostGIS geometry on insert.
    """
    track = TimelineTrack(label=label, source_format=source_format)

    points = [
        TimelinePoint(
            observed_at=feature.properties.timestamp,
            geom=(
                f"SRID=4326;POINT("
                f"{feature.geometry.coordinates[0]} "
                f"{feature.geometry.coordinates[1]})"
            ),
        )
        for feature in collection.features
    ]

    return track, points


def csv_to_collection(
    raw: str, column_map: CsvColumnMap
) -> TimelineFeatureCollection:
    """Parse CSV text into a TimelineFeatureCollection.

    The column map is required (no auto-detection) — silent guessing tends
    to produce confidently-wrong ingests. Timestamps must be ISO-8601;
    anything `datetime.fromisoformat` accepts is fine.
    """
    reader = csv.DictReader(io.StringIO(raw))

    features: list[TimelineFeature] = []
    for row in reader:
        ts_raw = row.get(column_map.timestamp_col)
        lat_raw = row.get(column_map.lat_col)
        lon_raw = row.get(column_map.lon_col)
        if ts_raw is None or lat_raw is None or lon_raw is None:
            raise ValueError(
                f"row missing required column "
                f"(timestamp={column_map.timestamp_col}, "
                f"lat={column_map.lat_col}, lon={column_map.lon_col}): {row}"
            )

        features.append(
            TimelineFeature(
                type="Feature",
                geometry=PointGeometry(
                    type="Point",
                    coordinates=(float(lon_raw), float(lat_raw)),
                ),
                properties=TimelineFeatureProperties(
                    timestamp=datetime.fromisoformat(ts_raw),
                ),
            )
        )

    return TimelineFeatureCollection(type="FeatureCollection", features=features)
