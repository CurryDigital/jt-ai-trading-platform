import { useState, useEffect } from 'react';

// Utils - Compact formatting functions
export const fmt = (n, d = 2) => n == null || isNaN(n) ? '—' : n.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
export const fmtK = (n) => n == null ? '—' : Math.abs(n) >= 1e6 ? `$${(n/1e6).toFixed(1)}M` : Math.abs(n) >= 1e3 ? `$${(n/1e3).toFixed(1)}K` : `$${n.toFixed(0)}`;
export const fmtPct = (n) => n == null ? '—' : `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`;
export const pnlCl = (v) => v == null ? 'text-slate-500' : v >= 0 ? 'text-emerald-400' : 'text-rose-400';
export const pnlBg = (v) => v == null ? 'bg-slate-800' : v >= 0 ? 'bg-emerald-500/10' : 'bg-rose-500/10';

// Quant-researcher formatters
export const fmtNum = (n, d = 2) => n == null || isNaN(n) ? '—' : Number(n).toFixed(d);
export const fmtSigned = (n, d = 2) => n == null ? '—' : `${n >= 0 ? '+' : ''}${Number(n).toFixed(d)}`;
export const fmtBps = (n) => n == null ? '—' : `${n >= 0 ? '+' : ''}${(n * 100).toFixed(0)}bp`;
export const fmtTime = (d) => d == null ? '—' : new Date(d).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
export const fmtAge = (d) => {
  if (!d) return '—';
  const ms = Date.now() - new Date(d).getTime();
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s/60)}m`;
  if (s < 86400) return `${Math.floor(s/3600)}h`;
  return `${Math.floor(s/86400)}d`;
};

// Multi-timezone clock helper for quant researchers
export const marketClock = () => {
  const now = new Date();
  const fmt = (tz) => now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: tz });
  return {
    hkt: fmt('Asia/Hong_Kong'),
    nyc: fmt('America/New_York'),
    lon: fmt('Europe/London'),
    utc: fmt('UTC'),
  };
};

// Market open status
export const marketStatus = () => {
  const now = new Date();
  const day = now.getUTCDay(); // 0=Sun, 6=Sat
  const utcH = now.getUTCHours();
  const utcM = now.getUTCMinutes();
  const utcMin = utcH * 60 + utcM;
  const isWeekday = day >= 1 && day <= 5;

  // HK: 01:30-08:00 UTC, NYC: 14:30-21:00 UTC, LON: 08:00-16:30 UTC
  return {
    hk:  isWeekday && utcMin >= 90  && utcMin < 480,
    lon: isWeekday && utcMin >= 480 && utcMin < 990,
    nyc: isWeekday && utcMin >= 870 && utcMin < 1260,
  };
};

// Compact number formatter
export const compact = (n) => {
  if (n == null || isNaN(n)) return '—';
  const abs = Math.abs(n);
  if (abs >= 1e9) return `${(n/1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${(n/1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `${(n/1e3).toFixed(1)}K`;
  return n.toFixed(n % 1 === 0 ? 0 : 2);
};

// API helpers with error handling
export const api = {
  get: async (url) => {
    try {
      const res = await fetch(url);
      return res.ok ? await res.json() : null;
    } catch {
      return null;
    }
  },
  post: async (url, body) => {
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      return res.ok ? await res.json() : null;
    } catch {
      return null;
    }
  }
};

// Data fetching hook
export const useData = (urls) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const urlKey = JSON.stringify(urls);

  useEffect(() => {
    const fetchData = async () => {
      const results = await Promise.all(
        urls.map(url => api.get(url).catch(() => null))
      );
      setData(results);
      setLoading(false);
    };
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [urlKey]);

  return { data, loading };
};
