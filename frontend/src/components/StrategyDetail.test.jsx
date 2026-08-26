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

    // Date column shows the signal date (one per active signal).
    expect(await screen.findAllByText('25/07/2026')).toHaveLength(5);

    // P&L column is rendered for an active position with a live trade.
    expect(screen.getByText('+$230')).toBeTruthy(); // 0001.HK: 100 * (70.8 - 68.5)
    expect(screen.getByText('+$125')).toBeTruthy(); // 2388.HK: 50 * (46.5 - 44.0)

    // Capital panel must agree with the allocation tab (5 active), not the backend's 4.
    expect(screen.getByText('5/5')).toBeTruthy();
  });

  it('computes allocation P&L from the last BUY price even when the position is currently closed', async () => {
    const signals = [
      { ticker: '0001.HK', signal: 'BUY', strength: 0.2, confidence: 0.8, price: 70.8, ts: '2026-07-25T15:16:33.589123' },
    ];
    const trades = [
      // Position was bought and then fully sold, so net qty is 0.
      { ts: '2026-07-24T10:00:00Z', ticker: '0001.HK', side: 'BUY', quantity: 100, price: 68.5, pnl: null, mode: 'PAPER' },
      { ts: '2026-07-24T11:00:00Z', ticker: '0001.HK', side: 'SELL', quantity: 100, price: 69.0, pnl: 50, mode: 'PAPER' },
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

    // Implied qty = round(0.2 * 100000 / 70.8) = 282.
    // P&L = 282 * (70.8 - 68.5) = 648.6, formatted as +$649.
    expect(screen.getByText('+$649')).toBeTruthy();
    // The allocation table should show the whole-lot implied quantity.
    expect(screen.getByText('282')).toBeTruthy();
  });
});
