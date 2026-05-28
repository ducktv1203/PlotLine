/**
 * MapCanvas — Maplibre GL + Deck.gl overlay mount point.
 *
 * Phase 0 placeholder: no map instance is constructed here. The eventual
 * implementation will:
 *   1. Create a Maplibre `Map` against this <div> with a dark style.
 *   2. Attach a Deck.gl `MapboxOverlay` so deck layers share Maplibre's
 *      WebGL context (single context, no canvas stacking).
 *   3. Subscribe to the timeline hook for per-frame layer updates.
 */
export default function MapCanvas(): JSX.Element {
  return (
    <div
      id="plotline-map"
      className="h-full w-full bg-base"
      data-status="uninitialized"
    />
  );
}
