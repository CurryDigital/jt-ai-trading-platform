import React, { useState, useEffect, useMemo } from 'react';
import { api, fmtAge } from '../utils';

const COLS = [
  { key: 'ticker',             label: 'Ticker',    sub: null },
  { key: 'asset_class',        label: 'Asset',     sub: null },
  { key: 'fusion_signal',      label: 'Signal',    sub: null },
  { key: 'liquidity_momentum', label: 'Liquidity', sub: 'momentum' },
  { key: 'pressure_value',     label: 'Pressure',  sub: 'value' },
  { key: 'shock_warning',      label: 'Shock',     sub: null },
  { key: 'reasoning',          label: 'Reasoning',  sub: null },
];

const signalChip = (s) => {
  if (s === 'LONG')  return 'qr-chip qr-chip-emerald';
  if (s === 'SHORT') return 'qr-chip qr-chip-rose';
  return 'qr-chip qr-chip-slate';
};

const PctBar = ({ value, color }) => {
  const pct = Math.max(0, Math.min(1, value ?? 0)) * 100;
  return (
    <div className="flex items-center gap-1.5 min-w-[90px]">
      <div className="flex-1 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="qr-num text-[11px] w-[38px] text-right">{pct.toFixed(0)}%</span>
    </div>
  );
};

export const HftMatrix = () => {
  const [rows, setRows] = useState(null);
  const [err, setErr] = useState(false);
  const [refreshedAt, setRefreshedAt] = useState(null);
  const [sort, setSort] = useState({ key: 'ticker', dir: 'asc' });

  const load = async () => {
    const res = await api.get('/api/hft/matrix');
    if (res) {
      setRows(Array.isArray(res) ? res : []);
      setErr(false);
    } else {
      setRows((prev) => prev ?? []);
      setErr(true);
    }
    setRefreshedAt(new Date().toISOString());
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, []);

  const toggle = (key) =>
    setSort((s) =>
      s.key === key ? { key, dir: s.dir === 'asc' ? 'desc' : 'asc' } : { key, dir: 'asc' }
    );

  const sorted = useMemo(() => {
    if (!rows || rows.length === 0) return [];
    const { key, dir } = sort;
    const m = dir === 'asc' ? 1 : -1;
    return [...rows].sort((a, b) => {
      const av = a[key], bv = b[key];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === 'boolean') return (av === bv ? 0 : av ? -1 : 1) * m;
      if (typeof av === 'number') return (av - bv) * m;
      return String(av).localeCompare(String(bv)) * m;
    });
  }, [rows, sort]);

  /* ---------- loading state ---------- */
  if (rows === null) {
    return (
      <div className="qr-surface px-3 py-2.5 flex items-center gap-2 text-[11px] text-slate-500">
        <div className="w-3 h-3 border-2 border-slate-700 border-t-blue-500 rounded-full animate-spin" />
        Loading HFT matrix…
      </div>
    );
  }

  /* ---------- empty / pipeline-not-ready state ---------- */
  if (rows.length === 0) {
    return (
      <div className="qr-surface px-4 py-6 text-center">
        <p className="text-sm text-slate-400">HFT matrix not yet populated — waiting for DE pipeline</p>
        {err && <p className="text-[10px] text-slate-600 mt-1">Endpoint returned error or empty</p>}
        {refreshedAt && (
          <p className="text-[10px] text-slate-600 mt-1">Last attempt {fmtAge(refreshedAt)} ago</p>
        )}
      </div>
    );
  }

  return (
    <div className="qr-surface overflow-hidden">
      {/* header bar */}
      <div className="px-3 py-2 border-b border-white/[0.05] flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-white">HFT Matrix</span>
          <span className="qr-chip qr-chip-amber text-[10px]">{rows.length} instruments</span>
        </div>
        <span className="qr-num text-[10px] text-slate-500">
          upd {fmtAge(refreshedAt)}
          {err && <span className="text-rose-400 ml-1">(stale)</span>}
        </span>
      </div>

      {/* table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-white/[0.06]">
              {COLS.map((c) => (
                <th
                  key={c.key}
                  className="qr-label py-1.5 px-2 cursor-pointer select-none hover:text-white text-left"
                  onClick={() => toggle(c.key)}
                >
                  {c.label}
                  {sort.key === c.key && (
                    <span className="ml-0.5 text-blue-400">{sort.dir === 'asc' ? '↑' : '↓'}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/[0.04]">
            {sorted.map((r) => (
              <tr key={r.ticker} className="qr-tr-hover">
                {/* Ticker */}
                <td className="py-1 px-2 qr-num text-white font-medium">{r.ticker}</td>
                {/* Asset class */}
                <td className="py-1 px-2 text-[10px] text-slate-500">{r.asset_class}</td>
                {/* Signal */}
                <td className="py-1 px-2">
                  <span className={signalChip(r.fusion_signal)}>{r.fusion_signal}</span>
                </td>
                {/* Liquidity momentum bar */}
                <td className="py-1 px-2">
                  <PctBar value={r.liquidity_momentum} color="bg-blue-500" />
                </td>
                {/* Pressure bar */}
                <td className="py-1 px-2">
                  <PctBar value={r.pressure_value} color="bg-violet-500" />
                </td>
                {/* Shock warning */}
                <td className="py-1 px-2">
                  {r.shock_warning ? (
                    <span className="qr-chip qr-chip-rose">SHOCK</span>
                  ) : (
                    <span className="text-[10px] text-slate-600">—</span>
                  )}
                </td>
                {/* Reasoning */}
                <td className="py-1 px-2 text-[11px] text-slate-400 max-w-[260px] truncate">
                  {r.reasoning || '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default HftMatrix;
