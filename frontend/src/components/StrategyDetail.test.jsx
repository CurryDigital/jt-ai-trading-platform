import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';

vi.mock('../utils', async () => {
  const actual = await vi.importActual('../utils');
  return {
    ...actual,
    api: { get: vi.fn(), post: vi.fn() },
  };
});

import { api } from '../utils';
import { StrategyDetail } from './StrategyDetail';

const baseEvaluation = {
  strategy_id: 'HK_Quality_BlueChips',
  name: 'HK Quality BlueChips',
  version: null,
  status: 'paper',
  priority: 'NEAR_GOLDEN',
  asset_class: 'HK Stock',
  direction: 'Long',
  time_horizon: 'Medium-term',
  execution_mode: 'PAPER_TRADING',
  book: 'paper',
  venue: 'HK Equities',
  assigned_capital: 100000,
  in_market_capital: 50000,
  conviction_score: null,
  created_at: '2021-01-01T00:00:00Z',
  updated_at: '2021-08-02T00:00:00Z',
  universe: ['0001.HK', '0002.HK', '0003.HK', '0006.HK', '0388.HK', '1299.HK'],
  universe_count: 6,
  entry_logic: 'Top 5 momentum',
  exit_logic: 'Rebalance monthly',
  description: 'Test',
  metrics: { backtest: {}, live: {} },
  divergence: { verdict: 'no_backtest_baseline', win_rate_delta_pp: null, profit_factor_delta: null },
  equity_curve: [],
  monthly_returns: [],
  recent_signals: [],
  window_days: 30,
};

describe('StrategyDetail unified statistics panel', () => {
  const richEvaluation = {
    ...baseEvaluation,
    book: 'paper',
    metrics: {
      backtest: { win_rate: 0.6389, profit_factor: 4.7674, sharpe: 2.2022, max_drawdown: -0.0662, total_trades: 36, total_return: 0.558, avg_holding_days: 75.1 },
      live: { total_trades: 6, win_rate: 0.1667, profit_factor: 0.339, total_pnl: -6607.65, last_trade_at: '2026-10-02', first_trade_at: '2026-08-11', avg_holding_days: 20.8 },
    },
    metrics_by_mode: {
      sim: { win_rate: 0.6389, profit_factor: 4.7674, sharpe: 2.2022, max_drawdown: -0.0662, total_trades: 36, total_return: 0.558, avg_holding_days: 75.1, total_pnl: null },
      paper: { total_trades: 6, win_rate: 0.1667, profit_factor: 0.339, total_pnl: -6607.65, last_trade_at: '2026-10-02', first_trade_at: '2026-08-11', avg_holding_days: 20.8 },
      uat: { total_fills: 0, total_trades: null, win_rate: null, profit_factor: null, total_pnl: null, last_trade_at: null },
      live: { total_trades: 0, win_rate: null, profit_factor: null, total_pnl: null, last_trade_at: null },
    },
    divergence: { verdict: 'insufficient_live_data', win_rate_delta_pp: -47.22, profit_factor_delta: -4.428 },
    monthly_returns: [{ year: 2026, month: 1, return: 0.068 }],
    monthly_returns_paper: [{ year: 2026, month: 9, return: -0.05 }],
    yearly_returns: { sim: { '2026': 0.1324 }, paper: { '2026': -0.0529 } },
    equity_curve: [{ date: '2026-09-01', pnl: -1000, cum_pnl: -1000 }, { date: '2026-09-17', pnl: -5607.65, cum_pnl: -6607.65 }],
    recent_trades: [],
    backtest_trades: [],
    paper_skips: [],
    uat_fills: [],
  };

  it('renders SIM and PAPER KPIs simultaneously on first load — no toggle click required', async () => {
    api.get.mockImplementation(async () => richEvaluation);
    render(<StrategyDetail strategyId="ETF_Multi_Asset_Tactical_Allocation" onBack={() => {}} />);

    // SIM column (OOS backtest baseline)
    expect(await screen.findByText('63.9%')).toBeTruthy();   // win rate
    expect(screen.getByText('4.77')).toBeTruthy();           // profit factor
    expect(screen.getByText('+55.8%')).toBeTruthy();         // OOS return
    expect(screen.getByText('-6.6%')).toBeTruthy();          // max drawdown
    expect(screen.getByText('2.20')).toBeTruthy();           // sharpe
    expect(screen.getByText('75.1d')).toBeTruthy();          // avg hold

    // PAPER column, same initial view, no click
    expect(screen.getByText('16.7%')).toBeTruthy();          // win rate
    expect(screen.getAllByText('$-6.6K').length).toBeGreaterThanOrEqual(1); // net P&L (table + curve header)
    expect(screen.getByText('0.34')).toBeTruthy();           // profit factor
    expect(screen.getByText('20.8d')).toBeTruthy();          // avg hold

    // Delta column — win-rate difference in pp, profit factor arithmetic delta
    expect(screen.getByText('-47.2pp')).toBeTruthy();
    expect(screen.getByText('-4.43')).toBeTruthy();
    expect(screen.getByText('-54.3d')).toBeTruthy();

    // The old SIM/PAPER statistics-view toggle tiles are gone
    expect(screen.queryByText('SIM · BACKTEST')).toBeNull();
    expect(screen.queryByText('ACTIVE MODE')).toBeNull();
    expect(screen.queryByText('stage not reached')).toBeNull();
  });

  it('renders — for missing paper metrics, never a fabricated zero or fake delta', async () => {
    const emptyPaper = {
      ...richEvaluation,
      metrics_by_mode: {
        ...richEvaluation.metrics_by_mode,
        paper: { total_trades: 0, win_rate: null, profit_factor: null, total_pnl: null, last_trade_at: null },
      },
      metrics: { ...richEvaluation.metrics, live: { total_trades: 0, win_rate: null, profit_factor: null, total_pnl: 0.0, last_trade_at: null, first_trade_at: null, avg_holding_days: null } },
      divergence: { verdict: 'insufficient_live_data', win_rate_delta_pp: null, profit_factor_delta: null },
      monthly_returns_paper: [],
      yearly_returns: { sim: { '2026': 0.1324 }, paper: {} },
      equity_curve: [],
    };
    api.get.mockImplementation(async () => emptyPaper);
    render(<StrategyDetail strategyId="ETF_Multi_Asset_Tactical_Allocation" onBack={() => {}} />);

    // SIM column still renders
    expect(await screen.findByText('63.9%')).toBeTruthy();
    // No pp delta and no fabricated $0 / 0.00 paper values
    expect(screen.queryByText(/pp$/)).toBeNull();
    expect(screen.queryByText('$0')).toBeNull();
    expect(screen.queryByText('0.00')).toBeNull();
  });

  it('eagerly fetches the paper book for live-mode strategies so both ledgers are on screen', async () => {
    const calls = [];
    api.get.mockImplementation(async (url) => {
      calls.push(url);
      return {
        ...richEvaluation,
        book: url.includes('book=paper') ? 'paper' : 'live',
        execution_mode: 'LIVE_TRADING',
      };
    });
    render(<StrategyDetail strategyId="ETF_Multi_Asset_Tactical_Allocation" onBack={() => {}} />);
    await screen.findByText('63.9%');
    expect(calls.some(u => u.includes('book=paper'))).toBe(true);
  });
});

