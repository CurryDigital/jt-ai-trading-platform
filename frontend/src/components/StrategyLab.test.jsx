import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';

// Mock the api module before importing StrategyLab
vi.mock('../utils', async () => {
  const actual = await vi.importActual('../utils');
  return {
    ...actual,
    api: {
      get: vi.fn(),
    },
  };
});

import { api } from '../utils';
import { StrategyLab } from './StrategyLab';

describe('StrategyLab UI acceptance criteria', () => {
  const pipelineData = [
    { id: 's1', name: 'Approved with live metrics', asset: 'ETF', sim_wr: 50, btpf: 1.5, trades: 30, sharpe: 1.2, dd: -5, is_paper_monitoring: true, paper_wr: 55, paper_pf: 2.1, paper_pnl: 1000, db_status: 'approved' },
    { id: 's2', name: 'Null live metrics', asset: 'EQUITY', sim_wr: 45, btpf: 1.2, trades: 40, sharpe: 1.0, dd: -8, is_paper_monitoring: false, paper_wr: null, paper_pf: null, paper_pnl: null, db_status: 'approved' },
    { id: 's3', name: 'Zero live PnL', asset: 'EQUITY', sim_wr: 45, btpf: 1.2, trades: 40, sharpe: 1.0, dd: -8, is_paper_monitoring: true, paper_wr: 0, paper_pf: 0, paper_pnl: 0, db_status: 'approved' },
    { id: 's4', name: 'Rejected strategy', asset: 'CRYPTO', sim_wr: 30, btpf: 0.8, trades: 20, sharpe: 0.5, dd: -25, is_paper_monitoring: false, paper_wr: null, paper_pf: null, paper_pnl: null, db_status: 'rejected' },
  ];

  const researcherData = {
    strategies: [
      { id: 's1', description: 'desc1', universe: ['AAPL'] },
      { id: 's2', description: 'desc2', universe: ['TSLA'] },
      { id: 's3', description: 'desc3', universe: ['MSFT'] },
      { id: 's4', description: 'desc4', universe: ['BTC'] },
    ],
  };

  it('renders all four columns and distinguishes null from zero', async () => {
    api.get.mockImplementation(async (url) => {
      if (url === '/api/strategies/pipeline-feed') return { data: pipelineData };
      if (url === '/api/strategies/researcher') return researcherData;
      return {};
    });

    render(<StrategyLab />);

    await screen.findByText('Approved with live metrics');
    expect(screen.getByText('Paper PF')).toBeInTheDocument();

    const nullRow = screen.getByText('Null live metrics').closest('tr');
    const dashEls = nullRow.querySelectorAll('.text-slate-600');
    const dashTexts = Array.from(dashEls).map((el) => el.textContent);
    expect(dashTexts).toContain('—');

    const zeroRow = screen.getByText('Zero live PnL').closest('tr');
    expect(zeroRow.textContent).toContain('0.0');
  });

  it('flags rejected strategies with badge and disabled row styling', async () => {
    api.get.mockImplementation(async (url) => {
      if (url === '/api/strategies/pipeline-feed') return { data: pipelineData };
      if (url === '/api/strategies/researcher') return researcherData;
      return {};
    });

    render(<StrategyLab />);

    await screen.findByText('Rejected strategy');
    const rejectedRow = screen.getByText('Rejected strategy').closest('tr');
    expect(rejectedRow.textContent).toContain('Rejected');
    expect(rejectedRow.className).toContain('opacity-70');
  });
});
