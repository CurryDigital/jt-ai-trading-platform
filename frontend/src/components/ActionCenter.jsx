import React, { useMemo, useState } from 'react';
import { api, usePoll, fmtK, fmtAge } from '../utils';
import { useBarQuality, barQualityView } from '../freshness';

// Action Center — the merged attention queue (alerts, data quality,
// approvals/gates). Moved off the Command home page into the Settings tab
// (2026-09-18 redesign) as its own section; self-fetches /api/command/overview
// so it mounts standalone. Items: strategy risks + monitoring gap + platform
// alerts, sorted by severity then recency, with server-side ack/snooze.

// Restrained palette: colour carries meaning only.
//   rose  = critical severity   emerald/rose text = signed P&L
//   blue  = interactive links   everything else = neutral slate/white
const SEV_STYLE = {
  critical: { border: 'border-l-rose-500', bg: 'bg-rose-500/[0.06]', tag: 'text-rose-300 bg-rose-500/15' },
  warning:  { border: 'border-l-slate-500', bg: '', tag: 'text-slate-300 bg-white/[0.07]' },
  info:     { border: 'border-l-slate-700', bg: '', tag: 'text-slate-400 bg-white/[0.05]' },
};
const SEV_RANK = { critical: 0, warning: 1, info: 2 };
const ACT_LABEL = { reconnect: 'Reconnect', flatten: 'Flatten', open: 'Open' };

