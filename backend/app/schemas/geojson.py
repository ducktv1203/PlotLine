"""Pydantic v2 wire models for the PlotLine custom GeoJSON timeline format.

The shape extends standard GeoJSON Feature/FeatureCollection with a required
`timestamp` (ISO-8601, UTC) on each feature's properties. Geometries are
restricted to Point for the initial timeline format.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PointGeometry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Point"]
    coordinates: tuple[float, float]  # (lon, lat) per GeoJSON RFC 7946


class TimelineFeatureProperties(BaseModel):
    model_config = ConfigDict(extra="allow")

    timestamp: datetime
    label: str | None = None


class TimelineFeature(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Feature"]
    geometry: PointGeometry
    properties: TimelineFeatureProperties


class TimelineFeatureCollection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["FeatureCollection"]
    features: list[TimelineFeature] = Field(default_factory=list)
