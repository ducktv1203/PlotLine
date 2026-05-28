import { useEffect, useState } from "react";

import { listTracks, type TrackSummary } from "@/lib/api";
import { colorForTrack } from "@/lib/layers";

interface TrackListProps {
  readonly visibleIds: ReadonlyArray<number>;
  readonly onToggle: (id: number) => void;
  readonly onRefresh?: () => void;
}

export default function TrackList({
  visibleIds,
  onToggle,
  onRefresh,
}: TrackListProps) {
  const [tracks, setTracks] = useState<TrackSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => {
    listTracks()
      .then((rs) => {
        setTracks(rs);
        setError(null);
      })
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : String(e)),
      );
  };

  useEffect(refresh, []);
  useEffect(() => {
    if (!onRefresh) return;
    refresh();
  }, [onRefresh]);

  return (
    <div className="w-[220px] rounded-sm border border-tactical-cyan/40 bg-black/80 backdrop-blur-sm">
      <header className="flex items-center justify-between border-b border-tactical-cyan/30 px-3 py-2 text-[10px] uppercase tracking-[0.2em] text-tactical-cyan/70">
        <span>// tracks</span>
        <button
          type="button"
          onClick={refresh}
          className="text-tactical-cyan/60 transition hover:text-tactical-cyan"
        >
          refresh
        </button>
      </header>
      {error && (
        <div className="px-3 py-2 text-xs text-tactical-red">{error}</div>
      )}
      <ul className="max-h-[280px] overflow-y-auto">
        {tracks.length === 0 && !error && (
          <li className="px-3 py-2 text-xs text-tactical-cyan/40">
            no tracks ingested
          </li>
        )}
        {tracks.map((t) => {
          const checked = visibleIds.includes(t.id);
          const [r, g, b] = colorForTrack(t.id);
          return (
            <li key={t.id}>
              <label className="flex cursor-pointer items-center gap-2 px-3 py-1.5 text-xs transition hover:bg-tactical-cyan/5">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => onToggle(t.id)}
                  className="h-3 w-3 accent-tactical-cyan"
                />
                <span
                  className="inline-block h-2 w-2 rounded-full"
                  style={{ backgroundColor: `rgb(${r},${g},${b})` }}
                />
                <span className="flex-1 truncate font-mono text-tactical-cyan/80">
                  #{t.id} {t.label}
                </span>
                <span className="text-[9px] uppercase text-tactical-cyan/40">
                  {t.source_format}
                </span>
              </label>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
