import React, { useState, useEffect, useMemo } from 'react';
import { api, fmtK, pnlCl } from '../utils';

const inputCls = 'px-2 py-1.5 bg-slate-800/80 border border-white/10 rounded-lg text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/50';

// ---------------------------------------------------------------------------
// Presets
// ---------------------------------------------------------------------------
const PRESETS = {
  conservative: {
    label: 'Conservative',
    values: {
      risk_max_daily_loss_pct: 2,
      risk_max_position_pct: 10,
      risk_max_hhi: 1800,
      risk_max_consecutive_losses: 3,
      risk_max_drawdown_pct: 8,
    },
  },
  moderate: {
    label: 'Moderate',
    values: {
      risk_max_daily_loss_pct: 5,
      risk_max_position_pct: 20,
      risk_max_hhi: 2500,
      risk_max_consecutive_losses: 5,
      risk_max_drawdown_pct: 15,
    },
  },
  aggressive: {
    label: 'Aggressive',
    values: {
      risk_max_daily_loss_pct: 10,
      risk_max_position_pct: 35,
      risk_max_hhi: 4000,
      risk_max_consecutive_losses: 8,
      risk_max_drawdown_pct: 25,
    },
  },
};

const GLOBAL_FIELDS = [
  { key: 'risk_max_daily_loss_pct',     label: 'Max portfolio risk / day',      unit: '% equity',  defaultVal: 5 },
  { key: 'risk_max_position_pct',       label: 'Max single position size',      unit: '% portfolio', defaultVal: 20 },
  { key: 'risk_max_hhi',               label: 'Max correlation exposure (HHI)', unit: '',           defaultVal: 2500 },
  { key: 'risk_max_consecutive_losses', label: 'Max consecutive losses',        unit: 'trades',     defaultVal: 5 },
  { key: 'risk_max_drawdown_pct',       label: 'Max drawdown (kill switch)',    unit: '%',          defaultVal: 15 },
];

// ---------------------------------------------------------------------------
// Inline editable cell
// ---------------------------------------------------------------------------
const EditableCell = ({ value, onSave, suffix = '', placeholder = '--' }) => {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState('');

  const beginEdit = () => {
    setDraft(value ?? '');
    setEditing(true);
  };

  const commit = () => {
    setEditing(false);
    const num = parseFloat(draft);
    if (!isNaN(num)) onSave(num);
  };

  if (!editing) {
    return (
      <span
        className="cursor-pointer qr-num text-xs text-slate-300 hover:text-white px-1.5 py-0.5 rounded hover:bg-white/5"
        onClick={beginEdit}
        title="Click to edit"
      >
        {value != null ? `${value}${suffix}` : placeholder}
      </span>
    );
  }
  return (
    <input
      autoFocus
      type="number"
      className={`${inputCls} w-20`}
      value={draft}
      onChange={e => setDraft(e.target.value)}
      onBlur={commit}
      onKeyDown={e => { if (e.key === 'Enter') commit(); if (e.key === 'Escape') setEditing(false); }}
    />
  );
};

