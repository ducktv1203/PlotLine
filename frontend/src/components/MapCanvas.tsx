import { useEffect, useRef, useState } from "react";

import {
  fetchIntersections,
  fetchTrack,
  type Intersection,
  type TrackResponse,
} from "@/lib/api";
import {
  buildIntersectionLayer,
  buildTrackLayers,
  colorForTrack,
  type Hover,
} from "@/lib/layers";
import { createMap, type MapHandle } from "@/lib/map";

interface MapCanvasProps {
  readonly trackIds: ReadonlyArray<number>;
  /** Epoch ms — when set, scatter layers are filtered to this playhead. */
  readonly playheadMs?: number;
  /** Called with [globalStartMs, globalEndMs] when tracks load. */
  readonly onTracksBounds?: (startMs: number, endMs: number) => void;
}

export default function MapCanvas({
  trackIds,
  playheadMs,
  onTracksBounds,
}: MapCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const handleRef = useRef<MapHandle | null>(null);
  const tracksRef = useRef<Map<number, TrackResponse>>(new Map());
  const intersectionsRef = useRef<ReadonlyArray<Intersection>>([]);
  const [error, setError] = useState<string | null>(null);
  const [hover, setHover] = useState<Hover | null>(null);

  // Mount the map once.
  useEffect(() => {
    if (!containerRef.current) return;
    const handle = createMap({ container: containerRef.current });
    handleRef.current = handle;
    return () => {
      handle.destroy();
      handleRef.current = null;
    };
  }, []);

  const repaint = () => {
    const handle = handleRef.current;
    if (!handle) return;

    const layers = [];
    for (const [id, track] of tracksRef.current) {
      layers.push(
        ...buildTrackLayers(track, {
          trackId: id,
          color: colorForTrack(id),
          playheadMs,
          onHover: setHover,
        }),
      );
    }
    const overlay = buildIntersectionLayer(intersectionsRef.current, setHover);
    if (overlay) layers.push(overlay);

    handle.setLayers(layers);
  };

  // Load tracks whenever the visible-set changes.
  useEffect(() => {
    let cancelled = false;

    const ids = [...trackIds];
    // Drop tracks no longer visible.
    for (const id of [...tracksRef.current.keys()]) {
      if (!ids.includes(id)) tracksRef.current.delete(id);
    }

    Promise.all(ids.map((id) => fetchTrack(id)))
      .then(async (loaded) => {
        if (cancelled) return;
        loaded.forEach((t) => tracksRef.current.set(t.track.id, t));
        setError(null);

        // Recompute global bounds.
        if (loaded.length > 0 && onTracksBounds) {
          const allTs = loaded.flatMap((t) =>
            t.features.map((f) => Date.parse(f.properties.timestamp)),
          );
          if (allTs.length > 0) {
            onTracksBounds(Math.min(...allTs), Math.max(...allTs));
          }
        }

        // Refresh intersections if multiple tracks loaded.
        if (ids.length >= 2) {
          try {
            const res = await fetchIntersections(ids);
            if (!cancelled) intersectionsRef.current = res.intersections;
          } catch {
            // Non-fatal.
          }
        } else {
          intersectionsRef.current = [];
        }

        repaint();

        // Fit camera to the union of visible tracks.
        if (handleRef.current && loaded.length > 0) {
          const lons = loaded.flatMap((t) =>
            t.features.map((f) => f.geometry.coordinates[0]),
          );
          const lats = loaded.flatMap((t) =>
            t.features.map((f) => f.geometry.coordinates[1]),
          );
          if (lons.length > 0 && lats.length > 0) {
            handleRef.current.map.fitBounds(
              [
                [Math.min(...lons), Math.min(...lats)],
                [Math.max(...lons), Math.max(...lats)],
              ],
              { padding: 80, duration: 600 },
            );
          }
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trackIds.join(","), onTracksBounds]);

  // Push playhead changes without re-fetching.
  useEffect(() => {
    repaint();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playheadMs]);

  return (
    <div className="relative h-full w-full">
      <div
        ref={containerRef}
        className="h-full w-full bg-base"
        data-testid="plotline-map"
      />
      {error && (
        <div className="absolute top-3 right-3 rounded-sm border border-tactical-red bg-black/80 px-3 py-2 font-mono text-xs text-tactical-red">
          {error}
        </div>
      )}
      {hover && <HoverTooltip hover={hover} />}
    </div>
  );
}

function HoverTooltip({ hover }: { hover: Hover }) {
  // Offset from cursor so the tooltip never sits under the pointer.
  const style: React.CSSProperties = {
    left: hover.pixelX + 14,
    top: hover.pixelY + 14,
  };

  if (hover.kind === "point") {
    return (
      <div
        className="pointer-events-none absolute z-10 rounded-sm border border-tactical-cyan/60 bg-black/90 px-2 py-1.5 font-mono text-[11px] leading-snug text-tactical-cyan shadow-neon backdrop-blur-sm"
        style={style}
      >
        <div className="text-tactical-cyan/60">
          track #{hover.trackId}
        </div>
        <div>{new Date(hover.timestamp).toISOString().replace("T", " ").slice(0, 19)} UTC</div>
        <div className="text-tactical-cyan/70">
          {hover.lat.toFixed(5)}, {hover.lon.toFixed(5)}
        </div>
      </div>
    );
  }

  // Intersection
  return (
    <div
      className="pointer-events-none absolute z-10 rounded-sm border border-tactical-red/70 bg-black/90 px-2 py-1.5 font-mono text-[11px] leading-snug text-tactical-red shadow-[0_0_8px_rgba(255,0,80,0.4)] backdrop-blur-sm"
      style={style}
    >
      <div className="text-tactical-red/70">
        intersection
      </div>
      <div>
        #{hover.trackA} × #{hover.trackB}
      </div>
      <div className="text-tactical-red/80">
        {hover.distanceM.toFixed(1)} m · Δt {Math.round(hover.deltaS)} s
      </div>
    </div>
  );
}
