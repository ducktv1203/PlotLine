import { useEffect, useRef, useState } from "react";

import { fetchTrack, type TrackResponse } from "@/lib/api";
import { buildTrackLayers } from "@/lib/layers";
import { createMap, type MapHandle } from "@/lib/map";

interface MapCanvasProps {
  /** Track id to fetch and display. If undefined, renders an empty map. */
  readonly trackId?: number;
}

export default function MapCanvas({ trackId }: MapCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const handleRef = useRef<MapHandle | null>(null);
  const [track, setTrack] = useState<TrackResponse | null>(null);
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
      setTrack(null);
      return;
    }
    let cancelled = false;
    fetchTrack(trackId)
      .then((t) => {
        if (!cancelled) {
          setTrack(t);
          setError(null);
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      cancelled = true;
    };
  }, [trackId]);

  // Push layers to the map whenever the loaded track changes.
  useEffect(() => {
    const handle = handleRef.current;
    if (!handle || !track) {
      handle?.setLayers([]);
      return;
    }
    const layers = buildTrackLayers(track, { trackId: track.track.id });
    handle.setLayers(layers);

    // Fly to fit the track's bounds.
    if (track.features.length > 0) {
      const lons = track.features.map((f) => f.geometry.coordinates[0]);
      const lats = track.features.map((f) => f.geometry.coordinates[1]);
      handle.map.fitBounds(
        [
          [Math.min(...lons), Math.min(...lats)],
          [Math.max(...lons), Math.max(...lats)],
        ],
        { padding: 80, duration: 800 },
      );
    }
  }, [track]);

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
