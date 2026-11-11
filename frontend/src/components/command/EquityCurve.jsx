// Command center — P&L / equity curve, visible in the Performance panel
// (never behind a tab). The caller labels the series basis (realized P&L vs
// genuine equity) and window.

import React, { useState, useEffect, useRef } from 'react';
import { fmtK, pnlCl } from '../../utils';
import { sK } from './format';

export function EquityCurve({ data, color, height = 200, emptyLabel = 'No history yet' }) {
  const ref = useRef(null);
  const [width, setWidth] = useState(600);
  const [hover, setHover] = useState(null);
  useEffect(() => {
    if (!ref.current) return undefined;
    const ro = new ResizeObserver((entries) => {
      setWidth(Math.max(320, Math.round(entries[0].contentRect.width)));
    });
    ro.observe(ref.current);
    return () => ro.disconnect();
  }, []);

  if (!data || data.length < 2) {
    return <div className="flex items-center justify-center text-[13px] text-slate-500 px-4" style={{ height: 96 }}>{emptyLabel}</div>;
  }
  const margin = { left: 52, right: 12, top: 10, bottom: 24 };
  const values = data.map(d => d.equity);
  const min = Math.min(...values), max = Math.max(...values), range = (max - min) || 1;
  const w = width, h = height;
  const plotW = w - margin.left - margin.right;
  const plotH = h - margin.top - margin.bottom;
  const x = (i) => margin.left + (i / (values.length - 1)) * plotW;
  const y = (v) => margin.top + plotH - ((v - min) / range) * plotH;
  const line = values.map((v, i) => `${x(i)},${y(v)}`).join(' ');
  const area = `${margin.left},${margin.top + plotH} ${line} ${margin.left + plotW},${margin.top + plotH}`;
  const id = 'jt-eq-grad';
  const yTicks = [min, (min + max) / 2, max];
  const crossesZero = min < 0 && max > 0;
  const monthTicks = data.map((d, i) => ({ i, date: new Date(d.d + 'T00:00:00') })).filter((d, i, arr) => {
    if (i === 0) return true;
    const prev = arr[i - 1].date;
    return d.date.getMonth() !== prev.getMonth() || d.date.getFullYear() !== prev.getFullYear();
  });

  const onMove = (e) => {
    const r = ref.current?.getBoundingClientRect();
    if (!r || r.width === 0) return;
    const px = (e.clientX - r.left) * (w / r.width);
    const frac = (px - margin.left) / plotW;
    const i = Math.round(frac * (values.length - 1));
    setHover(Math.max(0, Math.min(values.length - 1, i)));
  };

  const hd = hover != null ? data[hover] : null;

  return (
    <div ref={ref} className="relative px-2" onMouseMove={onMove} onMouseLeave={() => setHover(null)}>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full block" style={{ height: h }}>
        <defs>
          <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.28" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0, 0.5, 1].map(f => {
          const gy = margin.top + plotH * f;
          return <line key={f} x1={margin.left} y1={gy} x2={margin.left + plotW} y2={gy} stroke="rgba(255,255,255,0.08)" strokeWidth="1" vectorEffect="non-scaling-stroke" />;
        })}
        {crossesZero && (
          <line x1={margin.left} y1={y(0)} x2={margin.left + plotW} y2={y(0)} stroke="rgba(255,255,255,0.30)" strokeWidth="1" strokeDasharray="4 3" vectorEffect="non-scaling-stroke" />
        )}
        <polygon points={area} fill={`url(#${id})`} />
        <polyline points={line} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
        <line x1={margin.left} y1={margin.top} x2={margin.left} y2={margin.top + plotH} stroke="rgba(255,255,255,0.15)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
        <line x1={margin.left} y1={margin.top + plotH} x2={margin.left + plotW} y2={margin.top + plotH} stroke="rgba(255,255,255,0.15)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
        {yTicks.map((v, i) => (
          <text key={i} x={margin.left - 6} y={y(v) + 3.5} textAnchor="end" fill="rgba(148,163,184,0.9)" fontSize="10" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
            {fmtK(v)}
          </text>
        ))}
        {monthTicks.map((t, i) => (
          <text key={i} x={x(t.i)} y={h - 8} textAnchor="middle" fill="rgba(148,163,184,0.9)" fontSize="10" fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
            {t.date.toLocaleDateString('en-US', { month: 'short' })}
          </text>
        ))}
        {hover != null && (
          <>
            <line x1={x(hover)} y1={margin.top} x2={x(hover)} y2={margin.top + plotH} stroke="rgba(255,255,255,0.25)" strokeWidth="1" vectorEffect="non-scaling-stroke" />
            <circle cx={x(hover)} cy={y(values[hover])} r="3.5" fill={color} stroke="#0a0d12" strokeWidth="1.5" />
          </>
        )}
      </svg>
      {hd && (
        <div className="absolute pointer-events-none rounded bg-[#0a0d12] border border-white/[0.12] px-2 py-1 text-[11px] font-mono whitespace-nowrap"
          style={{ left: Math.min(Math.max(x(hover), 60), w - 110), top: 2, transform: 'translateX(-50%)' }}>
          <span className="text-slate-400">{hd.d}</span>
          <span className={`ml-2 font-bold ${pnlCl(hd.equity)}`}>{sK(hd.equity)}</span>
        </div>
      )}
    </div>
  );
}
