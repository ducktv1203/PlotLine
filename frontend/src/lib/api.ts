/**
 * Typed fetch wrappers for the PlotLine backend.
 *
 * No runtime schema validation is enforced here yet — the contract is
 * defined in src/types/spatial.d.ts and mirrored by the backend's
 * Pydantic models. If the two ever diverge, integration tests catch it.
 */
import type { TimelineFeatureCollection } from "@/types/spatial";

const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export interface TrackResponse extends TimelineFeatureCollection {
  readonly track: {
    readonly id: number;
    readonly label: string;
    readonly source_format: string;
  };
}

export async function fetchTrack(trackId: number): Promise<TrackResponse> {
  const res = await fetch(`${API_BASE_URL}/tracks/${trackId}`);
  if (!res.ok) {
    throw new Error(`fetchTrack(${trackId}) failed: ${res.status}`);
  }
  return (await res.json()) as TrackResponse;
}

export interface IngestResponse {
  readonly track_id: number;
  readonly point_count: number;
}

export async function ingestGeoJSON(
  label: string,
  collection: TimelineFeatureCollection,
): Promise<IngestResponse> {
  const res = await fetch(
    `${API_BASE_URL}/ingest/geojson?label=${encodeURIComponent(label)}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collection),
    },
  );
  if (!res.ok) {
    throw new Error(`ingestGeoJSON failed: ${res.status}`);
  }
  return (await res.json()) as IngestResponse;
}