export const ActionCenter = ({ navigateToTab, onSelectStrategy }) => {
  const [overview, setOverview] = useState(null);
  const barQ = useBarQuality();
  const bqView = barQualityView(barQ.loaded, barQ.bq);

  usePoll(async () => {
    const res = await api.get('/api/command/overview');
    if (res) setOverview(res);
  }, 60000);

  const strategyRisks = useMemo(() => overview?.strategy_risks || [], [overview]);
  const monitoringGap = overview?.monitoring_gap || 0;

  // Merged attention queue: strategy risks + monitoring gap + platform items
  // in ONE panel, sorted by severity then recency. Every item carries a
  // stable ackKey for server-side ack/snooze, a real action verb, and a
  // dedup class so same-class rows collapse to one.
  const attentionItems = useMemo(() => {
    const items = [];
    for (const s of strategyRisks) items.push({
      kind: 'risk', sev: s.sev, tag: 'RISK', title: s.name,
      triggers: s.triggers || null,
      fullMetrics: `PF ${s.paper_pf != null ? s.paper_pf.toFixed(2) : '—'} · P&L ${s.paper_pnl >= 0 ? '+' : ''}${fmtK(s.paper_pnl)} · WR ${s.paper_wr}% · ${s.closed_trades} closed`,
      impact: `PF ${s.paper_pf != null ? s.paper_pf.toFixed(2) : '—'} · P&L ${s.paper_pnl >= 0 ? '+' : ''}${fmtK(s.paper_pnl)} · WR ${s.paper_wr}% · ${s.closed_trades} closed`,
      ts: null, age: null, strategyId: s.strategy_id, action: 'open',
      key: `risk-${s.strategy_id}`, ackKey: `risk:${s.strategy_id}`,
    });
    if (monitoringGap > 0) items.push({
      kind: 'gap', sev: 'info', tag: 'GAPS',
      title: `${monitoringGap} paper strateg${monitoringGap === 1 ? 'y' : 'ies'} not actively monitored`,
      impact: 'Registry says PAPER but no ACTIVE paper deployment — no live signal tracking running.',
      ts: null, age: null, target: 'strategies', action: 'open', key: 'gap', ackKey: 'gap:monitoring',
    });
    for (const a of (overview?.attention || [])) {
      const raw = a.created_at;
      const ts = raw ? new Date(/Z|[+-]\d{2}:?\d{2}$/.test(raw) ? raw : raw + 'Z').getTime() : null;
      items.push({
        kind: 'platform', sev: a.sev, tag: a.tag, title: a.title, impact: a.impact,
        ts, age: a.age || fmtAge(a.created_at), target: a.target,
        action: a.action || 'open', refId: a.ref_id,
        key: `plat-${a.id || a.ref_id || a.title}`, ackKey: a.id ? String(a.id) : null,
      });
    }
    // Yahoo suspect-bar guard (bar_quality, t_285be732): YELLOW is a SOFT
    // warning — never critical, episodes can self-heal as Yahoo backfills
    // real bars. Client-side item (no ackKey → not dismissible; it clears
    // itself when the 30d window heals). UNKNOWN/null is NOT surfaced here —
    // the Settings badge carries that state; the queue stays for real signal.
    if (bqView.level === 'YELLOW') {
      const bq = barQ.bq || {};
      const tickers = bq.recent_30d_tickers || [];
      items.push({
        kind: 'platform', sev: 'warning', tag: 'DATA',
        title: `Yahoo suspect bars — ${tickers.join(', ') || 'unknown tickers'}`,
        impact: `${bq.recent_30d_rows ?? 0} unresolved synthetic zero-volume flat-bar suspects in 30d (latest ${bq.latest_suspect_date ?? '—'}): ${bq.recent_30d_gold_rows ?? 0} pre-guard gold rows + ${bq.recent_30d_quarantined_rows ?? 0} quarantined post-guard. Soft warning — can self-heal as Yahoo backfills. Source: gold.v_us_equity_bar_quality (qr_etl).`,
        ts: null, age: null, target: 'settings', action: 'open',
        key: 'bar-quality', ackKey: null,
      });
    }
    items.sort((x, y) => (SEV_RANK[x.sev] ?? 9) - (SEV_RANK[y.sev] ?? 9) || (y.ts ?? -1) - (x.ts ?? -1));
    return items;
  }, [overview, strategyRisks, monitoringGap, bqView.level, barQ.bq]);

  // Server-side dismissals filter the payload already; this set is the
  // optimistic local removal after the user acks/snoozes in THIS session.
  const [dismissed, setDismissed] = useState(() => new Set());
  const [actBusy, setActBusy] = useState(null);   // ackKey currently executing
  const [actMsg, setActMsg] = useState(null);     // {ackKey, ok, text}
  const visibleItems = useMemo(
    () => attentionItems.filter(a => !a.ackKey || !dismissed.has(a.ackKey)),
    [attentionItems, dismissed],
  );

  // Dedup by class: '<source> feed is stale' rows collapse into one group row
  // with a disclosure triangle; other classes stay individual.
  const alertClass = (a) =>
    (a.kind === 'platform' && / feed is stale$/i.test(a.title)) ? 'feed-stale' : `solo:${a.key}`;
  const attentionGroups = useMemo(() => {
    const order = [], byClass = new Map();
    for (const a of visibleItems) {
      const k = alertClass(a);
      if (!byClass.has(k)) { byClass.set(k, []); order.push(k); }
      byClass.get(k).push(a);
    }
    return order.map(k => byClass.get(k));
  }, [visibleItems]);
  const [openGroups, setOpenGroups] = useState(() => new Set());
  const toggleGroup = (k) => setOpenGroups(prev => {
    const n = new Set(prev);
    n.has(k) ? n.delete(k) : n.add(k);
    return n;
  });

  const dismissAlert = async (targets, action) => {
    const keys = targets.map(a => a.ackKey).filter(Boolean);
    if (!keys.length) return;
    for (const k of keys) {
      await api.post('/api/command/alerts/ack', { alert_key: k, action, snooze_minutes: 60 });
    }
    setDismissed(prev => new Set([...prev, ...keys]));
  };

  const runAction = async (a) => {
    if (a.action === 'reconnect') {
      setActBusy(a.ackKey || a.key);
      const res = await api.post('/api/ib/tws/connect', {});
      setActBusy(null);
      setActMsg({ key: a.ackKey || a.key, ok: !!(res && res.success !== false), text: res && (res.message || res.status) ? String(res.message || res.status) : (res ? 'connect requested' : 'request failed') });
      return;
    }
    if (a.strategyId) onSelectStrategy?.(a.strategyId);
    else navigateToTab?.(a.target || 'command');
  };

  const sevCounts = visibleItems.reduce((m, a) => ({ ...m, [a.sev]: (m[a.sev] || 0) + 1 }), {});

  return (
    <div className="qr-surface overflow-hidden" id="action-center">
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-white/[0.05]">
        <span className="qr-label">Action Center</span>
        <span className="flex items-center gap-2 whitespace-nowrap">
          {/* Bar-quality badge (bar_quality from /api/system/freshness).
              Always rendered so UNKNOWN/PENDING are visible — never
              silently treated as GREEN. */}
          <span className={`text-[9px] font-bold ${bqView.badgeCl}`} title={bqView.tip}>
            Bar quality {bqView.label}
          </span>
          {sevCounts.critical > 0 && <span className="text-[9px] font-bold text-rose-400">{sevCounts.critical} critical</span>}
          {sevCounts.warning > 0 && <span className="text-[9px] font-bold text-slate-400">{sevCounts.warning} warning</span>}
          {sevCounts.info > 0 && <span className="text-[9px] text-slate-500">{sevCounts.info} info</span>}
          {visibleItems.length === 0 && <span className="text-[9px] text-slate-500">clear</span>}
        </span>
      </div>
      {attentionGroups.map((group, gi) => {
        const lead = group[0];
        const isCrit = lead.sev === 'critical';
        const sv = SEV_STYLE[lead.sev] || SEV_STYLE.info;
        const grouped = group.length > 1;
        const gKey = grouped ? alertClass(lead) : null;
        const expanded = gKey != null && openGroups.has(gKey);
        const leadId = lead.ackKey || lead.key;
        const groupTitle = grouped && gKey === 'feed-stale'
          ? `${group.length} feeds stale — ${group.map(a => a.refId || a.title).join(', ')}`
          : lead.title;
        return (
          <div key={gKey || lead.key} className={gi > 0 ? 'border-t border-t-white/[0.05]' : ''}>
            <div className={`flex items-center gap-3 px-3 ${isCrit ? 'py-3 border-l-4' : 'py-2 border-l-2'} ${sv.border} ${sv.bg}`}>
              {grouped && (
                <button onClick={() => toggleGroup(gKey)} className="flex-none w-3 text-[10px] text-slate-500 hover:text-slate-300" title="Show individual alerts">{expanded ? '▾' : '▸'}</button>
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`text-[8px] font-black tracking-wide px-1.5 py-0.5 rounded ${sv.tag}`}>{lead.tag}</span>
                  <button onClick={() => grouped ? toggleGroup(gKey) : runAction(lead)} className={`${isCrit ? 'text-[13px]' : 'text-[12px]'} font-bold text-white truncate hover:opacity-80 text-left`}>{groupTitle}</button>
                </div>
                {lead.kind === 'risk' && lead.triggers && lead.triggers.length > 0 ? (
                  <div className="flex items-center gap-1 mt-1 flex-wrap" title={lead.fullMetrics}>
                    {lead.triggers.map(t => (
                      <span key={t} className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-white/[0.06] text-slate-300">{t}</span>
                    ))}
                  </div>
                ) : (
                  <div className={`${isCrit ? 'text-[11px]' : 'text-[10px]'} text-slate-500 mt-0.5 truncate`} title={lead.impact}>{lead.impact}</div>
                )}
                {actMsg && actMsg.key === leadId && (
                  <div className={`text-[9px] font-mono mt-0.5 ${actMsg.ok ? 'text-teal-400' : 'text-rose-400'}`}>{actMsg.text}</div>
                )}
              </div>
              <span className="font-mono text-[10px] text-slate-600 flex-none">{lead.age || '—'}</span>
              <div className="flex-none flex items-center gap-1">
                <button onClick={() => runAction(lead)} disabled={actBusy === leadId}
                  className="text-[10px] font-bold px-2.5 py-1 rounded bg-white/[0.06] hover:bg-white/[0.1] text-slate-200 disabled:opacity-50">
                  {actBusy === leadId ? '…' : (ACT_LABEL[lead.action] || 'Open')}
                </button>
                {lead.ackKey && (
                  <>
                    <button onClick={() => dismissAlert(group, 'acknowledge')} title="Acknowledge — persists server-side (actor + timestamp)"
                      className="text-[9px] px-1.5 py-1 rounded text-slate-500 hover:text-slate-300 hover:bg-white/[0.05]">Ack</button>
                    <button onClick={() => dismissAlert(group, 'snooze')} title="Snooze 1h — persists server-side, auto-returns"
                      className="text-[9px] px-1.5 py-1 rounded text-slate-500 hover:text-slate-300 hover:bg-white/[0.05]">Snooze 1h</button>
                  </>
                )}
              </div>
            </div>
            {grouped && expanded && group.map(m => {
              const mid = m.ackKey || m.key;
              return (
                <div key={m.key} className="flex items-center gap-3 py-1.5 px-3 pl-8 border-l-2 border-l-white/[0.08]">
                  <div className="flex-1 min-w-0">
                    <div className="text-[11px] font-mono text-slate-300 truncate">{m.title}</div>
                    <div className="text-[9px] text-slate-600 truncate" title={m.impact}>{m.impact}</div>
                  </div>
                  <span className="font-mono text-[9px] text-slate-600 flex-none">{m.age || '—'}</span>
                  <button onClick={() => runAction(m)} className="flex-none text-[9px] font-bold px-2 py-0.5 rounded bg-white/[0.05] hover:bg-white/[0.09] text-slate-300">{ACT_LABEL[m.action] || 'Open'}</button>
                  {m.ackKey && <button onClick={() => dismissAlert([m], 'acknowledge')} className="flex-none text-[9px] px-1.5 py-0.5 rounded text-slate-600 hover:text-slate-300">Ack</button>}
                </div>
              );
            })}
          </div>
        );
      })}
      {visibleItems.length === 0 && (
        <div className="py-6 text-center text-[11px] text-slate-600">Nothing needs attention right now</div>
      )}
    </div>
  );
};

export default ActionCenter;
