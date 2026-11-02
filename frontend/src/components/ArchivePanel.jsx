import React, { useState, useMemo } from 'react';
import { Chip, fmtK } from './jtkit';
import { fracToPct } from './strategyProfiles';

// Performance Archive (PORTFOLIO-PRUNE-1, 2026-11-02): first-class registry
// view of archived books — evidence record, not a trash bin. Data:
// GET /api/strategies/archive (gold.strategy_registry rows stamped
// PORTFOLIO-PRUNE-1, parsed reason tag + open-leg runoff state from
// gold.paper_trades_synthetic). No restore action is exposed by design:
// revival requires a fresh pre-reg ID + operator approval.

const REASON_LABEL = {
  OVERFIT_REJECTED: 'Overfit — rejected',
  WEAK_EVIDENCE: 'Weak evidence',
  INSUFFICIENT_EVIDENCE: 'Insufficient evidence',
  REGIME_FRAGILE: 'Regime fragile',
  SUPERSEDED_BY_MULTI_ASSET: 'Superseded by multi-asset',
  DATA_BLOCKED_SURVIVORSHIP: 'Data blocked — survivorship',
};

const fmtPct1 = (v) => (v == null ? '—' : `${v >= 0 ? '+' : ''}${Number(v).toFixed(1)}%`);
// Ledger floats arrive with binary noise (35.20000076); trim to 4dp max.
const fmtNum = (v) => (v == null ? '—' : String(+Number(v).toFixed(4)));

function EvidenceMetric({ label, value, tip, sub }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }} title={tip || undefined}>
      <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}>{label}</span>
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 700, color: 'var(--text-secondary)' }}>{value}</span>
      {sub && <span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, color: 'var(--text-faint)' }}>{sub}</span>}
    </div>
  );
}

