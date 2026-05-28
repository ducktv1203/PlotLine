"""Build PlotLine demo GeoJSON files from real OpenStreetMap public GPS uploads.

The OSM trackpoints API returns anonymized, real-world human GPS traces
that contributors uploaded — actual people walking, cycling, or driving
through cities, with the natural GPS jitter and irregular sampling that
synthetic data can never reproduce. This is the canonical "OSINT-style"
demo data: real movement, real timestamps, no synthesis.

Per OSM API: only the bbox-bounded trackpoints endpoint works
anonymously. We fetch several cities' worth, group the response by
<trk> element (each trace == one PlotLine track), and emit the
longest ones.

Run from the repo root:
    python backend/scripts/build_human_traces.py
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# defusedxml hardens against XXE / billion-laughs attacks. Same API as the
# stdlib xml.etree.ElementTree, safer default for any script that may one
# day point at an untrusted source.
import defusedxml.ElementTree as ET

OSM_ENDPOINT = "https://api.openstreetmap.org/api/0.6/trackpoints"
GPX_NS = {"gpx": "http://www.topografix.com/GPX/1/0"}

# Each city: (slug-prefix, label, bbox tuple (min_lon, min_lat, max_lon, max_lat))
CITIES: list[tuple[str, str, tuple[float, float, float, float]]] = [
    ("sf", "San Francisco Mission", (-122.435, 37.745, -122.405, 37.775)),
    ("nyc", "New York Midtown", (-74.005, 40.745, -73.975, 40.770)),
    ("london", "London Westminster", (-0.145, 51.490, -0.115, 51.515)),
    ("tokyo", "Tokyo Shibuya", (139.690, 35.650, 139.715, 35.675)),
]

MIN_POINTS = 25     # filter out tiny fragments
MAX_PER_CITY = 4    # cap traces per city so the demo is curated, not noisy
TRACES_PER_PAGE_LIMIT = 5000


def _fetch_gpx(bbox: tuple[float, float, float, float]) -> str:
    qs = urllib.parse.urlencode(
        {"bbox": ",".join(str(b) for b in bbox), "page": 0}
    )
    req = urllib.request.Request(
        f"{OSM_ENDPOINT}?{qs}",
        headers={"User-Agent": "PlotLine-Demo/0.1 (educational use)"},
    )
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8")


def _gpx_to_traces(gpx_text: str) -> list[list[dict]]:
    """Return one list of feature-dicts per <trk> with enough timestamped points."""
    root = ET.fromstring(gpx_text)
    traces: list[list[dict]] = []
    for trk in root.findall("gpx:trk", GPX_NS):
        points: list[dict] = []
        for trkpt in trk.iter("{http://www.topografix.com/GPX/1/0}trkpt"):
            lat = trkpt.get("lat")
            lon = trkpt.get("lon")
            time_el = trkpt.find("gpx:time", GPX_NS)
            if lat is None or lon is None or time_el is None or not time_el.text:
                continue
            points.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(lon), float(lat)],
                    },
                    "properties": {
                        "timestamp": time_el.text,
                    },
                }
            )
        if len(points) >= MIN_POINTS:
            # GPX is already chronological; keep that order.
            traces.append(points)
    return traces


def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _trace_label(city_label: str, idx: int, points: list[dict]) -> str:
    start = points[0]["properties"]["timestamp"][:10]  # YYYY-MM-DD
    return f"{city_label} — anonymous trace {idx + 1} ({start})"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "frontend" / "public" / "demo"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = out_dir / "index.json"
    existing: list[dict[str, str | int]] = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else []
    )

    new_entries: list[dict[str, str | int]] = []
    for slug_prefix, city_label, bbox in CITIES:
        print(f"Fetching {city_label} ...")
        try:
            gpx = _fetch_gpx(bbox)
        except Exception as exc:
            print(f"  ! fetch failed: {exc}")
            continue
        traces = _gpx_to_traces(gpx)
        traces.sort(key=len, reverse=True)
        traces = traces[:MAX_PER_CITY]
        for idx, points in enumerate(traces):
            label = _trace_label(city_label, idx, points)
            slug = f"{slug_prefix}-trace-{idx + 1}"
            fc = {"type": "FeatureCollection", "features": points}
            (out_dir / f"{slug}.geojson").write_text(
                json.dumps(fc, indent=2), encoding="utf-8"
            )
            new_entries.append(
                {
                    "file": f"{slug}.geojson",
                    "label": label,
                    "points": len(points),
                    "category": "Public Human GPS Traces (OSM contributors)",
                }
            )
            print(f"  wrote {slug}.geojson  ({len(points)} pts)")

    # Replace any prior Public Human GPS entries; leave other categories alone.
    cleaned = [
        e
        for e in existing
        if e.get("category") != "Public Human GPS Traces (OSM contributors)"
    ]
    manifest_path.write_text(
        json.dumps(cleaned + new_entries, indent=2), encoding="utf-8"
    )
    print(
        f"\nDone. {len(new_entries)} new traces written. "
        f"Manifest now has {len(cleaned) + len(new_entries)} entries."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
