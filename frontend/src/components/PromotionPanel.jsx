import React, { useEffect, useState } from 'react';
import { api } from '../utils';

const MODE_LABEL = {
  SIMULATION: 'SIM',
  PAPER_TRADING: 'PAPER',
  LIVE_TRADING: 'LIVE',
};
const MODE_COLOR = {
  SIMULATION: 'qr-chip-blue',
  PAPER_TRADING: 'qr-chip-amber',
  LIVE_TRADING: 'qr-chip-rose',
};

const MODES_ORDER = ['SIMULATION', 'PAPER_TRADING', 'LIVE_TRADING'];

const fmtThreshold = (v) => {
  if (v == null) return '—';
  if (typeof v === 'number') return Number.isInteger(v) ? v : v.toFixed(2);
  return String(v);
};

const fmtActual = (v) => {
  if (v == null) return '—';
  if (typeof v === 'number') return Number.isInteger(v) ? v : v.toFixed(2);
  return String(v);
};

export const PromotionPanel = ({ strategyId, currentMode, onPromoted }) => {
  const [target, setTarget] = useState(null);
  const [check, setCheck] = useState(null);
  const [loading, setLoading] = useState(false);
  const [confirmPhrase, setConfirmPhrase] = useState('');
  const [override, setOverride] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null);

  // Default target = next mode up
  useEffect(() => {
    if (!currentMode) return;
    const idx = MODES_ORDER.indexOf(currentMode);
    const next = idx >= 0 && idx < MODES_ORDER.length - 1 ? MODES_ORDER[idx + 1] : null;
    setTarget(next || (idx > 0 ? MODES_ORDER[idx - 1] : null));
  }, [currentMode]);

  const runCheck = async (t = target) => {
    if (!t) return;
    setLoading(true);
    setFeedback(null);
    const res = await api.post(`/api/strategies/${encodeURIComponent(strategyId)}/promote/check`, { target_mode: t });
    setCheck(res);
    setLoading(false);
  };

  useEffect(() => {
    if (target) runCheck(target);
  }, [target, strategyId]);

  const submit = async () => {
    if (!target) return;
    setSubmitting(true);
    setFeedback(null);
    const body = { target_mode: target };
    if (check?.requires_confirmation_phrase) body.confirmation_phrase = confirmPhrase;
    if (override) body.override_gates = true;
    const res = await api.post(`/api/strategies/${encodeURIComponent(strategyId)}/promote`, body);
    setSubmitting(false);

    if (!res) {
      setFeedback({ ok: false, msg: 'Request failed (network or 5xx)' });
      return;
    }
    if (res.success) {
      setFeedback({ ok: true, msg: res.message || 'Mode updated' });
      setConfirmPhrase('');
      setOverride(false);
      onPromoted?.(res.current_mode);
      runCheck(target);
    } else {
      setFeedback({ ok: false, msg: res.message || 'Blocked by gates' });
    }
  };

  if (!currentMode) return null;

  const isPromotion = check?.is_promotion;
  const phraseRequired = check?.requires_confirmation_phrase;
  const phraseOk = !phraseRequired || confirmPhrase === check?.confirmation_phrase;
  const gatesPassed = check?.passed;
  const canSubmit = !!target && target !== currentMode
    && (gatesPassed || override || !isPromotion)
    && phraseOk
    && !submitting;

  return (
    <div className="qr-surface overflow-hidden">
      <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="qr-label">Mode Promotion</span>
          <span className={`qr-chip ${MODE_COLOR[currentMode] || 'qr-chip-slate'}`}>{MODE_LABEL[currentMode] || currentMode}</span>
          <span className="text-slate-600">→</span>
          <div className="flex gap-0.5 p-0.5 rounded bg-slate-900/60 border border-white/[0.06]">
            {MODES_ORDER.map(m => (
              <button
                key={m}
                onClick={() => setTarget(m)}
                disabled={m === currentMode}
                className={`px-2 py-0.5 rounded text-[10px] font-bold transition-colors ${
                  m === currentMode
                    ? 'text-slate-700 cursor-not-allowed'
                    : target === m
                    ? 'bg-blue-500 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {MODE_LABEL[m]}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {check && (
            <span className={`qr-chip ${gatesPassed ? 'qr-chip-emerald' : isPromotion ? 'qr-chip-rose' : 'qr-chip-slate'}`}>
              {gatesPassed ? 'GATES PASS' : isPromotion ? 'BLOCKED' : 'NO GATES'}
            </span>
          )}
          <button onClick={() => runCheck()} className="qr-btn-ghost" disabled={loading}>
            {loading ? '…' : '↻ Recheck'}
          </button>
        </div>
      </div>

      <div className="p-3 space-y-2">
        {check?.blocked && (
          <div className="text-[11px] text-rose-300 bg-rose-500/10 ring-1 ring-rose-500/25 rounded-md px-3 py-2">
            {check.reason || 'Transition not supported'}
          </div>
        )}

        {check && !check.blocked && check.gates.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-1">
            {check.gates.map(g => (
              <div
                key={g.id}
                className={`flex items-start gap-2 px-2.5 py-1.5 rounded-md ring-1 ${
                  g.pass
                    ? 'bg-emerald-500/5 ring-emerald-500/20'
                    : g.required
                    ? 'bg-rose-500/5 ring-rose-500/20'
                    : 'bg-slate-800/30 ring-white/5'
                }`}
              >
                <span className={`mt-0.5 inline-flex items-center justify-center w-4 h-4 rounded-full text-[9px] font-bold ${
                  g.pass ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                }`}>
                  {g.pass ? '✓' : '✕'}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-[11px] text-white font-semibold truncate">{g.label}</div>
                  <div className="qr-num text-[9px] text-slate-500 mt-0.5">
                    actual <span className="text-slate-300">{fmtActual(g.actual)}</span>
                    <span className="text-slate-700 mx-1">·</span>
                    target <span className="text-slate-300">{fmtThreshold(g.threshold)}</span>
                  </div>
                  {!g.pass && g.reason && (
                    <div className="text-[9px] text-rose-300/80 mt-0.5">{g.reason}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {check && !check.blocked && check.gates.length === 0 && (
          <div className="text-[10px] text-slate-500">No gates required for this transition (demotion / lateral)</div>
        )}

        {/* Confirmation + override row */}
        {check && !check.blocked && target !== currentMode && (
          <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-white/[0.05]">
            {phraseRequired && (
              <label className="flex items-center gap-2">
                <span className="qr-label">Confirm</span>
                <input
                  type="text"
                  value={confirmPhrase}
                  onChange={(e) => setConfirmPhrase(e.target.value)}
                  placeholder={check.confirmation_phrase}
                  className="px-2 py-1 bg-slate-900/60 border border-white/[0.08] rounded text-[11px] text-white w-44 placeholder-slate-600 focus:outline-none focus:border-rose-500/50 font-mono"
                />
              </label>
            )}
            {isPromotion && !gatesPassed && (
              <label className="flex items-center gap-1.5 text-[10px] text-amber-300 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={override}
                  onChange={(e) => setOverride(e.target.checked)}
                  className="accent-amber-400"
                />
                Override gates (audited)
              </label>
            )}
            <button
              onClick={submit}
              disabled={!canSubmit}
              className={`ml-auto px-3 py-1.5 rounded text-[11px] font-bold transition-colors ${
                !canSubmit
                  ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
                  : target === 'LIVE_TRADING'
                  ? 'bg-rose-500/20 text-rose-200 ring-1 ring-rose-500/40 hover:bg-rose-500/30'
                  : 'bg-blue-500/20 text-blue-200 ring-1 ring-blue-500/40 hover:bg-blue-500/30'
              }`}
            >
              {submitting ? 'Submitting…' : isPromotion ? `Promote → ${MODE_LABEL[target]}` : `Set to ${MODE_LABEL[target]}`}
            </button>
          </div>
        )}

        {feedback && (
          <div className={`mt-2 text-[11px] px-3 py-2 rounded-md ring-1 ${
            feedback.ok
              ? 'bg-emerald-500/10 ring-emerald-500/25 text-emerald-200'
              : 'bg-rose-500/10 ring-rose-500/25 text-rose-200'
          }`}>
            {feedback.msg}
          </div>
        )}
      </div>
    </div>
  );
};

export default PromotionPanel;
