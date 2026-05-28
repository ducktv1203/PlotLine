"""Ingestion service — pure transforms from wire types to ORM rows.

No database access lives here by design: the endpoint layer wraps these
helpers in a session, calls commit, and returns IDs. Keeping the transforms
pure means they can be unit-tested without spinning up Postgres.
"""
from __future__ import annotations

from app.models.spatial import TimelinePoint, TimelineTrack
from app.schemas.geojson import TimelineFeatureCollection


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
