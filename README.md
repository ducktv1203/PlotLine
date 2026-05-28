# PlotLine

> A geospatial OSINT tool for reconstructing movement from location data.

PlotLine ingests chronological location footprints (CSV or GeoJSON timelines) and projects them onto an interactive, GPU-accelerated map — letting you scrub through time, trace paths, and surface spatiotemporal intersections.

---

## Architecture

```
plotline/
├── backend/    FastAPI + PostGIS spatial ingestion & query layer
└── frontend/   Vite + React + Maplibre GL + Deck.gl rendering surface
```

| Layer       | Stack                                                                 |
|-------------|-----------------------------------------------------------------------|
| Render      | Maplibre GL JS v4 + Deck.gl v9 (WebGL overlay)                        |
| UI          | React 19, Tailwind v3/v4, Shadcn primitives, Lucide icons, JetBrains Mono |
| API         | FastAPI (Python 3.11+) + Uvicorn                                      |
| Storage     | PostgreSQL 16 + PostGIS                                               |
| Validation  | Pydantic v2 (wire) / SQLAlchemy 2 + GeoAlchemy2 (persistence)         |
| Geospatial  | Shapely 2, PyProj (fallback computation)                              |

---

## Quickstart

### Prerequisites

- **Node.js** LTS (v20+)
- **Python** 3.11+
- **PostgreSQL** 16 with the `postgis` extension installed
- (Optional) **Docker** for the dev DB

### 1. Clone & configure environment

```bash
cp .env.example .env
# edit .env with your local Postgres credentials
```

### 2. Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend will be live at `http://localhost:8000` — interactive docs at `http://localhost:8000/docs`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be live at `http://localhost:5173`.

---

## Usage

### Ingest a track

```bash
# GeoJSON
curl -X POST 'http://localhost:8000/api/v1/ingest/geojson?label=my-trip' \
  -H 'Content-Type: application/json' \
  -d @track.geojson

# CSV (override column names if not "timestamp,lat,lon")
curl -X POST 'http://localhost:8000/api/v1/ingest/csv?label=my-trip' \
  -F 'file=@track.csv'
```

Or drag a `.geojson` file onto the map in the browser — same path.

### Controls

| Key      | Action                          |
|----------|---------------------------------|
| `d`      | Load the bundled demo track     |
| `space`  | Play / pause the timeline       |
| `[` / `]`| Step the playhead ±1 minute     |
| `r`      | Reset the playhead to the start |

Toggle the checkboxes in the top-left **TRACKS** panel to show multiple tracks at once. When two or more tracks are visible, space-time intersections (within 50m and 5min of each other by default) are highlighted as red markers.

### REST surface

| Method | Path                                                | Purpose                                              |
|--------|-----------------------------------------------------|------------------------------------------------------|
| POST   | `/api/v1/ingest/geojson`                            | Ingest a GeoJSON FeatureCollection                   |
| POST   | `/api/v1/ingest/csv`                                | Ingest a CSV file with explicit column mapping       |
| GET    | `/api/v1/tracks`                                    | List ingested tracks (id, label, source)             |
| GET    | `/api/v1/tracks/{id}`                               | Fetch full track as a FeatureCollection              |
| GET    | `/api/v1/tracks/{id}/window?start=&end=`            | Time-windowed slice of a track                       |
| GET    | `/api/v1/spatial/intersections?track_ids=...&...`   | Space-time intersections across visible tracks       |

Interactive docs at `http://localhost:8000/docs`.

## Project Status

End-to-end working: ingest → store → query → render → scrub → multi-track intersect.
