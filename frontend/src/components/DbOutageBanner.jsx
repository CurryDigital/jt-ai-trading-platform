import { useState, useEffect, useRef } from 'react';
import { useDbHealth } from '../utils.js';

// Global database-outage banner. Mounted in main.jsx so it renders above
// every gate (auth check, login page, loading spinner) — infra status is not
// privileged information. Rose accent = critical severity (palette rule).
// Dismiss snoozes for 10 minutes; the banner returns while the outage lasts
// and clears itself the moment the DB answers healthy again.
const SNOOZE_MS = 10 * 60 * 1000;

export default function DbOutageBanner() {
  const status = useDbHealth();
  const [snoozedUntil, setSnoozedUntil] = useState(0);
  const wasBad = useRef(false);

  const bad = status === 'degraded' || status === 'down';

  // Auto-clear snooze on recovery so the next outage re-shows the banner
  useEffect(() => {
    if (!bad && wasBad.current) setSnoozedUntil(0);
    wasBad.current = bad;
  }, [bad]);

  if (!bad || Date.now() < snoozedUntil) return null;

  const label = status === 'down'
    ? 'BACKEND UNREACHABLE'
    : 'DATABASE UNREACHABLE';

  return (
    <div className="fixed bottom-3 left-1/2 -translate-x-1/2 z-50 max-w-[92vw]">
      <div className="flex items-center gap-2.5 px-3 py-2 rounded-md border border-rose-500/40 bg-[#0a0c10]/95 shadow-lg shadow-rose-500/10 backdrop-blur">
        <span className="relative flex h-2 w-2 shrink-0">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-60" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-400" />
        </span>
        <div className="text-[11px] leading-tight">
          <span className="font-bold text-rose-300 tracking-wide">{label}</span>
          <span className="text-slate-400">
            {' '}— panels may be empty or stale. Infra incident t_b2b5e4fd, recovery in progress; this clears automatically.
          </span>
        </div>
        <button
          onClick={() => setSnoozedUntil(Date.now() + SNOOZE_MS)}
          className="ml-1 shrink-0 text-slate-500 hover:text-slate-300 text-sm leading-none px-1"
          title="Snooze for 10 minutes"
          aria-label="Dismiss"
        >
          ×
        </button>
      </div>
    </div>
  );
}
