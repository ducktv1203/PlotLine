"""SQLAlchemy 2 + GeoAlchemy2 ORM placeholders for spatial persistence.

The schema shapes are sketched here (no Alembic migrations, no inserts, no
spatial indexes). PostGIS geometry columns use SRID 4326 (WGS84) so that
ingested GeoJSON requires no reprojection on the write path.
"""
from __future__ import annotations

from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, ForeignKey, String, Table, Column, Integer, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# Association table — a track can belong to multiple cases, and a case
# is just a labelled bag of tracks.
case_tracks = Table(
    "case_tracks",
    Base.metadata,
    Column("case_id", Integer, ForeignKey("cases.id", ondelete="CASCADE"), primary_key=True),
    Column("track_id", Integer, ForeignKey("timeline_tracks.id", ondelete="CASCADE"), primary_key=True),
)


class Case(Base):
    """A named investigation grouping zero or more tracks."""

    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )

    tracks: Mapped[list["TimelineTrack"]] = relationship(
        secondary=case_tracks, backref="cases"
    )


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
