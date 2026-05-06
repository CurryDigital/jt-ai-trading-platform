import React, { useState, useEffect } from 'react';
import { api, fmtAge } from '../utils';

const STATUS_COLORS = {
  pending: 'qr-chip-slate',
  assigned_algo: 'qr-chip-blue',
  claimed_algo: 'qr-chip-blue',
  in_progress_algo: 'qr-chip-blue',
  algo_complete: 'qr-chip-amber',
  assigned_qa: 'qr-chip-amber',
  claimed_qa: 'qr-chip-amber',
  qa_approved: 'qr-chip-emerald',
  qa_rejected: 'qr-chip-rose',
  golden: 'qr-chip-amber',
  rejected: 'qr-chip-rose',
};

const sharpeColor = (v) => {
  if (v == null || isNaN(v)) return 'text-slate-500';
  if (v > 1.5) return 'text-emerald-400';
  if (v > 1.0) return 'text-amber-400';
  return 'text-rose-400';
};

const sharpeChip = (v) => {
  if (v == null || isNaN(v)) return 'qr-chip-slate';
  if (v > 1.5) return 'qr-chip-emerald';
  if (v > 1.0) return 'qr-chip-amber';
  return 'qr-chip-rose';
};

const ddColor = (v) => {
  if (v == null || isNaN(v)) return 'text-slate-500';
  if (v > -0.10) return 'text-emerald-400';
  if (v > -0.20) return 'text-amber-400';
  return 'text-rose-400';
};

const EVENT_COLORS = {
  'strategy.created': 'bg-emerald-500',
  'experiment.started': 'bg-blue-500',
  'dataset.ready': 'bg-cyan-500',
  'backtest.completed': 'bg-violet-500',
  'risk.evaluated': 'bg-amber-500',
  'debate.completed': 'bg-rose-500',
  'qa.validated': 'bg-emerald-500',
  'strategy.promoted': 'bg-amber-500',
};

const EVENT_CHIP_COLORS = {
  'strategy.created': 'qr-chip-emerald',
  'experiment.started': 'qr-chip-blue',
  'dataset.ready': 'qr-chip-blue',
  'backtest.completed': 'qr-chip-blue',
  'risk.evaluated': 'qr-chip-amber',
  'debate.completed': 'qr-chip-rose',
  'qa.validated': 'qr-chip-emerald',
  'strategy.promoted': 'qr-chip-amber',
};

const fmtPctVal = (v) => {
  if (v == null || isNaN(v)) return '--';
  return `${(v * 100).toFixed(1)}%`;
};

