import { describe, expect, it } from 'vitest';

import { tierBorderFor, tierCutoffsFor } from './newsTiers';

const rows = (scores) => scores.map((impact_score, i) => ({ impact_score, cluster_id: `c${i}` }));

describe('NewsTab tier treatment', () => {
  it('maps every HIGH-row direction to the intended border class', () => {
    expect(tierBorderFor('HIGH', 'bullish')).toBe('border-teal-400');
    expect(tierBorderFor('HIGH', 'bull')).toBe('border-teal-400');
    expect(tierBorderFor('HIGH', 'bearish')).toBe('border-rose-400');
    expect(tierBorderFor('HIGH', 'bear')).toBe('border-rose-400');
    expect(tierBorderFor('HIGH', 'neutral')).toBe('border-slate-500');
    expect(tierBorderFor('HIGH', 'mixed')).toBe('border-slate-500');
    expect(tierBorderFor('HIGH', null)).toBe('border-slate-500');
  });

  it('caps HIGH at 4 rows on the full news feed', () => {
    const scores = Array.from({ length: 400 }, (_, i) => 400 - i);
    expect(tierCutoffsFor(rows(scores)).hi).toBe(4);
  });

  it('includes a short tie run when that is as close as excluding it', () => {
    const scores = [90, 80, 70, 64, 64, ...Array(35).fill(10)];
    expect(tierCutoffsFor(rows(scores)).hi).toBe(5);
  });

  it('excludes a long tie run when excluding stays closer to target', () => {
    const scores = [90, 80, 70, ...Array(10).fill(64), ...Array(27).fill(10)];
    expect(tierCutoffsFor(rows(scores)).hi).toBe(3);
  });

  it('keeps the HIGH floor when a tie run starts at the first row', () => {
    expect(tierCutoffsFor(rows([64, 64, 64, 64, 64])).hi).toBe(5);
  });

  it('does not split ties at the MEDIUM boundary either', () => {
    const scores = [100, 90, 80, 70, ...Array(11).fill(60), 55, 55, ...Array(24).fill(10)];
    expect(tierCutoffsFor(rows(scores)).medEnd).toBe(17);
  });
});
