/**
 * useTimeline — shared scrubber state coordinator.
 *
 * Exposes the playhead and play/pause/scrub controls. The playhead
 * advances inside a requestAnimationFrame loop and commits to React
 * state on every frame, which is fine at RAF rate and keeps the slider
 * UI and the deck.gl layer in lockstep.
 */
import { useCallback, useEffect, useRef, useState } from "react";

export interface TimelineState {
  readonly playheadMs: number;
  readonly startMs: number;
  readonly endMs: number;
  readonly playing: boolean;
}

export interface TimelineController {
  readonly state: TimelineState;
  setPlayhead(ms: number): void;
  setRange(startMs: number, endMs: number): void;
  play(): void;
  pause(): void;
  togglePlay(): void;
}

const INITIAL_STATE: TimelineState = {
  playheadMs: 0,
  startMs: 0,
  endMs: 0,
  playing: false,
};

/**
 * Playback rate in "ms of data per ms of wall clock". 1000 = one minute of
 * data per real-world second.
 */
const PLAYBACK_RATE = 1000;

export function useTimeline(): TimelineController {
  const [state, setState] = useState<TimelineState>(INITIAL_STATE);
  const stateRef = useRef(state);
  stateRef.current = state;

  const rafRef = useRef<number | null>(null);
  const lastFrameRef = useRef<number>(0);

  const cancelLoop = useCallback(() => {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const loop = useCallback(
    (now: number) => {
      const current = stateRef.current;
      if (!current.playing) return;

      const dt = now - lastFrameRef.current;
      lastFrameRef.current = now;

      const next = current.playheadMs + dt * PLAYBACK_RATE;

      if (current.endMs > 0 && next >= current.endMs) {
        setState((s) => ({ ...s, playheadMs: s.endMs, playing: false }));
        cancelLoop();
        return;
      }

      setState((s) => ({ ...s, playheadMs: next }));
      rafRef.current = requestAnimationFrame(loop);
    },
    [cancelLoop],
  );

  const play = useCallback(() => {
    const current = stateRef.current;
    if (current.playing) return;
    lastFrameRef.current = performance.now();
    const playheadMs =
      current.endMs > 0 && current.playheadMs >= current.endMs
        ? current.startMs
        : current.playheadMs;
    setState((s) => ({ ...s, playing: true, playheadMs }));
    rafRef.current = requestAnimationFrame(loop);
  }, [loop]);

  const pause = useCallback(() => {
    cancelLoop();
    setState((s) => ({ ...s, playing: false }));
  }, [cancelLoop]);

  const togglePlay = useCallback(() => {
    if (stateRef.current.playing) pause();
    else play();
  }, [pause, play]);

  const setPlayhead = useCallback((ms: number) => {
    setState((s) => ({ ...s, playheadMs: ms }));
  }, []);

  const setRange = useCallback((startMs: number, endMs: number) => {
    setState((s) => ({ ...s, startMs, endMs, playheadMs: startMs }));
  }, []);

  useEffect(() => cancelLoop, [cancelLoop]);

  return { state, setPlayhead, setRange, play, pause, togglePlay };
}
