/**
 * TimeSlider — chronological scrubber placeholder.
 * The eventual implementation will read/write the shared timeline state
 * from `useTimeline` and emit current-time updates at animation frame rate.
 */
export default function TimeSlider(): JSX.Element {
  return (
    <div className="w-full rounded-sm border border-tactical-cyan/40 bg-black/70 px-3 py-2 backdrop-blur-sm">
      <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.2em] text-tactical-cyan/60">
        <span>// timeline</span>
        <span>00:00:00 — 00:00:00 UTC</span>
      </div>
      <div
        className="mt-1 h-[2px] w-full bg-tactical-cyan/20"
        role="presentation"
      />
    </div>
  );
}
