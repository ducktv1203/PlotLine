import { useState } from "react";

import MapCanvas from "@/components/MapCanvas";
import TimeSlider from "@/components/TimeSlider";
import TerminalStream from "@/components/TerminalStream";
import TrackPicker from "@/components/TrackPicker";

/**
 * Top-level situation-room layout:
 *   - Left  (flex-1):           full-bleed map canvas + timeline scrubber overlay
 *   - Right (w-[360px]):        monospace terminal stream sidebar
 */
export default function App() {
  const [trackId, setTrackId] = useState<number | undefined>(undefined);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-base text-tactical-cyan">
      <section className="relative flex-1 border-r border-tactical-cyan/30">
        <MapCanvas trackId={trackId} />
        <div className="pointer-events-none absolute top-3 left-3">
          <div className="pointer-events-auto">
            <TrackPicker value={trackId} onChange={setTrackId} />
          </div>
        </div>
        <div className="pointer-events-none absolute inset-x-0 bottom-0 p-4">
          <div className="pointer-events-auto">
            <TimeSlider />
          </div>
        </div>
      </section>
      <aside className="w-[360px] shrink-0">
        <TerminalStream />
      </aside>
    </div>
  );
}
