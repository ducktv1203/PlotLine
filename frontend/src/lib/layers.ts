/**
 * Layer factories — turn a TimelineFeatureCollection into deck.gl layers.
 *
 * Two layers per track:
 *   - PathLayer: one polyline through all points (the route)
 *   - ScatterplotLayer: a dot at every observed position (the samples)
 *
 * When `playheadMs` is set the scatter layer uses DataFilterExtension to
 * hide points observed after the playhead. The filter runs on the GPU,
 * so 100k+ points still scrub at frame rate. The path layer is left
 * un-filtered intentionally — the full route is meant to stay visible
 * as a "context" backdrop while the playhead reveals samples.
 */
import { PathLayer, ScatterplotLayer } from "@deck.gl/layers";
import { DataFilterExtension } from "@deck.gl/extensions";
import type { Layer } from "@deck.gl/core";

import type { TimelineFeature, TimelineFeatureCollection } from "@/types/spatial";

export interface BuildTrackLayersOptions {
  readonly trackId: number;
  readonly color?: readonly [number, number, number];
  /** Epoch ms — hide points with timestamp > playheadMs. Omit for no filter. */
  readonly playheadMs?: number;
}

const DEFAULT_TACTICAL_CYAN: readonly [number, number, number] = [0, 240, 255];

type Position = [number, number];

interface PathDatum {
  path: Position[];
}

const timestampFilter = new DataFilterExtension({ filterSize: 1 });

export function buildTrackLayers(
  collection: TimelineFeatureCollection,
  options: BuildTrackLayersOptions,
): Layer[] {
  const color = options.color ?? DEFAULT_TACTICAL_CYAN;
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
    // DataFilterExtension adds `getFilterValue` / `filterRange` props that
    // aren't on ScatterplotLayer's base type signature — we widen the props
    // type here rather than reach for `as any`.
    new ScatterplotLayer<TimelineFeature, { getFilterValue: (f: TimelineFeature) => number; filterRange: [number, number] }>({
      id: `track-${options.trackId}-points`,
      data: [...collection.features],
      getPosition: (f) => [...f.geometry.coordinates] as Position,
      getRadius: 40,
      radiusUnits: "meters",
      getFillColor: [...color, 220],
      stroked: true,
      getLineColor: [...color, 255],
      lineWidthMinPixels: 1,
      getFilterValue: (f: TimelineFeature) =>
        Date.parse(f.properties.timestamp),
      filterRange,
      extensions: [timestampFilter],
    }),
  ];
}
