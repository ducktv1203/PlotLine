import { useCallback, useMemo, useState } from "react";

import MapCanvas from "@/components/MapCanvas";
import TimeSlider from "@/components/TimeSlider";
import TerminalStream from "@/components/TerminalStream";
import TrackList from "@/components/TrackList";
import { useTimeline } from "@/hooks/useTimeline";

export default function App() {
  const [visibleIds, setVisibleIds] = useState<ReadonlyArray<number>>([]);
  const timeline = useTimeline();
  const { setRange } = timeline;

  const handleTracksBounds = useCallback(
    (startMs: number, endMs: number) => {
      setRange(startMs, endMs);
    },
    [setRange],
  );

  const toggleTrack = useCallback((id: number) => {
    setVisibleIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }, []);

  // Memoize trackIds so the same array identity is passed across re-renders
  // unless contents change — prevents MapCanvas refetch storms.
  const trackIds = useMemo(() => visibleIds, [visibleIds]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-base text-tactical-cyan">
      <section className="relative flex-1 border-r border-tactical-cyan/30">
        <MapCanvas
          trackIds={trackIds}
          playheadMs={
            timeline.state.endMs > 0 ? timeline.state.playheadMs : undefined
          }
          onTracksBounds={handleTracksBounds}
        />
        <div className="pointer-events-none absolute top-3 left-3">
          <div className="pointer-events-auto">
            <TrackList visibleIds={visibleIds} onToggle={toggleTrack} />
          </div>
        </div>
        <div className="pointer-events-none absolute inset-x-0 bottom-0 p-4">
          <div className="pointer-events-auto">
            <TimeSlider controller={timeline} />
          </div>
        </div>
      </section>
      <aside className="w-[360px] shrink-0">
        <TerminalStream />
      </aside>
    </div>
  );
}
