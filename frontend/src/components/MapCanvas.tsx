import { useEffect, useRef, useState } from "react";

import { fetchTrack, type TrackResponse } from "@/lib/api";
import { buildTrackLayers } from "@/lib/layers";
import { createMap, type MapHandle } from "@/lib/map";

interface MapCanvasProps {
  readonly trackId?: number;
  /** Epoch ms — when set, the scatter layer is filtered to this playhead. */
  readonly playheadMs?: number;
  /** Called once with [startMs, endMs] when a track loads. */
  readonly onTrackBounds?: (startMs: number, endMs: number) => void;
}

export default function MapCanvas({
  trackId,
  playheadMs,
  onTrackBounds,
}: MapCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const handleRef = useRef<MapHandle | null>(null);
  const trackRef = useRef<TrackResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  // Load the track when the id changes.
  useEffect(() => {
    if (trackId === undefined) {
      trackRef.current = null;
      handleRef.current?.setLayers([]);
      return;
    }
    let cancelled = false;
    fetchTrack(trackId)
      .then((t) => {
        if (cancelled) return;
        trackRef.current = t;
        setError(null);

        if (t.features.length > 0 && onTrackBounds) {
          const tss = t.features.map((f) =>
            Date.parse(f.properties.timestamp),
          );
          onTrackBounds(Math.min(...tss), Math.max(...tss));
        }

        // Initial render.
        handleRef.current?.setLayers(
          buildTrackLayers(t, { trackId: t.track.id, playheadMs }),
        );

        // Fly to fit bounds.
        if (t.features.length > 0 && handleRef.current) {
          const lons = t.features.map((f) => f.geometry.coordinates[0]);
          const lats = t.features.map((f) => f.geometry.coordinates[1]);
          handleRef.current.map.fitBounds(
            [
              [Math.min(...lons), Math.min(...lats)],
              [Math.max(...lons), Math.max(...lats)],
            ],
            { padding: 80, duration: 800 },
          );
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      cancelled = true;
    };
    // playheadMs intentionally excluded: it's pushed via the next effect.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [trackId, onTrackBounds]);

  // Push playhead updates without rebuilding the whole effect chain.
  useEffect(() => {
    const handle = handleRef.current;
    const track = trackRef.current;
    if (!handle || !track) return;
    handle.setLayers(
      buildTrackLayers(track, { trackId: track.track.id, playheadMs }),
    );
  }, [playheadMs]);

  return (
    <div className="relative h-full w-full">
      <div
        ref={containerRef}
        className="h-full w-full bg-base"
        data-testid="plotline-map"
      />
      {error && (
        <div className="absolute top-3 left-3 rounded-sm border border-tactical-red bg-black/80 px-3 py-2 font-mono text-xs text-tactical-red">
          {error}
        </div>
      )}
    </div>
  );
}
