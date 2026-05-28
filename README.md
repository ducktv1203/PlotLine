# PlotLine

> **Cinematic Geospatial OSINT Sandbox** — an interactive, browser-based situation-room engine that ingests chronological location footprints and projects them onto a hardware-accelerated, scrubable map.

PlotLine is an empty sandbox engine: it takes unstructured CSV or custom GeoJSON timelines and reconstructs paths, intersections, and spatiotemporal events inside a tactical-intelligence aesthetic (pitch-black canvas, monospace type, high-contrast neon accents).

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

## Project Status

Phase 0 — **Scaffolding complete**. Application logic (parsers, shaders, render trees, migrations) is intentionally not yet implemented.
