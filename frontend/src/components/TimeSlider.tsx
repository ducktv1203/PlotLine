import { Pause, Play } from "lucide-react";

import type { TimelineController } from "@/hooks/useTimeline";

interface TimeSliderProps {
  readonly controller: TimelineController;
}

function formatUtc(ms: number): string {
  if (!Number.isFinite(ms) || ms <= 0) return "--:--:--";
  return new Date(ms).toISOString().slice(11, 19);
}

export default function TimeSlider({ controller }: TimeSliderProps) {
  const { state, setPlayhead, togglePlay } = controller;
  const { playheadMs, startMs, endMs, playing } = state;

  const disabled = endMs <= startMs;

  return (
    <div className="flex w-full items-center gap-3 rounded-sm border border-tactical-cyan/40 bg-black/70 px-3 py-2 backdrop-blur-sm">
      <button
        type="button"
        onClick={togglePlay}
        disabled={disabled}
        aria-label={playing ? "Pause" : "Play"}
        className="grid h-7 w-7 place-items-center rounded-sm border border-tactical-cyan/60 text-tactical-cyan transition hover:border-tactical-cyan hover:shadow-neon disabled:opacity-30"
      >
        {playing ? <Pause size={14} /> : <Play size={14} />}
      </button>

      <div className="flex-1">
        <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.2em] text-tactical-cyan/60">
          <span>// timeline</span>
          <span>
            {formatUtc(playheadMs)} / {formatUtc(endMs)} UTC
          </span>
        </div>
        <input
          type="range"
          min={startMs}
          max={endMs || 1}
          step={1000}
          value={playheadMs}
          disabled={disabled}
          onChange={(e) => setPlayhead(Number(e.target.value))}
          className="mt-1 h-1 w-full cursor-pointer appearance-none rounded-full bg-tactical-cyan/20 accent-tactical-cyan disabled:opacity-40"
        />
      </div>
    </div>
  );
}
