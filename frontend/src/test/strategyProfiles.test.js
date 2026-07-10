import { describe, it, expect } from 'vitest';
import { mapApiToBook } from '../components/strategyProfiles';

// mapApiToBook is the seam between /api/strategies/researcher and everything the
// Strategies workspace renders — mode ladder placement, win-rate normalization,
// and yearly-return extraction all live here.
describe('mapApiToBook', () => {
  it('normalizes execution_mode variants onto the mode ladder', () => {
    const rows = [
      { id: 'a', execution_mode: 'LIVE' },
      { id: 'b', execution_mode: 'PAPER_TRADING' },
      { id: 'c', execution_mode: 'sim' === 'never' ? 'x' : 'SIMULATION' },
      { id: 'd', execution_mode: null, status: 'approved' },
    ];
    const book = mapApiToBook(rows);
    expect(book[0].mode).toBe('LIVE_TRADING');
    expect(book[1].mode).toBe('PAPER_TRADING');
    expect(book[2].mode).toBe('SIMULATION');
    expect(book[3].mode).toBe('LIVE_TRADING'); // approved status implies deployed
  });

  it('converts fractional win_rate and max_drawdown to percents', () => {
    const [s] = mapApiToBook([{ id: 'a', win_rate: 0.6792, max_drawdown: 0.121 }]);
    expect(s.btWR).toBe(68);
    expect(s.dd).toBe(-12.1);
  });

  it('takes the latest yearly backtest return as the headline return', () => {
    const [s] = mapApiToBook([{
      id: 'a',
      yearly_backtest: {
        2024: { return_pct: 0.10 },
        2026: { return_pct: 0.238 },
        2025: { return_pct: -0.05 },
      },
    }]);
    expect(s.returns).toBe(23.8);
  });

  it('degrades to null/zero for missing fields instead of NaN', () => {
    const [s] = mapApiToBook([{ id: 'a' }]);
    expect(s.btWR).toBeNull();
    expect(s.returns).toBeNull();
    expect(s.sharpe).toBe(0);
    expect(Number.isNaN(s.dd)).toBe(false);
  });
});
