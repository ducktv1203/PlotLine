/**
 * useTimeline — shared scrubber state coordinator.
 *
 * Phase 0 surface contract only. The hook will eventually own:
 *   - current playhead (epoch ms)
 *   - playback rate
 *   - inclusive [start, end] domain bounds
 * and broadcast updates to MapCanvas (layer time filter) and TerminalStream.
 */
import { useState } from "react";

export interface TimelineState {
  readonly playheadMs: number;
  readonly startMs: number;
  readonly endMs: number;
  readonly playing: boolean;
}

export interface TimelineController extends TimelineState {
  setPlayhead(ms: number): void;
  setRange(startMs: number, endMs: number): void;
  togglePlay(): void;
}

const INITIAL_STATE: TimelineState = {
  playheadMs: 0,
  startMs: 0,
  endMs: 0,
  playing: false,
};

export function useTimeline(): TimelineController {
  const [state, setState] = useState<TimelineState>(INITIAL_STATE);

  return {
    ...state,
    setPlayhead: (ms) => setState((s) => ({ ...s, playheadMs: ms })),
    setRange: (startMs, endMs) =>
      setState((s) => ({ ...s, startMs, endMs })),
    togglePlay: () => setState((s) => ({ ...s, playing: !s.playing })),
  };
}
