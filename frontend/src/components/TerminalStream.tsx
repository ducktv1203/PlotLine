/**
 * TerminalStream — monospace scrolling log surface.
 * Phase 0 placeholder shell only. Will be wired to a backend SSE/WebSocket
 * channel for live ingestion + spatial event traces.
 */
export default function TerminalStream(): JSX.Element {
  return (
    <div className="flex h-full flex-col bg-base">
      <header className="flex items-center justify-between border-b border-tactical-cyan/30 px-3 py-2 text-[10px] uppercase tracking-[0.2em] text-tactical-cyan/70">
        <span>plotline://stream</span>
        <span className="text-tactical-green">● live</span>
      </header>
      <pre
        className="flex-1 overflow-auto whitespace-pre-wrap px-3 py-2 text-xs leading-relaxed text-tactical-cyan/80"
        aria-live="polite"
      >
        {"[boot] plotline shell ready\n[boot] awaiting ingest..."}
      </pre>
    </div>
  );
}
