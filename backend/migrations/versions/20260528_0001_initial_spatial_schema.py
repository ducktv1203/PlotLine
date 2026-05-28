"""initial spatial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-28
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostGIS extension MUST exist before any Geometry column is created.
    # IF NOT EXISTS makes the migration idempotent against the postgis/postgis
    # image, which already provisions the extension on first boot.
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    op.create_table(
        "timeline_tracks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("source_format", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_table(
        "timeline_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "track_id",
            sa.Integer(),
            sa.ForeignKey("timeline_tracks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "geom",
            Geometry(geometry_type="POINT", srid=4326),
            nullable=False,
        ),
    )

    # GiST index on geom — required for ST_DWithin / ST_Intersects to use
    # the index instead of falling back to a sequential scan.
    op.create_index(
        "ix_timeline_points_geom",
        "timeline_points",
        ["geom"],
        postgresql_using="gist",
    )

    # B-tree on (track_id, observed_at) — supports time-window queries
    # scoped to a single track, which is the dominant read pattern.
    op.create_index(
        "ix_timeline_points_track_time",
        "timeline_points",
        ["track_id", "observed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_timeline_points_track_time", table_name="timeline_points")
    op.drop_index("ix_timeline_points_geom", table_name="timeline_points")
    op.drop_table("timeline_points")
    op.drop_table("timeline_tracks")
    # Intentionally NOT dropping the postgis extension — other databases on
    # the same cluster may depend on it.
