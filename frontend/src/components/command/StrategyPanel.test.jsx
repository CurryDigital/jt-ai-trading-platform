// Command center v7.1 — StrategyPanel render tests: active vs historical
// split, contribution % suppression on zero/negative totals, reconciliation
// badge, and strategy detail links.

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';

import { StrategyPanel } from './StrategyPanel';

const baseProps = {
  env: 'paper',
  defCcy: 'USD',
  navigateToTab: vi.fn(),
  onSelectStrategy: vi.fn(),
  riskBy: {},
  noDataText: null,
};

const stratPnl = {
  strategies: [
    { strategy_id: 's1', name: 'Alpha', closed_trades: 84, win_rate: 39.3, cum_pnl: 17029.19, ytd_pnl: 30182.54 },
    { strategy_id: 's2', name: 'Beta', closed_trades: 10, win_rate: 50, cum_pnl: -4000, ytd_pnl: -4000 },
  ],
  total_closed: 94,
  total_cum_pnl: 13029.19,
};

describe('StrategyPanel (v7.1)', () => {
  it('splits active holdings from historical/closed strategies', () => {
    const rows = [{ strategyId: 's9', strategy: 'Gamma', symbol: 'AAA', mv: 1000, unreal: 250 }];
    render(<StrategyPanel {...baseProps} rows={rows} stratPnl={stratPnl} bookCumPnl={13029.19} />);
    expect(screen.getByText(/Active — open holdings/i)).toBeInTheDocument();
    expect(screen.getByText(/Historical — closed ledger/i)).toBeInTheDocument();
    expect(screen.getByText('Gamma')).toBeInTheDocument();
    expect(screen.getByText('Alpha')).toBeInTheDocument();
    expect(screen.getByText('Beta')).toBeInTheDocument();
  });

  it('shows contribution as a percentage on a meaningful positive total', () => {
    const rows = [
      { strategyId: 's1', strategy: 'Alpha', symbol: 'A', mv: 100, unreal: 300 },
      { strategyId: 's2', strategy: 'Beta', symbol: 'BBB', mv: 100, unreal: 100 },
    ];
    const { container } = render(<StrategyPanel {...baseProps} rows={rows} stratPnl={null} bookCumPnl={null} />);
    expect(container.textContent).toContain('+75%');
    expect(container.textContent).toContain('+25%');
  });

  it('suppresses contribution percentages when the book total is near zero (shows currency amounts)', () => {
    const rows = [
      { strategyId: 's1', strategy: 'Alpha', symbol: 'A', mv: 100, unreal: 500 },
      { strategyId: 's2', strategy: 'Beta', symbol: 'BBB', mv: 100, unreal: -499.5 },
    ];
    const { container } = render(<StrategyPanel {...baseProps} rows={rows} stratPnl={null} bookCumPnl={null} />);
    // No giant misleading percentages — the contribution cells show currency.
    expect(container.textContent).not.toContain('%');
    expect(container.textContent).toContain('+$500');
  });

  it('suppresses contribution percentages when the book total is negative', () => {
    const rows = [
      { strategyId: 's1', strategy: 'Alpha', symbol: 'A', mv: 100, unreal: -200 },
      { strategyId: 's2', strategy: 'Beta', symbol: 'BBB', mv: 100, unreal: -100 },
    ];
    const { container } = render(<StrategyPanel {...baseProps} rows={rows} stratPnl={null} bookCumPnl={null} />);
    expect(container.textContent).not.toMatch(/\d+%/);
    expect(container.textContent).toContain('$-200');
  });

  it('links each strategy row to its detail page via onSelectStrategy', () => {
    const rows = [{ strategyId: 's9', strategy: 'Gamma', symbol: 'AAA', mv: 1000, unreal: 250 }];
    render(<StrategyPanel {...baseProps} rows={rows} stratPnl={stratPnl} bookCumPnl={13029.19} />);
    fireEvent.click(screen.getByText('Alpha'));
    expect(baseProps.onSelectStrategy).toHaveBeenCalledWith('s1');
    fireEvent.click(screen.getByText('Gamma'));
    expect(baseProps.onSelectStrategy).toHaveBeenCalledWith('s9');
  });

  it('shows the reconciliation badge when the aggregate ties to the book total', () => {
    const rows = [{ strategyId: 's9', strategy: 'Gamma', symbol: 'AAA', mv: 1000, unreal: 250 }];
    const { container } = render(<StrategyPanel {...baseProps} rows={rows} stratPnl={stratPnl} bookCumPnl={13029.19} />);
    expect(container.textContent).toContain('reconciled');
  });

  it('flags a reconciliation mismatch instead of hiding it', () => {
    const rows = [{ strategyId: 's9', strategy: 'Gamma', symbol: 'AAA', mv: 1000, unreal: 250 }];
    const { container } = render(<StrategyPanel {...baseProps} rows={rows} stratPnl={stratPnl} bookCumPnl={9999} />);
    expect(container.textContent).toContain('recon Δ');
  });

  it('renders the honest no-data state for UAT', () => {
    render(<StrategyPanel {...baseProps} env="uat" rows={[]} stratPnl={null} noDataText="No strategy attribution exists for the UAT book" />);
    expect(screen.getByText(/No strategy attribution exists for the UAT book/)).toBeInTheDocument();
  });
});
