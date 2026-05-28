import { useEffect, useState } from "react";

const LINES: ReadonlyArray<string> = [
  "[boot] plotline shell ready",
  "[boot] webgl context initialized",
  "[boot] tile cache primed",
  "[boot] situation room online",
];

interface BootSequenceProps {
  /** Called once the sequence finishes typing. */
  readonly onDone?: () => void;
}

export default function BootSequence({ onDone }: BootSequenceProps) {
  const [visibleCount, setVisibleCount] = useState(0);
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    if (visibleCount >= LINES.length) {
      const t = setTimeout(() => {
        setHidden(true);
        onDone?.();
      }, 400);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setVisibleCount((c) => c + 1), 180);
    return () => clearTimeout(t);
  }, [visibleCount, onDone]);

  if (hidden) return null;

  return (
    <div className="pointer-events-none absolute inset-0 z-30 grid place-items-center bg-base/95">
      <pre className="font-mono text-sm leading-relaxed text-tactical-cyan">
        {LINES.slice(0, visibleCount).map((line, i) => (
          <div
            key={i}
            className={
              i === visibleCount - 1 ? "animate-pulse" : "text-tactical-cyan/60"
            }
          >
            {line}
          </div>
        ))}
      </pre>
    </div>
  );
}
