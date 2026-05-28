interface TrackPickerProps {
  readonly value: number | undefined;
  readonly onChange: (id: number | undefined) => void;
}

/** Minimal numeric input for selecting which track to display. */
export default function TrackPicker({ value, onChange }: TrackPickerProps) {
  return (
    <div className="flex items-center gap-2 rounded-sm border border-tactical-cyan/40 bg-black/70 px-3 py-2 backdrop-blur-sm">
      <span className="text-[10px] uppercase tracking-[0.2em] text-tactical-cyan/60">
        track id
      </span>
      <input
        type="number"
        min={1}
        inputMode="numeric"
        value={value ?? ""}
        onChange={(e) => {
          const next = e.target.value.trim();
          onChange(next === "" ? undefined : Number(next));
        }}
        className="w-20 bg-transparent font-mono text-sm text-tactical-cyan outline-none placeholder:text-tactical-cyan/30"
        placeholder="—"
      />
    </div>
  );
}
