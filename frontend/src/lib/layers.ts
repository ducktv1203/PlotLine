/**
 * Layer factories — turn a TimelineFeatureCollection into deck.gl layers.
 *
 * Two layers per track:
 *   - PathLayer: one polyline through all points (the route)
 *   - ScatterplotLayer: a dot at every observed position (the samples)
 *
 * Keeping the transform isolated here means the timeline scrubber phase
 * can wire a DataFilterExtension by extending the same factory rather
 * than rewriting MapCanvas.
 */
import { PathLayer, ScatterplotLayer } from "@deck.gl/layers";
import type { Layer } from "@deck.gl/core";

import type { TimelineFeature, TimelineFeatureCollection } from "@/types/spatial";

export interface BuildTrackLayersOptions {
  readonly trackId: number;
  readonly color?: readonly [number, number, number];
}

const DEFAULT_TACTICAL_CYAN: readonly [number, number, number] = [0, 240, 255];

type Position = [number, number];

interface PathDatum {
  path: Position[];
}

export function buildTrackLayers(
  collection: TimelineFeatureCollection,
  options: BuildTrackLayersOptions,
): Layer[] {
  const color = options.color ?? DEFAULT_TACTICAL_CYAN;
  const path: Position[] = collection.features.map(
    (f) => [...f.geometry.coordinates] as Position,
  );

  if (path.length === 0) return [];

  return [
    new PathLayer<PathDatum>({
      id: `track-${options.trackId}-path`,
      data: [{ path }],
      getPath: (d) => d.path,
      getColor: [...color, 200],
      getWidth: 3,
      widthMinPixels: 2,
    }),
    new ScatterplotLayer<TimelineFeature>({
      id: `track-${options.trackId}-points`,
      data: [...collection.features],
      getPosition: (f) => [...f.geometry.coordinates] as Position,
      getRadius: 40,
      radiusUnits: "meters",
      getFillColor: [...color, 220],
      stroked: true,
      getLineColor: [...color, 255],
      lineWidthMinPixels: 1,
    }),
  ];
}
