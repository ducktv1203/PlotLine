"""Build PlotLine demo GeoJSON files from NOAA HURDAT2.

HURDAT2 is the canonical, public, plain-text record of every Atlantic
hurricane since 1851 — six-hourly position fixes plus extra fixes around
landfall. Real timestamps, real curving tracks, no synthetic data.

Run from the repo root:
    python backend/scripts/build_hurricane_demos.py

Reads:
    https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2023-051124.txt
Writes:
    frontend/public/demo/<storm-slug>.geojson    (one per storm)
    frontend/public/demo/index.json              (manifest)
"""
from __future__ import annotations

import json
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

HURDAT2_URL = (
    "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2023-051124.txt"
)

# (HURDAT2 storm id, display label, slug)
TARGETS: list[tuple[str, str, str]] = [
    ("AL122005", "Hurricane Katrina (2005)", "katrina-2005"),
    ("AL182012", "Hurricane Sandy (2012)", "sandy-2012"),
    ("AL092017", "Hurricane Harvey (2017)", "harvey-2017"),
    ("AL112017", "Hurricane Irma (2017)", "irma-2017"),
    ("AL152017", "Hurricane Maria (2017)", "maria-2017"),
    ("AL092021", "Hurricane Ida (2021)", "ida-2021"),
    ("AL092022", "Hurricane Ian (2022)", "ian-2022"),
]


@dataclass
class Observation:
    timestamp: datetime
    lat: float
    lon: float
    status: str
    max_wind_kt: int


def _parse_coord(token: str) -> float:
    """Convert '28.0N' -> 28.0,  '94.8W' -> -94.8."""
    hemi = token[-1]
    value = float(token[:-1])
    if hemi in ("S", "W"):
        value = -value
    return value


def _parse_hurdat2(text: str) -> dict[str, tuple[str, list[Observation]]]:
    """Return {storm_id: (name, [observations])}."""
    storms: dict[str, tuple[str, list[Observation]]] = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        # Header row: "AL011851, UNNAMED, 14,"
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3 and parts[0].startswith(("AL", "EP", "CP")):
            storm_id = parts[0]
            name = parts[1]
            try:
                n = int(parts[2])
            except ValueError:
                i += 1
                continue
            obs: list[Observation] = []
            for j in range(1, n + 1):
                row = [c.strip() for c in lines[i + j].split(",")]
                date = row[0]
                hhmm = row[1]
                status = row[3]
                lat = _parse_coord(row[4])
                lon = _parse_coord(row[5])
                wind = int(row[6])
                ts = datetime(
                    int(date[0:4]),
                    int(date[4:6]),
                    int(date[6:8]),
                    int(hhmm[0:2]),
                    int(hhmm[2:4]),
                    tzinfo=timezone.utc,
                )
                obs.append(Observation(ts, lat, lon, status, wind))
            storms[storm_id] = (name, obs)
            i += n + 1
        else:
            i += 1
    return storms


def _observations_to_feature_collection(
    label: str, observations: list[Observation]
) -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [obs.lon, obs.lat],
                },
                "properties": {
                    "timestamp": obs.timestamp.isoformat(),
                    "status": obs.status,
                    "max_wind_kt": obs.max_wind_kt,
                    "label": label,
                },
            }
            for obs in observations
        ],
    }


def main() -> int:
    print(f"Fetching HURDAT2 from {HURDAT2_URL} ...")
    with urllib.request.urlopen(HURDAT2_URL) as resp:
        text = resp.read().decode("utf-8")
    print(f"Got {len(text):,} bytes — parsing ...")

    storms = _parse_hurdat2(text)
    print(f"Parsed {len(storms)} storms.")

    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "frontend" / "public" / "demo"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Preserve other categories that may already be in the manifest.
    manifest_path = out_dir / "index.json"
    existing: list[dict[str, str | int]] = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else []
    )

    new_entries: list[dict[str, str | int]] = []
    for storm_id, label, slug in TARGETS:
        if storm_id not in storms:
            print(f"  ! missing {storm_id} ({label}) — skipping")
            continue
        _, observations = storms[storm_id]
        fc = _observations_to_feature_collection(label, observations)
        out_path = out_dir / f"{slug}.geojson"
        out_path.write_text(json.dumps(fc, indent=2), encoding="utf-8")
        new_entries.append(
            {
                "file": f"{slug}.geojson",
                "label": label,
                "points": len(observations),
                "category": "Atlantic Hurricane Reference",
            }
        )
        print(f"  wrote {out_path.name}  ({len(observations)} observations)")

    keep = [e for e in existing if e["file"] not in {n["file"] for n in new_entries}]
    manifest_path.write_text(
        json.dumps(keep + new_entries, indent=2), encoding="utf-8"
    )
    print(f"\nDone. Manifest now has {len(keep) + len(new_entries)} entries.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