export const StrategyLineage = ({ strategyId, onBack }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!strategyId) return;
    setLoading(true);
    setError(null);
    api.get(`/api/agents/strategy/${strategyId}`).then(res => {
      if (!res) {
        setError('Failed to load strategy data');
        setData(null);
      } else {
        setData(res);
      }
      setLoading(false);
    });
  }, [strategyId]);

  if (loading) {
    return (
      <div className="qr-surface p-6 text-center">
        <div className="text-[11px] text-slate-500 animate-pulse">Loading strategy lineage...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="qr-surface p-6">
        {onBack && (
          <button onClick={onBack} className="qr-btn-ghost text-[11px] mb-3">
            &larr; Back
          </button>
        )}
        <div className="text-[11px] text-rose-400">{error}</div>
      </div>
    );
  }

  const workflow = data?.workflow;
  const events = data?.events || [];
  const lineage = data?.lineage || [];

  // Find best experiment by sharpe_oos
  const bestExpId = lineage.length > 0
    ? lineage.reduce((best, exp) =>
        (exp.sharpe_oos ?? -Infinity) > (best.sharpe_oos ?? -Infinity) ? exp : best
      , lineage[0]).experiment_id
    : null;

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="qr-surface p-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {onBack && (
              <button onClick={onBack} className="qr-btn-ghost text-[11px]">
                &larr;
              </button>
            )}
            <div>
              <div className="text-sm font-bold text-white">
                {workflow?.strategy_id || strategyId}
                {workflow?.name ? ` - ${workflow.name}` : ''}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">Strategy Lineage</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {workflow?.assigned_agent && (
              <span className="qr-chip qr-chip-blue text-[10px]">
                {workflow.assigned_agent}
              </span>
            )}
            {workflow?.status && (
              <span className={`qr-chip ${STATUS_COLORS[workflow.status] || 'qr-chip-slate'} text-[10px]`}>
                {workflow.status.replace(/_/g, ' ')}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Events Timeline */}
      {events.length > 0 && (
        <div className="qr-surface p-3">
          <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-2 font-semibold">
            Agent Events
          </div>
          <div className="relative ml-3">
            {/* Vertical line */}
            <div className="absolute left-0 top-1 bottom-1 border-l-2 border-slate-700" />
            <div className="space-y-2">
              {events.map((evt, i) => {
                const dotColor = EVENT_COLORS[evt.event_type] || 'bg-slate-500';
                const chipColor = EVENT_CHIP_COLORS[evt.event_type] || 'qr-chip-slate';
                return (
                  <div key={i} className="relative pl-5 flex items-start gap-2 min-h-[24px]">
                    {/* Node dot */}
                    <div className={`absolute left-[-5px] top-[5px] w-[10px] h-[10px] rounded-full ${dotColor} border-2 border-slate-900`} />
                    <div className="flex-1 flex items-center gap-2 flex-wrap">
                      {evt.agent_icon && (
                        <span className="text-[12px]" title={evt.agent_name}>{evt.agent_icon}</span>
                      )}
                      {evt.agent_name && (
                        <span className="text-[11px] text-slate-300 font-medium">
                          {evt.agent_name}
                        </span>
                      )}
                      <span className={`qr-chip ${chipColor} text-[9px]`}>
                        {evt.event_type}
                      </span>
                    </div>
                    <span className="text-[10px] text-slate-600 whitespace-nowrap flex-shrink-0">
                      {fmtAge(evt.timestamp)}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Lineage Experiments */}
      {lineage.length > 0 ? (
        <div className="qr-surface p-3">
          <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-2 font-semibold">
            Experiment Lineage
            <span className="ml-2 text-slate-600">{lineage.length} runs</span>
          </div>
          <div className="overflow-x-auto no-scrollbar">
            <div className="flex gap-2 min-w-max pb-1">
              {lineage.map((exp) => {
                const isBest = exp.experiment_id === bestExpId;
                return (
                  <div
                    key={exp.experiment_id}
                    className={`flex-shrink-0 w-44 rounded border p-2 ${
                      isBest
                        ? 'border-emerald-500/50 bg-emerald-500/5'
                        : 'border-slate-700/50 bg-slate-800/30'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[11px] text-white font-bold truncate">
                        {exp.experiment_id}
                      </span>
                      {isBest && (
                        <span className="qr-chip qr-chip-emerald text-[8px]">BEST</span>
                      )}
                    </div>

                    {/* Sharpe */}
                    <div className="flex justify-between items-baseline mb-1">
                      <span className="qr-label">Sharpe OOS</span>
                      <span className={`qr-num text-[13px] font-bold ${sharpeColor(exp.sharpe_oos)}`}>
                        {exp.sharpe_oos != null ? Number(exp.sharpe_oos).toFixed(2) : '--'}
                      </span>
                    </div>

                    {/* Max Drawdown */}
                    <div className="flex justify-between items-baseline mb-1">
                      <span className="qr-label">Max DD</span>
                      <span className={`qr-num text-[11px] ${ddColor(exp.max_drawdown)}`}>
                        {exp.max_drawdown != null ? fmtPctVal(exp.max_drawdown) : '--'}
                      </span>
                    </div>

                    {/* Trade Count */}
                    <div className="flex justify-between items-baseline mb-1.5">
                      <span className="qr-label">Trades OOS</span>
                      <span className="qr-num text-[11px] text-slate-300">
                        {exp.trade_count_oos ?? '--'}
                      </span>
                    </div>

                    {/* Meta row */}
                    <div className="border-t border-slate-700/50 pt-1 space-y-0.5">
                      {exp.dataset_version && (
                        <div className="flex justify-between">
                          <span className="text-[9px] text-slate-600">Dataset</span>
                          <span className="text-[9px] text-slate-400">{exp.dataset_version}</span>
                        </div>
                      )}
                      {exp.engine_version && (
                        <div className="flex justify-between">
                          <span className="text-[9px] text-slate-600">Engine</span>
                          <span className="text-[9px] text-slate-400">{exp.engine_version}</span>
                        </div>
                      )}
                      {exp.created_at && (
                        <div className="flex justify-between">
                          <span className="text-[9px] text-slate-600">Age</span>
                          <span className="text-[9px] text-slate-500">{fmtAge(exp.created_at)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        <div className="qr-surface p-3">
          <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-2 font-semibold">
            Experiment Lineage
          </div>
          <div className="text-[11px] text-slate-600 text-center py-4">
            No lineage data available -- experiment tables may not be initialized
          </div>
        </div>
      )}
    </div>
  );
};

export default StrategyLineage;
