/**
 * Layer factories — turn a TimelineFeatureCollection into deck.gl layers.
 *
 * `buildTrackLayers` produces the path + scatter pair for ONE track.
 * `buildIntersectionLayer` produces an overlay for space-time hits across
 *   multiple tracks. Both are pure functions so MapCanvas only re-renders
 *   layers when its inputs change.
 *
 * When `playheadMs` is set the scatter layer is filtered on the GPU via
 * DataFilterExtension. The path stays as a dim trail for context.
 */
import { PathLayer, ScatterplotLayer } from "@deck.gl/layers";
import { DataFilterExtension } from "@deck.gl/extensions";
import type { Layer } from "@deck.gl/core";

import type { Intersection } from "@/lib/api";
import type { TimelineFeature, TimelineFeatureCollection } from "@/types/spatial";

export type RGB = readonly [number, number, number];

/** Palette for distinct tracks — first N tracks pick from here in order. */
export const TRACK_PALETTE: ReadonlyArray<RGB> = [
  [0, 240, 255], //  cyan
  [255, 176, 0], //  amber
  [57, 255, 20], //  tactical-green
  [255, 0, 80], //   tactical-pink
  [180, 110, 255], // violet
  [255, 255, 255], // white
];

export function colorForTrack(trackId: number): RGB {
  return TRACK_PALETTE[trackId % TRACK_PALETTE.length]!;
}

export interface PointHover {
  readonly kind: "point";
  readonly trackId: number;
  readonly timestamp: string;
  readonly lon: number;
  readonly lat: number;
  readonly pixelX: number;
  readonly pixelY: number;
}

export interface IntersectionHover {
  readonly kind: "intersection";
  readonly trackA: number;
  readonly trackB: number;
  readonly tA: string;
  readonly tB: string;
  readonly distanceM: number;
  readonly deltaS: number;
  readonly pixelX: number;
  readonly pixelY: number;
}

export type Hover = PointHover | IntersectionHover;

export interface BuildTrackLayersOptions {
  readonly trackId: number;
  readonly color?: RGB;
  /** Epoch ms — hide points with timestamp > playheadMs. Omit for no filter. */
  readonly playheadMs?: number;
  readonly onHover?: (hover: Hover | null) => void;
}

type Position = [number, number];

interface PathDatum {
  path: Position[];
}

const timestampFilter = new DataFilterExtension({ filterSize: 1 });

export function buildTrackLayers(
  collection: TimelineFeatureCollection,
  options: BuildTrackLayersOptions,
): Layer[] {
  const color = options.color ?? colorForTrack(options.trackId);
  const path: Position[] = collection.features.map(
    (f) => [...f.geometry.coordinates] as Position,
  );

  if (path.length === 0) return [];

  const filteringActive = options.playheadMs !== undefined;
  const filterRange: [number, number] = filteringActive
    ? [0, options.playheadMs!]
    : [0, Number.MAX_SAFE_INTEGER];

  return [
    new PathLayer<PathDatum>({
      id: `track-${options.trackId}-path`,
      data: [{ path }],
      getPath: (d) => d.path,
      getColor: [...color, filteringActive ? 80 : 200],
      getWidth: 3,
      widthMinPixels: 2,
    }),
    new ScatterplotLayer<TimelineFeature, { getFilterValue: (f: TimelineFeature) => number; filterRange: [number, number] }>({
      id: `track-${options.trackId}-points`,
      data: [...collection.features],
      getPosition: (f) => [...f.geometry.coordinates] as Position,
      getRadius: 4,
      radiusUnits: "pixels",
      radiusMinPixels: 3,
      radiusMaxPixels: 8,
      getFillColor: [...color, 220],
      stroked: true,
      getLineColor: [...color, 255],
      lineWidthMinPixels: 1,
      pickable: true,
      onHover: (info) => {
        if (!options.onHover) return;
        const f = info.object as TimelineFeature | undefined;
        if (f) {
          options.onHover({
            kind: "point",
            trackId: options.trackId,
            timestamp: f.properties.timestamp,
            lon: f.geometry.coordinates[0],
            lat: f.geometry.coordinates[1],
            pixelX: info.x,
            pixelY: info.y,
          });
        } else {
          options.onHover(null);
        }
      },
      getFilterValue: (f: TimelineFeature) =>
        Date.parse(f.properties.timestamp),
      filterRange,
      extensions: [timestampFilter],
    }),
  ];
}

const INTERSECTION_RED: RGB = [255, 0, 80];

export function buildIntersectionLayer(
  intersections: ReadonlyArray<Intersection>,
  onHover?: (hover: Hover | null) => void,
): Layer | null {
  if (intersections.length === 0) return null;

  return new ScatterplotLayer<Intersection>({
    id: "intersections",
    data: [...intersections],
    getPosition: (d) => [d.lon, d.lat] as Position,
    // Pixel-scaled so the markers stay readable regardless of zoom and
    // don't bloom into a single blob when many cluster together.
    getRadius: 6,
    radiusUnits: "pixels",
    getFillColor: [...INTERSECTION_RED, 30],
    stroked: true,
    getLineColor: [...INTERSECTION_RED, 220],
    lineWidthMinPixels: 1.5,
    pickable: true,
    onHover: (info) => {
      if (!onHover) return;
      const d = info.object as Intersection | undefined;
      if (d) {
        onHover({
          kind: "intersection",
          trackA: d.track_a,
          trackB: d.track_b,
          tA: d.t_a,
          tB: d.t_b,
          distanceM: d.distance_m,
          deltaS: d.delta_s,
          pixelX: info.x,
          pixelY: info.y,
        });
      } else {
        onHover(null);
      }
    },
  });
}
