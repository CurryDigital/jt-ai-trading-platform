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
  const viewRuns = (strategy) => {
    setFocusStrategy(strategy.strategy_id);
    onSub && onSub('backtest');
  };
  return (
    <>
      {sub === 'research'  && <DerivativesResearch onViewRuns={viewRuns} />}
      {sub === 'backtest'  && <DerivativesBacktest focusStrategy={focusStrategy} onFocusConsumed={() => setFocusStrategy(null)} />}
      {sub === 'execution' && <DerivativesExecution />}
    </>
  );
}
