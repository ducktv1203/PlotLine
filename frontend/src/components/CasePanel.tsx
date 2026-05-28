import { useEffect, useState } from "react";
import { FolderClosed, Plus, X } from "lucide-react";

import {
  createCase,
  deleteCase,
  fetchCase,
  listCases,
  type CaseSummary,
} from "@/lib/api";

interface CasePanelProps {
  /** Currently active case id, or null if none. */
  readonly activeCaseId: number | null;
  /** Called when the user opens a case — receives the case's track ids. */
  readonly onOpen: (caseId: number, trackIds: ReadonlyArray<number>) => void;
  /** Called when the user closes the active case (back to "no case"). */
  readonly onClose: () => void;
  /** The tracks currently visible — used as the basis for creating a case. */
  readonly visibleTrackIds: ReadonlyArray<number>;
}

export default function CasePanel({
  activeCaseId,
  onOpen,
  onClose,
  visibleTrackIds,
}: CasePanelProps) {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");

  const refresh = () => {
    listCases()
      .then((cs) => {
        setCases(cs);
        setError(null);
      })
      .catch((e: unknown) =>
        setError(e instanceof Error ? e.message : String(e)),
      );
  };

  useEffect(refresh, []);

  const handleOpen = async (id: number) => {
    try {
      const detail = await fetchCase(id);
      onOpen(detail.id, detail.track_ids);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      const created = await createCase(newName.trim(), visibleTrackIds);
      setNewName("");
      setCreating(false);
      refresh();
      onOpen(created.id, created.track_ids);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteCase(id);
      if (activeCaseId === id) onClose();
      refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="w-[220px] rounded-sm border border-tactical-cyan/40 bg-black/80 backdrop-blur-sm">
      <header className="flex items-center justify-between border-b border-tactical-cyan/30 px-3 py-2 text-[10px] uppercase tracking-[0.2em] text-tactical-cyan/70">
        <span>// cases</span>
        <button
          type="button"
          onClick={() => setCreating((c) => !c)}
          className="text-tactical-cyan/60 transition hover:text-tactical-cyan"
          title="New case from visible tracks"
        >
          <Plus size={12} />
        </button>
      </header>

      {creating && (
        <div className="border-b border-tactical-cyan/20 px-3 py-2">
          <input
            autoFocus
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleCreate();
              if (e.key === "Escape") setCreating(false);
            }}
            placeholder="case name"
            className="w-full bg-transparent font-mono text-xs text-tactical-cyan outline-none placeholder:text-tactical-cyan/30"
          />
          <div className="mt-1 text-[9px] uppercase tracking-[0.15em] text-tactical-cyan/40">
            wraps {visibleTrackIds.length} visible track
            {visibleTrackIds.length === 1 ? "" : "s"}
          </div>
        </div>
      )}

      {error && <div className="px-3 py-2 text-xs text-tactical-red">{error}</div>}

      <ul className="max-h-[180px] overflow-y-auto">
        {cases.length === 0 && !error && (
          <li className="px-3 py-2 text-xs text-tactical-cyan/40">
            no cases yet
          </li>
        )}
        {cases.map((c) => {
          const active = c.id === activeCaseId;
          return (
            <li key={c.id}>
              <div
                className={`group flex items-center gap-2 px-3 py-1.5 text-xs transition hover:bg-tactical-cyan/5 ${
                  active ? "bg-tactical-cyan/10" : ""
                }`}
              >
                <button
                  type="button"
                  onClick={() => (active ? onClose() : handleOpen(c.id))}
                  className="flex flex-1 items-center gap-2 text-left font-mono"
                >
                  <FolderClosed
                    size={12}
                    className={
                      active ? "text-tactical-cyan" : "text-tactical-cyan/50"
                    }
                  />
                  <span
                    className={`flex-1 truncate ${
                      active ? "text-tactical-cyan" : "text-tactical-cyan/80"
                    }`}
                  >
                    {c.name}
                  </span>
                  <span className="text-[9px] uppercase text-tactical-cyan/40">
                    {c.track_count}
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(c.id)}
                  className="opacity-0 transition group-hover:opacity-100"
                  title="Delete case"
                >
                  <X
                    size={11}
                    className="text-tactical-red/60 hover:text-tactical-red"
                  />
                </button>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
