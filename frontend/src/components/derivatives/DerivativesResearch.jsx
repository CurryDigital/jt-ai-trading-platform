import { DerivPanel, DerivEmptyState } from './shared.jsx';

// Derivatives ▸ Research — derivative strategy research surface.
// Phase 1: honest PENDING shell. Phase 2 wires GET /api/derivatives/strategies;
// Phase 3 renders real rows once qr_etl/qr_research land the feeds.
export function DerivativesResearch() {
  return (
    <div className="space-y-3">
      <DerivPanel
        title="Derivative Strategies"
        endpoint="GET /api/derivatives/strategies"
        note="Options/futures strategy research — kept out of the shared equity strategy universe (Lab / Pipeline / Performance) by design."
      >
        <DerivEmptyState line="No derivative strategies yet — research registry feed pending." />
      </DerivPanel>
    </div>
  );
}
