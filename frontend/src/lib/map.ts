/**
 * Map factory — constructs a Maplibre instance with a Deck.gl overlay
 * sharing the same WebGL context.
 *
 * Critical detail: we use MapboxOverlay (interleaved/overlaid into Maplibre)
 * rather than the standalone <DeckGL> React component. The standalone path
 * creates its own canvas and stacks it over Maplibre's, which breaks picking
 * and burns a second GL context.
 */
import {
  Map as MaplibreMap,
  type IControl,
  type StyleSpecification,
} from "maplibre-gl";
import { MapboxOverlay } from "@deck.gl/mapbox";
import type { Layer } from "@deck.gl/core";

import "maplibre-gl/dist/maplibre-gl.css";

export interface MapHandle {
  readonly map: MaplibreMap;
  readonly overlay: MapboxOverlay;
  setLayers(layers: Layer[]): void;
  destroy(): void;
}

export interface CreateMapOptions {
  container: HTMLElement;
  style?: string | StyleSpecification;
  center?: [number, number];
  zoom?: number;
}

const DEFAULT_DARK_STYLE =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

export function createMap(opts: CreateMapOptions): MapHandle {
  const map = new MaplibreMap({
    container: opts.container,
    style: opts.style ?? DEFAULT_DARK_STYLE,
    center: opts.center ?? [-122.4194, 37.7749],
    zoom: opts.zoom ?? 11,
    attributionControl: { compact: true },
  });

  const overlay = new MapboxOverlay({ interleaved: true, layers: [] });
  map.addControl(overlay as unknown as IControl);

  return {
    map,
    overlay,
    setLayers(layers) {
      overlay.setProps({ layers });
    },
    destroy() {
      overlay.finalize();
      map.remove();
    },
  };
}
