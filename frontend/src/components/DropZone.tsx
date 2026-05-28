import { useEffect, useState } from "react";

import { ingestGeoJSON } from "@/lib/api";

interface DropZoneProps {
  /** Called after a successful ingest so the parent can refresh the list. */
  readonly onIngested?: (trackId: number) => void;
}

/**
 * Invisible drop target covering the map. Lights up only while a file is
 * being dragged over the window — otherwise it doesn't intercept clicks.
 *
 * Only GeoJSON is supported via drag-drop in this iteration; CSV ingest
 * remains an explicit endpoint (column mapping isn't sensible to guess).
 */
export default function DropZone({ onIngested }: DropZoneProps) {
  const [active, setActive] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    const onWindowDragEnter = (e: DragEvent) => {
      if (e.dataTransfer?.types.includes("Files")) setActive(true);
    };
    const onWindowDragLeave = (e: DragEvent) => {
      if (e.relatedTarget === null) setActive(false);
    };
    window.addEventListener("dragenter", onWindowDragEnter);
    window.addEventListener("dragleave", onWindowDragLeave);
    return () => {
      window.removeEventListener("dragenter", onWindowDragEnter);
      window.removeEventListener("dragleave", onWindowDragLeave);
    };
  }, []);

  const onDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setActive(false);

    const file = e.dataTransfer.files[0];
    if (!file) return;

    setStatus(`reading ${file.name}...`);
    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
      const result = await ingestGeoJSON(
        file.name.replace(/\.geo(json)?$/i, ""),
        parsed,
      );
      setStatus(
        `ingested track #${result.track_id} (${result.point_count} points)`,
      );
      onIngested?.(result.track_id);
      setTimeout(() => setStatus(null), 3000);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setStatus(`ingest failed: ${msg}`);
    }
  };

  return (
    <>
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={onDrop}
        className={`pointer-events-${active ? "auto" : "none"} absolute inset-0 z-20 grid place-items-center transition-opacity ${
          active
            ? "border-2 border-dashed border-tactical-cyan bg-base/70 opacity-100"
            : "opacity-0"
        }`}
      >
        <div className="rounded-sm border border-tactical-cyan/60 bg-base px-6 py-3 font-mono text-sm uppercase tracking-[0.2em] text-tactical-cyan shadow-neon">
          // drop geojson to ingest
        </div>
      </div>
      {status && (
        <div className="pointer-events-none absolute bottom-20 left-1/2 z-20 -translate-x-1/2 rounded-sm border border-tactical-green/60 bg-base/90 px-3 py-1.5 font-mono text-xs text-tactical-green">
          {status}
        </div>
      )}
    </>
  );
}
