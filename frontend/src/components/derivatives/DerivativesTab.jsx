import { DerivativesResearch } from './DerivativesResearch.jsx';
import { DerivativesBacktest } from './DerivativesBacktest.jsx';
import { DerivativesExecution } from './DerivativesExecution.jsx';

// Derivatives main tab shell. Sub-tab switching is driven by App.jsx
// (subTabConfig.derivatives, hotkeys q/w/e); this component only mounts the
// active sub-panel. Everything derivatives-related lives under
// components/derivatives/ — the rest of the app is untouched.
export function DerivativesTab({ sub }) {
  return (
    <>
      {sub === 'research'  && <DerivativesResearch />}
      {sub === 'backtest'  && <DerivativesBacktest />}
      {sub === 'execution' && <DerivativesExecution />}
    </>
  );
}
