"""Build PlotLine demo GeoJSON files from USGS earthquake catalog.

USGS exposes the entire global earthquake catalog as native GeoJSON via
the FDSN-style query API. We fetch a handful of famous earthquake
sequences and convert each into a PlotLine TimelineFeatureCollection
(timestamp + lon/lat + magnitude in properties).

Each sequence becomes ONE PlotLine "track" — the foreshocks and
aftershocks of a single event, ordered chronologically. That maps well
to PlotLine's existing rendering: a path of dots through time, with
the playhead revealing the seismic sequence as it unfolded.

Run from the repo root:
    python backend/scripts/build_quake_demos.py
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USGS_BASE = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# (slug, label, query params)
# We deliberately fetch a tight bbox + small time window around each event so
# the resulting track is the aftershock sequence, not random global noise.
SEQUENCES: list[tuple[str, str, dict[str, str]]] = [
    (
        "turkey-syria-2023",
        "2023 Turkey-Syria Earthquake Sequence",
        {
            "starttime": "2023-02-06",
            "endtime": "2023-02-15",
            "minmagnitude": "4.0",
            "minlatitude": "35",
            "maxlatitude": "39",
            "minlongitude": "35",
            "maxlongitude": "39",
        },
    ),
    (
        "tohoku-2011",
        "2011 Tohoku Earthquake Sequence",
        {
            "starttime": "2011-03-11",
            "endtime": "2011-03-18",
            "minmagnitude": "5.0",
            "minlatitude": "35",
            "maxlatitude": "42",
            "minlongitude": "139",
            "maxlongitude": "146",
        },
    ),
    (
        "ridgecrest-2019",
        "2019 Ridgecrest Earthquake Sequence",
        {
            "starttime": "2019-07-04",
            "endtime": "2019-07-08",
            "minmagnitude": "3.5",
            "minlatitude": "35.3",
            "maxlatitude": "36.3",
            "minlongitude": "-118",
            "maxlongitude": "-117",
        },
    ),
]


def _fetch_geojson(params: dict[str, str]) -> dict:
    qs = urllib.parse.urlencode({**params, "format": "geojson"})
    url = f"{USGS_BASE}?{qs}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _usgs_to_plotline(label: str, usgs: dict) -> dict:
    features = []
    for raw in usgs.get("features", []):
        props = raw.get("properties", {})
        geom = raw.get("geometry") or {}
        coords = geom.get("coordinates") or []
        if geom.get("type") != "Point" or len(coords) < 2:
            continue
        # USGS time is epoch ms; convert to ISO 8601 UTC.
        epoch_ms = props.get("time")
        if epoch_ms is None:
            continue
        ts = datetime.fromtimestamp(epoch_ms / 1000.0, tz=timezone.utc)
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(coords[0]), float(coords[1])],
                },
                "properties": {
                    "timestamp": ts.isoformat(),
                    "label": label,
                    "magnitude": props.get("mag"),
                    "place": props.get("place"),
                    "depth_km": float(coords[2]) if len(coords) >= 3 else None,
                },
            }
        )
    # USGS returns most-recent first; PlotLine expects chronological order.
    features.sort(key=lambda f: f["properties"]["timestamp"])
    return {"type": "FeatureCollection", "features": features}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "frontend" / "public" / "demo"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load existing manifest if present so we extend it rather than replace.
    manifest_path = out_dir / "index.json"
    existing: list[dict[str, str | int]] = []
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))

    new_entries: list[dict[str, str | int]] = []
    for slug, label, params in SEQUENCES:
        print(f"Fetching {label} from USGS ...")
        usgs = _fetch_geojson(params)
        fc = _usgs_to_plotline(label, usgs)
        count = len(fc["features"])
        if count == 0:
            print(f"  ! no events returned for {label} — skipping")
            continue
        out_path = out_dir / f"{slug}.geojson"
        out_path.write_text(json.dumps(fc, indent=2), encoding="utf-8")
        new_entries.append(
            {
                "file": f"{slug}.geojson",
                "label": label,
                "points": count,
                "category": "Major Earthquake Sequences",
            }
        )
        print(f"  wrote {out_path.name}  ({count} events)")

    # De-duplicate: any existing entry with the same file is overwritten.
    keep_existing = [e for e in existing if e["file"] not in {n["file"] for n in new_entries}]
    manifest_path.write_text(
        json.dumps(keep_existing + new_entries, indent=2), encoding="utf-8"
    )
    print(f"\nDone. Manifest now has {len(keep_existing) + len(new_entries)} entries.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
