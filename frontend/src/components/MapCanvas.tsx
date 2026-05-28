import { useEffect, useRef } from "react";
import { ScatterplotLayer } from "@deck.gl/layers";

import { createMap, type MapHandle } from "@/lib/map";

const SF_LAT = 37.7749;
const SF_LON = -122.4194;
const TACTICAL_CYAN: [number, number, number] = [0, 240, 255];

const SMOKE_POINTS = [
  { position: [SF_LON, SF_LAT] as [number, number], label: "origin" },
  { position: [SF_LON + 0.01, SF_LAT + 0.01] as [number, number], label: "a" },
  { position: [SF_LON - 0.01, SF_LAT - 0.005] as [number, number], label: "b" },
];

export default function MapCanvas() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const handleRef = useRef<MapHandle | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const handle = createMap({ container: containerRef.current });
    handleRef.current = handle;

    handle.map.once("load", () => {
      handle.setLayers([
        new ScatterplotLayer({
          id: "smoke-points",
          data: SMOKE_POINTS,
          getPosition: (d) => d.position,
          getRadius: 80,
          getFillColor: [...TACTICAL_CYAN, 220],
          radiusUnits: "meters",
          stroked: true,
          getLineColor: [...TACTICAL_CYAN, 255],
          lineWidthMinPixels: 1,
        }),
      ]);
    });

    return () => {
      handle.destroy();
      handleRef.current = null;
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="h-full w-full bg-base"
      data-testid="plotline-map"
    />
  );
}