function ArchiveCard({ a, onOpen }) {
  const e = a.evidence || {};
  const oosWin = e.oos_start && e.oos_end ? `${String(e.oos_start).slice(0, 7)}→${String(e.oos_end).slice(0, 7)}` : null;
  const hasOpen = (a.open_count || 0) > 0;
  const posLine = hasOpen
    ? `${a.open_count} open leg${a.open_count === 1 ? '' : 's'} — ${(a.open_positions || []).map((p) => `${p.ticker} ${fmtNum(p.n_shares)}sh @ ${fmtNum(p.entry_price)} (${p.entry_date})`).join(', ')}`
    : 'FLAT';
  return (
    <div className="jt-surface" style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
      {hasOpen && (
        <div style={{
          padding: '6px 8px', borderRadius: 'var(--radius-sm)', fontSize: 9, lineHeight: 1.4,
          color: '#fda4af', background: 'rgba(244,63,94,0.08)', borderLeft: '3px solid rgba(244,63,94,0.55)',
        }}>
          Retired — managing existing position to{a.scheduled_exit ? ` scheduled exit ~${a.scheduled_exit}` : ' a rule-consistent exit'}; no new entries.
          <div style={{ color: 'var(--text-muted)', marginTop: 2 }}>{posLine}</div>
        </div>
      )}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ minWidth: 0, cursor: onOpen ? 'pointer' : 'default' }} onClick={() => onOpen && onOpen(a.id)} title="Open strategy detail — history and audit trail preserved">
          <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-strong)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{a.name}</div>
          <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 3 }}>
            {a.asset_class || '—'} · former {(a.former_status || '—').toUpperCase()}{a.former_priority ? ` · ${a.former_priority}` : ''}
          </div>
        </div>
        <Chip color={a.archive_state === 'retiring' ? 'rose' : 'slate'}>{a.archive_state === 'retiring' ? 'Retiring' : 'Archived'}</Chip>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
        <span title={REASON_LABEL[a.reason_code] || undefined}><Chip color="slate">{a.reason_code || 'UNSPECIFIED'}</Chip></span>
        <span style={{ fontSize: 9, color: 'var(--text-faint)', fontFamily: 'var(--font-mono)' }}>
          {a.archive_state === 'retiring'
            ? `archive pending · scheduled exit ~${a.scheduled_exit || '—'}`
            : `archived ${a.archive_date || '—'}`}
          {' · '}{hasOpen ? `${a.open_count} open` : 'flat'}
        </span>
      </div>

      {a.rationale && (
        <div style={{ fontSize: 9, color: 'var(--text-muted)', lineHeight: 1.4, display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }} title={a.rationale}>
          {a.rationale}
        </div>
      )}

      <div style={{ padding: '7px 8px', borderRadius: 'var(--radius-md)', background: 'rgba(255,255,255,0.02)' }}>
        <span style={{ fontSize: 8, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-muted)' }}
          title="Final evidence snapshot — frozen at archive; excluded from active rankings">
          Final evidence snapshot{oosWin ? ` · OOS ${oosWin}` : ''}
        </span>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0,1fr))', gap: '8px 8px', marginTop: 6 }}>
          <EvidenceMetric label="Sharpe (OOS)" value={e.sharpe_oos != null ? Number(e.sharpe_oos).toFixed(2) : '—'} />
          <EvidenceMetric label="Max DD" value={fmtPct1(e.max_drawdown_oos)} />
          <EvidenceMetric label="Trades (OOS)" value={e.trade_count_oos ?? '—'} />
          <EvidenceMetric
            label="Paper net P&L"
            value={e.paper_realized_pnl != null ? fmtK(e.paper_realized_pnl) : '—'}
            tip={e.paper_pnl_basis}
            sub={`${e.closed_paper_trades ?? 0} closed · net`}
          />
          <EvidenceMetric label="Win rate (OOS)" value={e.win_rate_oos != null ? `${Number(e.win_rate_oos).toFixed(0)}%` : '—'} />
          <EvidenceMetric label="Return (OOS)" value={e.returns_oos != null ? `${e.returns_oos >= 0 ? '+' : ''}${fracToPct(e.returns_oos, 1)}%` : '—'} tip="Stored OOS return of the latest backtest run (fraction → %); annualization basis differs per strategy" />
        </div>
      </div>

      <div style={{ fontSize: 9, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
        <span style={{ color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', fontSize: 8 }}>Revival: </span>
        {a.revival_condition}
      </div>
      {(a.linked_evidence || []).length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 8, color: 'var(--text-faint)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Evidence</span>
          {a.linked_evidence.map((t) => <Chip key={t} color="slate">{t}</Chip>)}
        </div>
      )}
    </div>
  );
}

export default function ArchivePanel({ data, error, onOpen }) {
  const [reasonFilter, setReasonFilter] = useState('ALL');
  const [search, setSearch] = useState('');

  const archived = useMemo(() => (data?.archived || []).slice().sort((a, b) => {
    // Retiring books (open runoff positions) first, then newest archive date.
    if ((a.archive_state === 'retiring') !== (b.archive_state === 'retiring')) return a.archive_state === 'retiring' ? -1 : 1;
    return String(b.archive_date || '').localeCompare(String(a.archive_date || '')) || a.name.localeCompare(b.name);
  }), [data]);

  const reasonCounts = useMemo(() => {
    const c = {};
    archived.forEach((a) => { const k = a.reason_code || 'UNSPECIFIED'; c[k] = (c[k] || 0) + 1; });
    return c;
  }, [archived]);

  const filtered = archived.filter((a) => {
    if (reasonFilter !== 'ALL' && (a.reason_code || 'UNSPECIFIED') !== reasonFilter) return false;
    if (search && !a.name.toLowerCase().includes(search.toLowerCase()) && !a.id.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  if (!data) {
    return (
      <div className="jt-surface" style={{ padding: '32px 16px', textAlign: 'center' }}>
        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{error ? 'Could not load the archive — backend unreachable.' : 'Loading archive…'}</div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <div className="strat-seg" style={{ display: 'flex', gap: 2, padding: 3, borderRadius: 'var(--radius-md)', background: 'rgba(15,23,42,0.5)', border: '1px solid var(--border-glass)', maxWidth: '100%', overflowX: 'auto' }}>
          {['ALL', ...Object.keys(reasonCounts).sort()].map((k) => (
            <button key={k} onClick={() => setReasonFilter(k)} style={{ display: 'flex', alignItems: 'center', gap: 5, padding: '4px 9px', borderRadius: 'var(--radius-sm)', border: 'none', cursor: 'pointer', fontSize: 9, fontWeight: 700, whiteSpace: 'nowrap', background: reasonFilter === k ? 'var(--primary)' : 'transparent', color: reasonFilter === k ? '#fff' : 'var(--text-secondary)' }}>
              {k}<span style={{ fontFamily: 'var(--font-mono)', fontSize: 8, opacity: 0.7 }}>{k === 'ALL' ? archived.length : reasonCounts[k]}</span>
            </button>
          ))}
        </div>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search strategy name…"
          style={{ marginLeft: 'auto', padding: '5px 10px', fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--text-strong)', background: 'rgba(15,23,42,0.6)', border: '1px solid var(--border-glass)', borderRadius: 'var(--radius-sm)', outline: 'none', width: 180 }}
        />
      </div>

      <div style={{ fontSize: 9, color: 'var(--text-faint)', lineHeight: 1.4 }}>
        Archived books are excluded from active strategy counts and best-performance rankings; ledgers, signals and history are preserved.
        Revival requires a fresh pre-reg ID + operator approval — a registry status flip alone never revives an archived strategy.
      </div>

      {filtered.length === 0
        ? <div className="jt-surface" style={{ padding: '24px 16px', textAlign: 'center', fontSize: 11, color: 'var(--text-muted)' }}>No archived strategies match these filters.</div>
        : <div className="strat-card-grid">
            {filtered.map((a) => <ArchiveCard key={a.id} a={a} onOpen={onOpen} />)}
          </div>}
    </div>
  );
}
