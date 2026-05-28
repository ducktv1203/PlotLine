/**
 * Tiny keybinding hook. Map a key (or `Space`, `ArrowLeft`, ...) to a handler.
 * Keys typed into form fields are ignored so checkboxes/inputs still work.
 */
import { useEffect } from "react";

export type Hotkeys = Readonly<Record<string, (e: KeyboardEvent) => void>>;

export function useHotkeys(bindings: Hotkeys): void {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (target) {
        const tag = target.tagName;
        if (tag === "INPUT" || tag === "TEXTAREA" || target.isContentEditable) {
          return;
        }
      }
      const fn = bindings[e.key] ?? bindings[e.code];
      if (fn) {
        e.preventDefault();
        fn(e);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [bindings]);
}
