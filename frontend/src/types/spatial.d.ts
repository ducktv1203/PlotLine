/**
 * PlotLine custom GeoJSON timeline format — TypeScript wire types.
 *
 * Mirrors `backend/app/schemas/geojson.py`. Any divergence here is a bug:
 * the frontend MUST be able to round-trip whatever the backend validates.
 */

export type Longitude = number;
export type Latitude = number;
export type LonLat = readonly [Longitude, Latitude];

export interface PointGeometry {
  readonly type: "Point";
  readonly coordinates: LonLat;
}

export interface TimelineFeatureProperties {
  /** ISO-8601 UTC timestamp string. */
  readonly timestamp: string;
  readonly label?: string;
  readonly [extra: string]: unknown;
}

export interface TimelineFeature {
  readonly type: "Feature";
  readonly geometry: PointGeometry;
  readonly properties: TimelineFeatureProperties;
}

export interface TimelineFeatureCollection {
  readonly type: "FeatureCollection";
  readonly features: ReadonlyArray<TimelineFeature>;
}
