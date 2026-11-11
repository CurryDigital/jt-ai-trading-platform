// Command center v7.1 — unit tests for the aggregation / currency utilities.
// Covers: mixed currencies (never netted), >500-trade books (full-ledger
// aggregate vs truncated page), reconciliation, grouping, per-environment
// normalization, and negative/zero P&L contribution handling.

import { describe, it, expect } from 'vitest';
import {
  maxDrawdown, sumByCcy, perCcyUnrealized, bookGrossStats, contribution,
  reconcileRealized, realizedFromTrades, buildStrategyRows, driverSegments,
  rankDrivers, buildActionItems, normPositions, normFills, normOrders,
  CONTRIB_MIN_BASE,
} from './aggregate';

// ---------------------------------------------------------------------------
// maxDrawdown
// ---------------------------------------------------------------------------
describe('maxDrawdown', () => {
  it('returns peak-to-trough of the series (<= 0)', () => {
    const curve = [100, 120, 90, 130, 80].map(v => ({ equity: v }));
    expect(maxDrawdown(curve)).toBe(-50); // 130 peak -> 80 trough
  });
  it('returns null for a series shorter than 2 points', () => {
    expect(maxDrawdown([{ equity: 1 }])).toBeNull();
    expect(maxDrawdown([])).toBeNull();
    expect(maxDrawdown(null)).toBeNull();
  });
  it('returns 0 for a monotonically rising series', () => {
    expect(maxDrawdown([1, 2, 3].map(v => ({ equity: v })))).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Currency safety — mixed currencies are never netted
// ---------------------------------------------------------------------------
describe('sumByCcy', () => {
  it('sums per currency and never across currencies', () => {
    const rows = [
      { unreal: 100, ccy: 'USD' }, { unreal: -40, ccy: 'USD' },
      { unreal: 500, ccy: 'HKD' }, { unreal: null, ccy: 'HKD' },
    ];
    const { sums, skipped } = sumByCcy(rows, 'unreal', 'USD');
    expect(Object.fromEntries(sums)).toEqual({ USD: 60, HKD: 500 });
    expect(skipped).toBe(1);
  });
  it('falls back to the default currency when a row carries none', () => {
    const { sums } = sumByCcy([{ mv: 10 }], 'mv', 'USD');
    expect(sums).toEqual([['USD', 10]]);
  });
});

describe('perCcyUnrealized', () => {
  it('keeps currency segments separate', () => {
    const seg = perCcyUnrealized([
      { unreal: 5, ccy: 'HKD' }, { unreal: 7, ccy: 'USD' }, { unreal: 1, ccy: 'HKD' },
    ]);
    expect(Object.fromEntries(seg)).toEqual({ HKD: 6, USD: 7 });
  });
});

describe('bookGrossStats', () => {
  it('flags mixed-currency books and never computes a gross total', () => {
    const r = bookGrossStats([{ mv: 100, ccy: 'USD' }, { mv: 200, ccy: 'HKD' }]);
    expect(r.mixed).toBe(true);
    expect(r.gross).toBeUndefined();
  });
  it('computes gross, concentration and allocation for single-currency books', () => {
    const r = bookGrossStats([
      { mv: 100, ccy: 'USD', symbol: 'A', strategy: 's1' },
      { mv: -50, ccy: 'USD', symbol: 'B', strategy: 's1' },
      { mv: 50, ccy: 'USD', symbol: 'C', strategy: 's2' },
    ]);
    expect(r.mixed).toBe(false);
    expect(r.gross).toBe(200);
    expect(r.top1).toBe(50);
    expect(r.top1Name).toBe('A');
    expect(r.alloc).toEqual([{ name: 's1', value: 150 }, { name: 's2', value: 50 }]);
  });
});

// ---------------------------------------------------------------------------
// Contribution — no percentages on zero/negative/near-zero bases
// ---------------------------------------------------------------------------
describe('contribution', () => {
  it('returns a percentage on a meaningful positive base', () => {
    expect(contribution(25, 100)).toEqual({ mode: 'pct', pct: 25 });
  });
  it('falls back to currency amount when the total is zero', () => {
    expect(contribution(25, 0)).toEqual({ mode: 'amount', amount: 25 });
  });
  it('falls back to currency amount when the total is negative', () => {
    expect(contribution(25, -300)).toEqual({ mode: 'amount', amount: 25 });
  });
  it('falls back to currency amount when the total is near zero', () => {
    const r = contribution(500, CONTRIB_MIN_BASE / 2);
    expect(r.mode).toBe('amount');
    expect(r.amount).toBe(500);
  });
  it('returns none for missing values', () => {
    expect(contribution(null, 100)).toEqual({ mode: 'none' });
  });
});

// ---------------------------------------------------------------------------
// Reconciliation and the >500-trade hazard
// ---------------------------------------------------------------------------
const makeLedger = (n) => Array.from({ length: n }, (_, i) => ({
  strategy_id: `s${i % 7}`, pnl: (i % 2 === 0 ? 1 : -1) * (i + 1), // deterministic
}));

describe('realizedFromTrades / reconcileRealized', () => {
  it('full-ledger aggregation reconciles exactly with the book total', () => {
    const ledger = makeLedger(620);
    const full = realizedFromTrades(ledger);
    const fullSum = Object.values(full).reduce((s, g) => s + g.realized, 0);
    const expectSum = ledger.reduce((s, t) => s + t.pnl, 0);
    expect(fullSum).toBeCloseTo(expectSum, 8);
    expect(reconcileRealized(fullSum, expectSum)).toEqual({ ok: true, delta: 0 });
  });

  it('page-truncated aggregation (limit=500) silently under-reports a 620-trade book — reconciliation flags it', () => {
    const ledger = makeLedger(620);
    const truncated = realizedFromTrades(ledger, {}, 500);
    const truncSum = Object.values(truncated).reduce((s, g) => s + g.realized, 0);
    const expectSum = ledger.reduce((s, t) => s + t.pnl, 0);
    expect(truncSum).not.toBeCloseTo(expectSum, 2);
    const recon = reconcileRealized(truncSum, expectSum);
    expect(recon.ok).toBe(false);
    expect(Math.abs(recon.delta)).toBeGreaterThan(0.02);
  });

  it('truncated aggregation also drops closed-trade counts per strategy', () => {
    const ledger = makeLedger(620);
    const full = realizedFromTrades(ledger);
    const truncated = realizedFromTrades(ledger, {}, 500);
    const closedFull = Object.values(full).reduce((s, g) => s + g.closed, 0);
    const closedTrunc = Object.values(truncated).reduce((s, g) => s + g.closed, 0);
    expect(closedFull).toBe(620);
    expect(closedTrunc).toBe(500);
  });

  it('returns null when either side is missing (no fake reconciliation)', () => {
    expect(reconcileRealized(null, 100)).toBeNull();
    expect(reconcileRealized(100, null)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// buildStrategyRows — union of open groups + ledger, active/historical split
// ---------------------------------------------------------------------------
describe('buildStrategyRows', () => {
  const stratPnl = {
    strategies: [
      { strategy_id: 's1', name: 'Alpha', closed_trades: 84, win_rate: 39.3, cum_pnl: 17029.19, ytd_pnl: 30182.54 },
      { strategy_id: 's2', name: 'Beta', closed_trades: 10, win_rate: 50, cum_pnl: -4000, ytd_pnl: -4000 },
    ],
    total_closed: 94,
    total_cum_pnl: 13029.19,
  };

  it('unions open-position strategies with closed-ledger strategies and splits active vs historical', () => {
    const posRows = [
      { strategyId: 's3', strategy: 'Gamma', mv: 1000, unreal: 200 },
      { strategyId: 's3', strategy: 'Gamma', mv: 500, unreal: -50 },
    ];
    const r = buildStrategyRows({ posRows, stratPnl, riskBy: {} });
    expect(r.active.map(g => g.id)).toEqual(['s3']);
    expect(r.active[0]).toMatchObject({ open: 2, mv: 1500, unreal: 150, realized: null });
    // historical = closed-ledger only (no open rows), biggest |realized| first
    expect(r.historical.map(g => g.id)).toEqual(['s1', 's2']);
    expect(r.historical[0]).toMatchObject({ open: 0, realized: 17029.19, closed: 84 });
  });

  it('joins open rows to the ledger by strategy_id (not by display name)', () => {
    const posRows = [{ strategyId: 's1', strategy: 'Alpha (renamed)', mv: 100, unreal: 10 }];
    const r = buildStrategyRows({ posRows, stratPnl, riskBy: {} });
    const g = r.active.find(x => x.id === 's1');
    expect(g).toMatchObject({ open: 1, realized: 17029.19, closed: 84 });
    expect(r.historical.map(x => x.id)).toEqual(['s2']);
  });

  it('sorts by max(|unrealized|, |realized|, |market value|)', () => {
    const posRows = [
      { strategyId: 's9', strategy: 'Tiny', mv: 5, unreal: 1 },
      { strategyId: 's2', strategy: 'Beta', mv: 0, unreal: 0 }, // realized -4000 dominates
    ];
    const r = buildStrategyRows({ posRows, stratPnl, riskBy: {} });
    expect(r.active[0].id).toBe('s2');
  });

  it('handles empty inputs and zero-P&L books without fabricating rows', () => {
    const r = buildStrategyRows({ posRows: [], stratPnl: { strategies: [] }, riskBy: {} });
    expect(r.active).toEqual([]);
    expect(r.historical).toEqual([]);
    const r2 = buildStrategyRows({ posRows: [{ strategyId: 's1', strategy: 'A', mv: 10, unreal: 0 }], stratPnl: { strategies: [] }, riskBy: {} });
    expect(r2.totalUn).toBe(0); // zero total -> contribution() will use amount mode
    expect(contribution(0, r2.totalUn).mode).toBe('amount');
  });
});

// ---------------------------------------------------------------------------
// Drivers — mixed-currency segmentation
// ---------------------------------------------------------------------------
describe('driverSegments / rankDrivers', () => {
  it('segments mixed-currency books and never nets them', () => {
    const rows = [
      { unreal: 10, ccy: 'USD', symbol: 'A' }, { unreal: -5, ccy: 'HKD', symbol: 'B' },
    ];
    const c = driverSegments(rows, 'USD');
    expect(c.mixed).toHaveLength(2);
    expect(c.mixed.map(s => s.ccy).sort()).toEqual(['HKD', 'USD']);
  });
  it('single-currency books stay one segment', () => {
    const c = driverSegments([{ unreal: 1 }, { unreal: -2 }], 'USD');
    expect(c.single.ccy).toBe('USD');
    const { pos, neg } = rankDrivers(c.single.rows);
    expect(pos.map(d => d.unreal)).toEqual([1]);
    expect(neg.map(d => d.unreal)).toEqual([-2]);
  });
  it('empty when nothing is marked', () => {
    expect(driverSegments([{ unreal: null }], 'USD').empty).toBe(true);
    expect(driverSegments(null, 'USD').loading).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Action items — critical alerts before execution/monitoring issues
// ---------------------------------------------------------------------------
describe('buildActionItems', () => {
  it('orders critical alerts first, then warning issues; HALT is global', () => {
    const items = buildActionItems({
      env: 'paper',
      limits: { global_halt: true },
      overview: {
        strategy_risks: [{ strategy_id: 's1', name: 'Alpha', sev: 'warning', triggers: ['cap'] }],
        attention: [{ id: 'att1', sev: 'critical', title: 'DB down' }, { id: 'live_x', sev: 'critical', title: 'live-only' }],
        monitoring_gap: 2,
      },
      positions: null,
    });
    expect(items[0].sev).toBe('critical');
    expect(items.map(i => i.id)).toContain('halt');
    expect(items.map(i => i.id)).toContain('gap'); // monitoring gap is an issue item
    expect(items.map(i => i.id)).not.toContain('live_x'); // env-scoped: live_* excluded from paper
    const sevs = items.map(i => i.sev);
    expect(sevs.indexOf('warning')).toBeGreaterThan(sevs.lastIndexOf('critical'));
  });

  it('uat disconnection is critical; live reads only live_* attention', () => {
    const uat = buildActionItems({ env: 'uat', limits: null, overview: null, positions: { connected: false } });
    expect(uat[0]).toMatchObject({ id: 'uat-down', sev: 'critical' });
    const live = buildActionItems({
      env: 'live', limits: null, positions: null,
      overview: { attention: [{ id: 'live_dd', sev: 'critical', title: 'L' }, { id: 'news1', sev: 'warning', title: 'N' }], deployed_health: [] },
    });
    expect(live.map(i => i.id)).toEqual(['live_dd']);
  });
});

// ---------------------------------------------------------------------------
// Per-environment normalization (environment switching)
// ---------------------------------------------------------------------------
describe('normPositions', () => {
  const names = { s1: 'Alpha' };
  it('sim maps entry_date/pnl fields and strategy_id', () => {
    const [p] = normPositions('sim', [{ id: 1, ticker: 'AAPL', strategy_id: 's1', side: 'long', quantity: 100, entry_price: 10, current_price: 12, unrealized_pnl: 200, market_value: 1200, entry_date: '2026-01-05' }], names, Date.UTC(2026, 0, 12));
    expect(p).toMatchObject({ entryDate: '2026-01-05', symbol: 'AAPL', strategy: 'Alpha', strategyId: 's1', side: 'LONG', unreal: 200, mv: 1200, days: 7 });
  });
  it('paper derives market value from shares × price and uses unrealised_pnl', () => {
    const [p] = normPositions('paper', [{ id: 2, ticker: 'MSFT', strategy_id: 's1', direction: 'long', shares: 10, current_price: 100, unrealised_pnl: -5, opened_at: '2026-01-01T00:00:00' }], names, Date.UTC(2026, 0, 2));
    expect(p).toMatchObject({ mv: 1000, unreal: -5, days: 1, entryDate: '2026-01-01' });
  });
  it('uat keeps per-row currency and carries no strategy/entry attribution', () => {
    const [p] = normPositions('uat', [{ symbol: '0700.HK', currency: 'HKD', qty: 100, avg_cost: 300, market_price: 310, unrealized_pnl: 1000, market_value: 31000 }]);
    expect(p).toMatchObject({ ccy: 'HKD', side: 'LONG', strategy: null, strategyId: null, entryDate: null, days: null });
    expect(p.entryTip).toMatch(/no entry timestamp/i);
  });
  it('live marks unattributed rows honestly', () => {
    const [p] = normPositions('live', [{ id: 9, ticker: 'NVDA', side: 'long', quantity: 5, avg_entry: 100, current_price: 110, unrealized_pnl: 50 }], names, Date.UTC(2026, 0, 2));
    expect(p.strategy).toBeNull();
    expect(p.strategyTip).toMatch(/no strategy attribution/i);
  });
});

describe('normFills / normOrders', () => {
  it('fills: uat/live carry no strategy attribution or per-fill pnl guarantee', () => {
    const [f] = normFills('uat', [{ t: '2026-01-02T10:00:00', ticker: 'X', side: 'buy', qty: 1, price: 2 }]);
    expect(f).toMatchObject({ fillDate: '2026-01-02', strategy: null, pnl: null });
    expect(f.pnlTip).toMatch(/not served/i);
    const [g] = normFills('paper', [{ t: '2026-01-02', ticker: 'Y', side: 'sell', qty: 1, price: 2, pnl: 50, strategy_id: 's1' }], { s1: 'Alpha' });
    expect(g).toMatchObject({ strategy: 'Alpha', pnl: 50 });
  });
  it('orders: uat rows have no order timestamp', () => {
    const [o] = normOrders('uat', [{ order_id: 1, local_symbol: 'AAPL', action: 'buy', qty: 10, order_type: 'MKT', status: 'Submitted' }]);
    expect(o.orderDate).toBeNull();
    expect(o.orderTip).toMatch(/no order submission timestamp/i);
  });
});
