import React from 'react';
import { STATUS_COLORS, formatTimeAgo } from './utils';

function ScoreBar({ label, value, max = 10 }) {
  if (value == null) return null;
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const color = value >= 7 ? 'bg-emerald-500' : value >= 4 ? 'bg-amber-500' : 'bg-rose-500';
  return (
    <div className="mb-2">
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-[9px] text-slate-500">{label}</span>
        <span className="text-[9px] text-white font-mono">{value.toFixed(1)}</span>
      </div>
      <div className="w-full h-1 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function StrategyDetail({ strategyId, onClose }) {
  const [detail, setDetail] = React.useState(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    setLoading(true);
    fetch(`/api/agents/strategy/${encodeURIComponent(strategyId)}`)
      .then(r => r.json())
      .then(data => { setDetail(data); setLoading(false); })
      .catch(() => { setDetail(null); setLoading(false); });
  }, [strategyId]);

  if (loading) {
    return (
      <div className="p-6 text-center text-slate-500">
        <div className="w-6 h-6 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto mb-2" />
        Loading strategy...
      </div>
    );
  }

  if (!detail || !detail.workflow) {
    return <div className="p-6 text-center text-slate-500">Strategy not found</div>;
  }

  const wf = detail.workflow;
  const statusClass = STATUS_COLORS[wf.status] || STATUS_COLORS.pending;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-white">{wf.name || wf.strategy_id}</h3>
          <p className="text-[10px] text-slate-500 font-mono">{wf.strategy_id}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[10px] px-2 py-1 rounded font-bold uppercase ${statusClass}`}>{wf.status}</span>
          <button onClick={onClose} className="text-slate-500 hover:text-white text-sm px-2">✕</button>
        </div>
      </div>

      {wf.thesis && <p className="text-xs text-slate-400">{wf.thesis}</p>}

      {/* Meta */}
      <div className="grid grid-cols-2 gap-3 text-[10px] text-slate-400">
        {wf.asset_class && <div><span className="text-slate-600">Asset:</span> {wf.asset_class}</div>}
        {wf.source && <div><span className="text-slate-600">Source:</span> {wf.source}</div>}
        {wf.generation != null && <div><span className="text-slate-600">Gen:</span> {wf.generation}</div>}
        {wf.parent_strategy_id && <div><span className="text-slate-600">Parent:</span> {wf.parent_strategy_id}</div>}
      </div>

      {/* Entry / Exit */}
      {(wf.entry_logic || wf.exit_logic) && (
        <div className="bg-slate-800/50 rounded-lg p-3 space-y-2">
          {wf.entry_logic && (
            <div>
              <div className="text-[9px] text-slate-500 uppercase mb-0.5">Entry Logic</div>
              <p className="text-[11px] text-slate-300">{wf.entry_logic}</p>
            </div>
          )}
          {wf.exit_logic && (
            <div>
              <div className="text-[9px] text-slate-500 uppercase mb-0.5">Exit Logic</div>
              <p className="text-[11px] text-slate-300">{wf.exit_logic}</p>
            </div>
          )}
        </div>
      )}

      {/* Backtests */}
      {detail.backtests && detail.backtests.length > 0 && (
        <div>
          <div className="text-[10px] text-slate-500 uppercase font-bold mb-2">Backtests ({detail.backtests.length})</div>
          <div className="space-y-2 max-h-[300px] overflow-y-auto">
            {detail.backtests.map((bt, i) => (
              <div key={i} className="bg-slate-800/50 rounded-lg p-3 text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-white font-mono font-bold">Run #{bt.run_number}</span>
                  <span className="text-[10px] text-slate-600">{formatTimeAgo(bt.created_at)}</span>
                </div>
                <div className="flex flex-wrap gap-3 text-[10px] text-slate-400">
                  {bt.sharpe_oos != null && <span>Sharpe OOS: <span className="text-white font-mono">{bt.sharpe_oos.toFixed(2)}</span></span>}
                  {bt.sharpe_is != null && <span>Sharpe IS: <span className="text-slate-300 font-mono">{bt.sharpe_is.toFixed(2)}</span></span>}
                  {bt.max_drawdown_oos != null && <span>Max DD: <span className="text-rose-400 font-mono">{(bt.max_drawdown_oos * 100).toFixed(1)}%</span></span>}
                  {bt.trade_count_oos != null && <span>Trades: <span className="text-white font-mono">{bt.trade_count_oos}</span></span>}
                  {bt.win_rate_oos != null && <span>Win Rate: <span className="text-emerald-400 font-mono">{(bt.win_rate_oos * 100).toFixed(1)}%</span></span>}
                </div>
                {bt.all_gates_passed != null && (
                  <div className={`text-[9px] mt-1 ${bt.all_gates_passed ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {bt.all_gates_passed ? '✅ All gates passed' : '❌ Some gates failed'}
                  </div>
                )}
                {bt.notes && <p className="text-[9px] text-slate-600 mt-1">{bt.notes}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* QA Reviews */}
      {detail.qa_reviews && detail.qa_reviews.length > 0 && (
        <div>
          <div className="text-[10px] text-slate-500 uppercase font-bold mb-2">QA Reviews ({detail.qa_reviews.length})</div>
          <div className="space-y-2">
            {detail.qa_reviews.map((q, i) => (
              <div key={i} className="bg-slate-800/50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${q.decision === 'APPROVED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                    {q.decision}
                  </span>
                  <span className="text-[10px] text-slate-600">{q.reviewed_by} • {formatTimeAgo(q.reviewed_at)}</span>
                </div>
                {q.conviction_score != null && (
                  <ScoreBar label="Conviction" value={q.conviction_score} />
                )}
                {q.scores && (
                  <div className="grid grid-cols-2 gap-x-3 mt-2">
                    <ScoreBar label="Sharpe Stability" value={q.scores.sharpe_stability} />
                    <ScoreBar label="Trade Count" value={q.scores.trade_count} />
                    <ScoreBar label="Drawdown" value={q.scores.drawdown} />
                    <ScoreBar label="Regime" value={q.scores.regime} />
                  </div>
                )}
                {q.comment && <p className="text-[10px] text-slate-400 mt-2">{q.comment}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Reviews */}
      {detail.risk_reviews && detail.risk_reviews.length > 0 && (
        <div>
          <div className="text-[10px] text-slate-500 uppercase font-bold mb-2">Risk Reviews ({detail.risk_reviews.length})</div>
          <div className="space-y-2">
            {detail.risk_reviews.map((r, i) => (
              <div key={i} className="bg-slate-800/50 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${r.decision === 'APPROVED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                    {r.decision}
                  </span>
                  <span className="text-[10px] text-slate-600">{r.reviewed_by} • {formatTimeAgo(r.reviewed_at)}</span>
                </div>
                {r.risk_score != null && (
                  <div className="mb-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] text-slate-500 uppercase">Risk Score</span>
                      <span className={`text-lg font-bold font-mono ${r.risk_score > 7 ? 'text-rose-400' : r.risk_score > 4 ? 'text-amber-400' : 'text-emerald-400'}`}>
                        {r.risk_score.toFixed(1)}
                      </span>
                    </div>
                  </div>
                )}
                {r.suggested_fixes && (
                  <div className="text-[10px] text-amber-400 mt-1">Fixes: {r.suggested_fixes}</div>
                )}
                {r.comment && <p className="text-[10px] text-slate-400 mt-1">{r.comment}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
