import { useCallback, useMemo, useState } from "react";

import BootSequence from "@/components/BootSequence";
import CasePanel from "@/components/CasePanel";
import DropZone from "@/components/DropZone";
import MapCanvas from "@/components/MapCanvas";
import TimeSlider from "@/components/TimeSlider";
import TerminalStream from "@/components/TerminalStream";
import TrackList from "@/components/TrackList";
import { useHotkeys } from "@/hooks/useHotkeys";
import { useTimeline } from "@/hooks/useTimeline";
import { createCase, ingestGeoJSON } from "@/lib/api";

export default function App() {
  const [visibleIds, setVisibleIds] = useState<ReadonlyArray<number>>([]);
  const [activeCaseId, setActiveCaseId] = useState<number | null>(null);
  const [trackListVersion, setTrackListVersion] = useState(0);
  const [caseListVersion, setCaseListVersion] = useState(0);
  const [boot, setBoot] = useState(true);
  const timeline = useTimeline();
  const { setRange, setPlayhead, togglePlay, state: tlState } = timeline;

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

  const handleIngested = useCallback((trackId: number) => {
    setTrackListVersion((v) => v + 1);
    setVisibleIds((prev) =>
      prev.includes(trackId) ? prev : [...prev, trackId],
    );
  }, []);

  const handleOpenCase = useCallback(
    (caseId: number, trackIds: ReadonlyArray<number>) => {
      setActiveCaseId(caseId);
      setVisibleIds(trackIds);
    },
    [],
  );

  const handleCloseCase = useCallback(() => {
    setActiveCaseId(null);
    setVisibleIds([]);
  }, []);

  const loadDemo = useCallback(async () => {
    try {
      const manifestRes = await fetch("/demo/index.json");
      if (!manifestRes.ok)
        throw new Error(`demo index fetch failed: ${manifestRes.status}`);
      const manifest = (await manifestRes.json()) as Array<{
        file: string;
        label: string;
        points: number;
        category?: string;
      }>;

      // Group by category so each category becomes its own case.
      const byCategory = new Map<string, typeof manifest>();
      for (const entry of manifest) {
        const cat = entry.category ?? "Uncategorized Demo";
        const bucket = byCategory.get(cat) ?? [];
        bucket.push(entry);
        byCategory.set(cat, bucket);
      }

      let lastCase: { id: number; trackIds: number[] } | null = null;
      for (const [category, entries] of byCategory) {
        const ids: number[] = [];
        for (const entry of entries) {
          const fc = await (await fetch(`/demo/${entry.file}`)).json();
          const ingested = await ingestGeoJSON(entry.label, fc);
          ids.push(ingested.track_id);
        }
        if (ids.length > 0) {
          const created = await createCase(
            category,
            ids,
            "Auto-generated demo data",
          );
          lastCase = { id: created.id, trackIds: ids };
        }
      }
      setTrackListVersion((v) => v + 1);
      setCaseListVersion((v) => v + 1);
      // Open one case cleanly — replaces visibleIds with just that case's
      // tracks so the camera fits to one city instead of all cities at once.
      if (lastCase) handleOpenCase(lastCase.id, lastCase.trackIds);
    } catch (e) {
      console.error("loadDemo failed", e);
    }
  }, [handleOpenCase]);

  const stepFrame = useCallback(
    (deltaMs: number) => {
      const next = Math.max(
        tlState.startMs,
        Math.min(tlState.endMs || tlState.startMs, tlState.playheadMs + deltaMs),
      );
      setPlayhead(next);
    },
    [setPlayhead, tlState.endMs, tlState.playheadMs, tlState.startMs],
  );

  const hotkeys = useMemo(
    () => ({
      " ": () => togglePlay(),
      Space: () => togglePlay(),
      "[": () => stepFrame(-60_000),
      "]": () => stepFrame(60_000),
      d: () => void loadDemo(),
      r: () => setPlayhead(tlState.startMs),
    }),
    [togglePlay, stepFrame, loadDemo, setPlayhead, tlState.startMs],
  );
  useHotkeys(hotkeys);

  const trackIds = useMemo(() => visibleIds, [visibleIds]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-base text-tactical-cyan">
      <section className="relative flex-1 border-r border-tactical-cyan/30">
        {boot && <BootSequence onDone={() => setBoot(false)} />}
        <MapCanvas
          trackIds={trackIds}
          playheadMs={
            timeline.state.endMs > 0 ? timeline.state.playheadMs : undefined
          }
          onTracksBounds={handleTracksBounds}
        />
        <DropZone onIngested={handleIngested} />
        <div className="pointer-events-none absolute top-3 left-3 space-y-2">
          <div className="pointer-events-auto">
            <CasePanel
              activeCaseId={activeCaseId}
              onOpen={handleOpenCase}
              onClose={handleCloseCase}
              visibleTrackIds={visibleIds}
              refreshKey={caseListVersion}
            />
          </div>
          <div className="pointer-events-auto">
            <TrackList
              key={trackListVersion}
              visibleIds={visibleIds}
              onToggle={toggleTrack}
            />
          </div>
        </div>
        <div className="pointer-events-none absolute top-3 right-3 rounded-sm border border-tactical-cyan/30 bg-black/60 px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.18em] text-tactical-cyan/50 backdrop-blur-sm">
          <span className="text-tactical-cyan">d</span> demo &nbsp;
          <span className="text-tactical-cyan">space</span> play &nbsp;
          <span className="text-tactical-cyan">[ ]</span> step &nbsp;
          <span className="text-tactical-cyan">r</span> reset
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
