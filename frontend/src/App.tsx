import { useCallback, useState } from "react";

import MapCanvas from "@/components/MapCanvas";
import TimeSlider from "@/components/TimeSlider";
import TerminalStream from "@/components/TerminalStream";
import TrackPicker from "@/components/TrackPicker";
import { useTimeline } from "@/hooks/useTimeline";

export default function App() {
  const [trackId, setTrackId] = useState<number | undefined>(undefined);
  const timeline = useTimeline();
  const { setRange } = timeline;

  const handleTrackBounds = useCallback(
    (startMs: number, endMs: number) => {
      setRange(startMs, endMs);
    },
    [setRange],
  );

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-base text-tactical-cyan">
      <section className="relative flex-1 border-r border-tactical-cyan/30">
        <MapCanvas
          trackId={trackId}
          playheadMs={
            timeline.state.endMs > 0 ? timeline.state.playheadMs : undefined
          }
          onTrackBounds={handleTrackBounds}
        />
        <div className="pointer-events-none absolute top-3 left-3">
          <div className="pointer-events-auto">
            <TrackPicker value={trackId} onChange={setTrackId} />
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