// ---------------------------------------------------------------------------
// Toggle switch
// ---------------------------------------------------------------------------
const Toggle = ({ on, onChange }) => (
  <button
    onClick={() => onChange(!on)}
    className={`w-9 h-5 rounded-full transition-all flex items-center ${on ? 'bg-emerald-500' : 'bg-slate-700'}`}
  >
    <div className={`w-4 h-4 rounded-full bg-white transition-all ${on ? 'translate-x-[18px]' : 'translate-x-0.5'}`} />
  </button>
);

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
export const RiskLimitsConfig = () => {
  // --- State ---
  const [globalLimits, setGlobalLimits] = useState(() => {
    const init = {};
    GLOBAL_FIELDS.forEach(f => { init[f.key] = f.defaultVal; });
    return init;
  });
  const [strategies, setStrategies] = useState([]);
  const [overrides, setOverrides] = useState({}); // { strategy_id: { max_position_pct, max_daily_loss_pct, enabled } }
  const [riskSummary, setRiskSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  // --- Load data ---
  useEffect(() => {
    const load = async () => {
      const [limitsRes, strats, risk, alertsRes] = await Promise.all([
        api.get('/api/risk/limits'),
        api.get('/api/strategies/researcher'),
        api.get('/api/portfolio/risk-summary'),
        api.get('/api/portfolio/alerts'),
      ]);

      if (limitsRes?.limits) {
        const settings = limitsRes.limits;
        setGlobalLimits(prev => {
          const next = { ...prev };
          GLOBAL_FIELDS.forEach(f => {
            if (settings[f.key] != null) next[f.key] = Number(settings[f.key]);
          });
          return next;
        });

        const ov = {};
        Object.keys(settings).forEach(k => {
          const m = k.match(/^risk_override_(.+?)_(max_position_pct|max_daily_loss_pct|enabled)$/);
          if (m) {
            const sid = m[1];
            const field = m[2];
            if (!ov[sid]) ov[sid] = {};
            ov[sid][field] = field === 'enabled' ? settings[k] === 'true' || settings[k] === true : Number(settings[k]);
          }
        });
        setOverrides(ov);
      }
      if (strats?.strategies) setStrategies(strats.strategies);
      if (risk) setRiskSummary(risk);
      if (alertsRes) setAlerts(Array.isArray(alertsRes) ? alertsRes : alertsRes.alerts || []);
      setLoading(false);
    };
    load();
  }, []);

  // --- Save global limits ---
  const saveGlobal = async () => {
    setSaving(true);
    setSaved(false);
    const payload = { ...globalLimits };
    // Also include overrides
    Object.entries(overrides).forEach(([sid, ov]) => {
      Object.entries(ov).forEach(([field, val]) => {
        payload[`risk_override_${sid}_${field}`] = val;
      });
    });
    await api.post('/api/risk/limits', payload);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  // --- Apply preset ---
  const applyPreset = (presetKey) => {
    setGlobalLimits(prev => ({ ...prev, ...PRESETS[presetKey].values }));
  };

  // --- Override helpers ---
  const getOverride = (strategyId, field) => overrides[strategyId]?.[field] ?? null;
  const setOverride = (strategyId, field, value) => {
    setOverrides(prev => ({
      ...prev,
      [strategyId]: { ...prev[strategyId], [field]: value },
    }));
  };

  // --- Risk status helpers ---
  const alertsByLevel = useMemo(() => {
    const crit = alerts.filter(a => a.level === 'critical');
    const warn = alerts.filter(a => a.level === 'warning');
    return { critical: crit, warning: warn, total: alerts.length };
  }, [alerts]);

  const statusChip = useMemo(() => {
    if (alertsByLevel.critical.length > 0) return { cls: 'qr-chip-rose', text: 'BREACHED' };
    if (alertsByLevel.warning.length > 0) return { cls: 'qr-chip-amber', text: 'WARNING' };
    return { cls: 'qr-chip-emerald', text: 'WITHIN LIMITS' };
  }, [alertsByLevel]);

  // --- Loading state ---
  if (loading) {
    return (
      <div className="qr-surface px-4 py-6 flex items-center gap-2 text-[11px] text-slate-500">
        <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
        Loading risk configuration...
      </div>
    );
  }

  return (
    <div className="space-y-4 max-w-5xl">
      {/* ---- Header ---- */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-white">Risk Limits Configuration</h2>
          <p className="text-[10px] text-slate-500 mt-0.5">Per-strategy and global risk caps</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`qr-chip ${statusChip.cls}`}>{statusChip.text}</span>
          <button onClick={saveGlobal} disabled={saving} className="qr-btn qr-btn-primary">
            {saving ? 'Saving...' : saved ? 'Saved' : 'Save All'}
          </button>
        </div>
      </div>

      {/* ---- Presets ---- */}
      <div className="qr-surface px-3 py-2.5 flex items-center gap-3">
        <span className="qr-label">Presets</span>
        {Object.entries(PRESETS).map(([key, preset]) => (
          <button
            key={key}
            onClick={() => applyPreset(key)}
            className="qr-btn qr-btn-ghost"
          >
            {preset.label}
          </button>
        ))}
        <span className="text-[10px] text-slate-500 ml-auto">Click a preset to fill values, then Save</span>
      </div>

      {/* ---- Global Risk Limits ---- */}
      <div className="qr-surface overflow-hidden">
        <div className="px-3 py-2 border-b border-white/[0.05]">
          <span className="qr-label">Global Risk Limits</span>
        </div>
        <div className="p-3">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {GLOBAL_FIELDS.map(f => (
              <div key={f.key} className="flex flex-col gap-1 px-2.5 py-2 rounded-md bg-slate-800/40 ring-1 ring-white/[0.04]">
                <span className="text-[10px] text-slate-500">{f.label}</span>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    className={`${inputCls} w-full`}
                    value={globalLimits[f.key]}
                    onChange={e => setGlobalLimits(prev => ({ ...prev, [f.key]: parseFloat(e.target.value) || 0 }))}
                  />
                  {f.unit && <span className="text-[10px] text-slate-600 whitespace-nowrap">{f.unit}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ---- Per-Strategy Overrides ---- */}
      <div className="qr-surface overflow-hidden">
        <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
          <span className="qr-label">Per-Strategy Overrides</span>
          <span className="text-[10px] text-slate-500">{strategies.length} strategies -- click value to edit</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-[10px] text-slate-500 uppercase border-b border-white/[0.04]">
                <th className="text-left px-3 py-2 font-medium">Strategy</th>
                <th className="text-right px-3 py-2 font-medium">Max Position %</th>
                <th className="text-right px-3 py-2 font-medium">Max Daily Loss %</th>
                <th className="text-center px-3 py-2 font-medium">Enabled</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {strategies.map(s => {
                const sid = s.strategy_id;
                const enabled = getOverride(sid, 'enabled') ?? true;
                return (
                  <tr key={sid} className={`qr-tr-hover ${!enabled ? 'opacity-40' : ''}`}>
                    <td className="px-3 py-1.5">
                      <span className="text-xs text-white font-medium">{s.strategy_name || sid}</span>
                      <span className="text-[10px] text-slate-600 ml-2">{sid}</span>
                    </td>
                    <td className="px-3 py-1.5 text-right">
                      <EditableCell
                        value={getOverride(sid, 'max_position_pct')}
                        onSave={v => setOverride(sid, 'max_position_pct', v)}
                        suffix="%"
                        placeholder={`${globalLimits.risk_max_position_pct}% (global)`}
                      />
                    </td>
                    <td className="px-3 py-1.5 text-right">
                      <EditableCell
                        value={getOverride(sid, 'max_daily_loss_pct')}
                        onSave={v => setOverride(sid, 'max_daily_loss_pct', v)}
                        suffix="%"
                        placeholder={`${globalLimits.risk_max_daily_loss_pct}% (global)`}
                      />
                    </td>
                    <td className="px-3 py-1.5 text-center">
                      <div className="flex justify-center">
                        <Toggle on={enabled} onChange={v => setOverride(sid, 'enabled', v)} />
                      </div>
                    </td>
                  </tr>
                );
              })}
              {strategies.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-3 py-4 text-center text-[11px] text-slate-600">
                    No strategies found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ---- Current Risk Status ---- */}
      <div className="qr-surface overflow-hidden">
        <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="qr-label">Current Risk Status</span>
            <span className={`qr-chip ${statusChip.cls}`}>{statusChip.text}</span>
          </div>
          <span className="qr-num text-[10px] text-slate-500">
            {alertsByLevel.total} alert{alertsByLevel.total !== 1 ? 's' : ''} active
          </span>
        </div>
        <div className="p-3">
          {/* Summary metrics */}
          {riskSummary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
              <div className="px-2.5 py-2 rounded-md bg-slate-800/40 ring-1 ring-white/[0.04]">
                <span className="text-[10px] text-slate-500 block">Invested</span>
                <span className="qr-num text-xs text-white">{fmtK(riskSummary.total_invested)}</span>
              </div>
              <div className="px-2.5 py-2 rounded-md bg-slate-800/40 ring-1 ring-white/[0.04]">
                <span className="text-[10px] text-slate-500 block">Unrealized P&L</span>
                <span className={`qr-num text-xs ${pnlCl(riskSummary.total_unrealized_pnl)}`}>
                  {fmtK(riskSummary.total_unrealized_pnl)}
                </span>
              </div>
              <div className="px-2.5 py-2 rounded-md bg-slate-800/40 ring-1 ring-white/[0.04]">
                <span className="text-[10px] text-slate-500 block">Active Positions</span>
                <span className="qr-num text-xs text-white">{riskSummary.active_positions ?? '--'}</span>
              </div>
              <div className="px-2.5 py-2 rounded-md bg-slate-800/40 ring-1 ring-white/[0.04]">
                <span className="text-[10px] text-slate-500 block">Net Exposure</span>
                <span className="qr-num text-xs text-white">{fmtK(riskSummary.net_exposure)}</span>
              </div>
            </div>
          )}

          {/* Active alerts */}
          {alerts.length > 0 ? (
            <div className="space-y-1">
              {alerts.map((a, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-2 px-2.5 py-1.5 rounded-md ring-1 ${
                    a.level === 'critical'
                      ? 'bg-rose-500/5 ring-rose-500/20'
                      : 'bg-amber-500/5 ring-amber-500/20'
                  }`}
                >
                  <span className={`mt-0.5 inline-flex items-center justify-center w-4 h-4 rounded-full text-[9px] font-bold ${
                    a.level === 'critical'
                      ? 'bg-rose-500/20 text-rose-300'
                      : 'bg-amber-500/20 text-amber-300'
                  }`}>
                    !
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="text-[11px] text-white font-semibold">
                      {a.type?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    </div>
                    <div className="text-[10px] text-slate-400">{a.message}</div>
                  </div>
                  <span className={`qr-chip text-[9px] ${
                    a.level === 'critical' ? 'qr-chip-rose' : 'qr-chip-amber'
                  }`}>
                    {a.level}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-2 px-2.5 py-2 rounded-md bg-emerald-500/5 ring-1 ring-emerald-500/15">
              <span className="inline-flex items-center justify-center w-4 h-4 rounded-full text-[9px] font-bold bg-emerald-500/20 text-emerald-300">
                OK
              </span>
              <span className="text-[11px] text-emerald-300">All risk metrics within configured limits</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RiskLimitsConfig;