describe('StrategyDetail rebalances', () => {
  it('renders all SELL rows even when the same ticker trades multiple times on one day', async () => {
    const sells = [
      { ts: '2021-08-02', ticker: '0006.HK', side: 'SELL', quantity: 410, price: 39.21, pnl: 704.64, mode: 'PAPER' },
      { ts: '2021-08-02', ticker: '0001.HK', side: 'SELL', quantity: 321, price: 45.34, pnl: -799.92, mode: 'PAPER' },
      { ts: '2021-08-02', ticker: '0016.HK', side: 'SELL', quantity: 168, price: 89.19, pnl: -1062.39, mode: 'PAPER' },
      { ts: '2021-08-02', ticker: '0388.HK', side: 'SELL', quantity: 0, price: 458.61, pnl: 11.59, mode: 'PAPER' },
      { ts: '2021-08-02', ticker: '1299.HK', side: 'SELL', quantity: 4, price: 83.98, pnl: -6.85, mode: 'PAPER' },
      { ts: '2021-08-02', ticker: '0388.HK', side: 'SELL', quantity: 3, price: 458.61, pnl: 93.13, mode: 'PAPER' },
      { ts: '2021-08-02', ticker: '1299.HK', side: 'SELL', quantity: 4, price: 83.98, pnl: -27.36, mode: 'PAPER' },
      { ts: '2021-08-02', ticker: '1299.HK', side: 'SELL', quantity: 7, price: 83.98, pnl: -18.49, mode: 'PAPER' },
      { ts: '2021-08-02', ticker: '0388.HK', side: 'SELL', quantity: 34, price: 458.61, pnl: 4046.95, mode: 'PAPER' },
      { ts: '2021-08-02', ticker: '1299.HK', side: 'SELL', quantity: 160, price: 83.98, pnl: 728.18, mode: 'PAPER' },
    ];

    api.get.mockImplementation(async () => ({ ...baseEvaluation, recent_trades: sells }));

    render(<StrategyDetail strategyId="HK_Quality_BlueChips" onBack={() => {}} />);

    await screen.findByText('02/08/21');
    const sellRows = screen.getAllByText('SELL');
    expect(sellRows.length).toBe(10);
  });

  it('shows the allocation date, P&L and active position count', async () => {
    const signals = [
      { ticker: '0001.HK', signal: 'BUY', strength: 0.2, confidence: 0.8, price: 70.8, ts: '2026-07-25T15:16:33.589123' },
      { ticker: '0002.HK', signal: 'BUY', strength: 0.2, confidence: 0.8, price: 77.7, ts: '2026-07-25T15:16:33.589123' },
      { ticker: '0005.HK', signal: 'BUY', strength: 0.2, confidence: 0.8, price: 156.9, ts: '2026-07-25T15:16:33.589123' },
      { ticker: '0016.HK', signal: 'BUY', strength: 0.2, confidence: 0.8, price: 121.9, ts: '2026-07-25T15:16:33.589123' },
      { ticker: '2388.HK', signal: 'BUY', strength: 0.2, confidence: 0.8, price: 46.5, ts: '2026-07-25T15:16:33.589123' },
    ];
    const trades = [
      { ts: '2026-07-24T10:00:00Z', ticker: '0001.HK', side: 'BUY', quantity: 100, price: 68.5, pnl: null, mode: 'PAPER' },
      { ts: '2026-07-24T10:00:00Z', ticker: '2388.HK', side: 'BUY', quantity: 50, price: 44.0, pnl: null, mode: 'PAPER' },
    ];

    api.get.mockImplementation(async (url) => {
      if (url.includes('/capital-pool')) {
        return {
          total_assigned: 100000,
          used: 100000,
          available: 0,
          trade_size: 25000,
          active_positions: 4,
          max_positions: 4,
          can_trade: false,
          usage_pct: 100,
        };
      }
      return { ...baseEvaluation, recent_signals: signals, recent_trades: trades };
    });

    render(<StrategyDetail strategyId="HK_Quality_BlueChips" onBack={() => {}} />);
    fireEvent.click(await screen.findByText('Allocation (5)'));

    // Purchased column shows the ledger BUY date for the two held positions.
    expect(await screen.findAllByText('24/07/2026')).toHaveLength(2);

    // P&L column is rendered for an active position with a live trade.
    expect(screen.getByText('+$230')).toBeTruthy(); // 0001.HK: 100 * (70.8 - 68.5)
    expect(screen.getByText('+$125')).toBeTruthy(); // 2388.HK: 50 * (46.5 - 44.0)

    // Capital panel must agree with the allocation tab (5 active), not the backend's 4.
    expect(screen.getByText('5/5')).toBeTruthy();
  });

  it('shows explicit zeros and a no-fill note for a signal whose position is currently flat', async () => {
    const signals = [
      { ticker: '0001.HK', signal: 'BUY', strength: 0.2, confidence: 0.8, price: 70.8, ts: '2026-07-25T15:16:33.589123' },
    ];
    const trades = [
      // recent_trades arrives DESC by ts — the component walks it oldest→newest.
      // Position was bought and then fully sold, so net qty is 0.
      { ts: '2026-07-24T11:00:00Z', ticker: '0001.HK', side: 'SELL', quantity: 100, price: 69.0, pnl: 50, mode: 'PAPER' },
      { ts: '2026-07-24T10:00:00Z', ticker: '0001.HK', side: 'BUY', quantity: 100, price: 68.5, pnl: null, mode: 'PAPER' },
    ];

    api.get.mockImplementation(async (url) => {
      if (url.includes('/capital-pool')) {
        return {
          total_assigned: 100000,
          used: 100000,
          available: 0,
          trade_size: 25000,
          active_positions: 4,
          max_positions: 4,
          can_trade: false,
          usage_pct: 100,
        };
      }
      return { ...baseEvaluation, recent_signals: signals, recent_trades: trades };
    });

    render(<StrategyDetail strategyId="HK_Quality_BlueChips" onBack={() => {}} />);
    fireEvent.click(await screen.findByText('Allocation (1)'));

    // Position is flat (bought then fully sold): the row stays visible with
    // explicit zeros and a factual no-fill note — never a hidden row and never
    // an invented quantity or P&L.
    expect(await screen.findByText('signal only · no fill')).toBeTruthy();
    expect(screen.getAllByText('0%').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('$0').length).toBeGreaterThanOrEqual(1);
  });
});
