"""SQLAlchemy 2 + GeoAlchemy2 ORM placeholders for spatial persistence.

The schema shapes are sketched here (no Alembic migrations, no inserts, no
spatial indexes). PostGIS geometry columns use SRID 4326 (WGS84) so that
ingested GeoJSON requires no reprojection on the write path.
"""
from __future__ import annotations

from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimelineTrack(Base):
    """A single ingested chronological footprint set (one upload = one track)."""

    __tablename__ = "timeline_tracks"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(255))
    source_format: Mapped[str] = mapped_column(String(32))  # "csv" | "geojson"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )


class TimelinePoint(Base):
    """A single (timestamped, geolocated) sample belonging to a track."""

    __tablename__ = "timeline_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("timeline_tracks.id"))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    geom: Mapped[str] = mapped_column(Geometry(geometry_type="POINT", srid=4326))
