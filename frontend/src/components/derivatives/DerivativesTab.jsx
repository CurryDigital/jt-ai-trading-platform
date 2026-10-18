import { useState } from 'react';
import { DerivativesResearch } from './DerivativesResearch.jsx';
import { DerivativesBacktest } from './DerivativesBacktest.jsx';
import { DerivativesExecution } from './DerivativesExecution.jsx';

// Derivatives main tab shell. Sub-tab switching is driven by App.jsx
// (subTabConfig.derivatives, hotkeys q/w/e); this component only mounts the
// active sub-panel. Everything derivatives-related lives under
// components/derivatives/ — the rest of the app is untouched.
//
// onSub (from App.jsx) lets a sub-panel request a sub-tab switch — used by
// the Research candidate card's "View detail" to open the Backtest tab with
// the strategy's headline run preselected (focusStrategy handoff).
export function DerivativesTab({ sub, onSub }) {
  const [focusStrategy, setFocusStrategy] = useState(null);
  // Shared basis toggle across Research and Backtest (2026-10-18, operator):
  // one control, default option-only — the carry-inclusive total basis
  // flatters every variant and the two sub-tabs must agree.
  const [basis, setBasis] = useState('opt');
  const viewRuns = (strategy) => {
    setFocusStrategy(strategy.strategy_id);
    onSub && onSub('backtest');
  };
  return (
    <>
      {sub === 'research'  && <DerivativesResearch onViewRuns={viewRuns} basis={basis} setBasis={setBasis} />}
      {sub === 'backtest'  && <DerivativesBacktest focusStrategy={focusStrategy} onFocusConsumed={() => setFocusStrategy(null)} basis={basis} setBasis={setBasis} />}
      {sub === 'execution' && <DerivativesExecution />}
    </>
  );
}
