import { useState, useEffect, useRef } from 'react';

// Utils - Compact formatting functions
export const fmt = (n, d = 2) => n == null || isNaN(n) ? '—' : n.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
export const fmtK = (n) => n == null ? '—' : Math.abs(n) >= 1e6 ? `$${(n/1e6).toFixed(1)}M` : Math.abs(n) >= 1e3 ? `$${(n/1e3).toFixed(1)}K` : `$${n.toFixed(0)}`;
// Currency-aware money formatting (t_22dee93d): NEVER render an account
// figure with '$' unless it is USD-labeled. Conversion itself is backend-only
// (app/services/fx.py / qr_etl conversion layer); the frontend only renders
// backend-labeled values. Unlabeled -> explicit marker, never a bare '$'.
export const CCY_SYMBOL = { USD: '$', HKD: 'HK$', CNY: 'CN¥', EUR: '€', GBP: '£', JPY: '¥' };
export const fmtKCcy = (n, ccy) => {
  if (n == null) return '—';
  const sym = CCY_SYMBOL[ccy];
  const core = Math.abs(n) >= 1e6 ? `${(n / 1e6).toFixed(1)}M` : Math.abs(n) >= 1e3 ? `${(n / 1e3).toFixed(1)}K` : `${Number(n).toFixed(0)}`;
  if (sym) return `${sym}${core}`;
  return ccy ? `${core} ${ccy}` : `${core} (ccy unlabeled)`;
};
export const fmtCcy = (n, ccy, d = 0) => {
  if (n == null) return '—';
  const sym = CCY_SYMBOL[ccy];
  const core = Number(n).toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
  if (sym) return `${sym}${core}`;
  return ccy ? `${core} ${ccy}` : `${core} (ccy unlabeled)`;
};
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

// Auth token helpers (stored in localStorage; backend reads Authorization header)
const TOKEN_KEY = 'jtcml.token';
export const getToken = () => { try { return localStorage.getItem(TOKEN_KEY); } catch { return null; } };
export const setToken = (t) => { try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY); } catch {} };
export const clearToken = () => setToken(null);

// Internal: bubble 401s up so the App can show the login page
const _onUnauthorized = { fn: () => {} };
export const onUnauthorized = (fn) => { _onUnauthorized.fn = fn; };

const _authHeaders = () => {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
};

// API helpers with error handling and timeout
const API_TIMEOUT_MS = 10000;

// Drop-in fetch() replacement with a hard AbortController timeout. Returns the
// raw Response (unlike api.get which returns parsed JSON) so existing
// `res.ok` / `res.status` call-sites work unchanged. Throws on abort/network
// error — callers already wrap in try/catch.
export const fetchWithTimeout = async (url, opts = {}, ms = API_TIMEOUT_MS) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), ms);
  try {
    return await fetch(url, { ...opts, signal: controller.signal });
  } finally {
    clearTimeout(timeoutId);
  }
};

// DB health monitor: polls /api/system/health every 30s and exposes the last
// known status app-wide, so an outage banner can render regardless of which
// tab is mounted. Statuses: 'unknown' (no answer yet) | 'ok' | 'degraded'
// (health answered but db != connected) | 'down' (health endpoint itself
// unreachable/timed out — backend or edge dead).
const DB_HEALTH_POLL_MS = 30000;
const _dbHealth = { status: 'unknown', listeners: new Set() };
let _dbHealthStarted = false;

const _setDbHealth = (status) => {
  if (_dbHealth.status === status) return;
  _dbHealth.status = status;
  _dbHealth.listeners.forEach(fn => { try { fn(status); } catch {} });
};

const _pollDbHealth = async () => {
  try {
    // 30s budget: on page load the browser's 6-per-origin connections are
    // saturated by other hanging API calls, so the health poll can be queued
    // behind ~10s of fail-fast aborts; the endpoint itself takes ~10s to
    // answer 'degraded' when the DB pool is wedged. 30s lands the correct
    // label (DATABASE vs BACKEND unreachable) on the first poll.
    const res = await fetchWithTimeout('/api/system/health', {}, 30000);
    if (!res.ok) { _setDbHealth('down'); return; }
    const json = await res.json();
    _setDbHealth(json && json.db === 'connected' && json.status === 'ok' ? 'ok' : 'degraded');
  } catch {
    _setDbHealth('down');
  }
};

export const useDbHealth = () => {
  const [status, setStatus] = useState(_dbHealth.status);
  useEffect(() => {
    if (!_dbHealthStarted) {
      _dbHealthStarted = true;
      _pollDbHealth();
      setInterval(_pollDbHealth, DB_HEALTH_POLL_MS);
    }
    const fn = (s) => setStatus(s);
    _dbHealth.listeners.add(fn);
    // Re-sync in case status changed between render and subscribe
    setStatus(_dbHealth.status);
    return () => { _dbHealth.listeners.delete(fn); };
  }, []);
  return status;
};

// GET micro-cache + in-flight dedupe. Many components poll the same endpoints
// (13 call-sites hit /api/execution/global-mode alone); sharing one request per
// URL per 3s window collapses those duplicates without touching any component.
const GET_CACHE_TTL_MS = 3000;
const _getCache = new Map(); // url -> { ts, promise }

const _rawGet = async (url) => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
    const res = await fetch(url, { headers: _authHeaders(), signal: controller.signal });
    clearTimeout(timeoutId);
    if (res.status === 401) { _onUnauthorized.fn(); return null; }
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
};

export const api = {
  get: (url) => {
    const hit = _getCache.get(url);
    if (hit && Date.now() - hit.ts < GET_CACHE_TTL_MS) return hit.promise;
    const promise = _rawGet(url);
    _getCache.set(url, { ts: Date.now(), promise });
    if (_getCache.size > 200) {
      const cutoff = Date.now() - GET_CACHE_TTL_MS;
      for (const [k, v] of _getCache) if (v.ts < cutoff) _getCache.delete(k);
    }
    return promise;
  },
  post: async (url, body) => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT_MS);
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ..._authHeaders() },
        body: JSON.stringify(body),
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      if (res.status === 401) { _onUnauthorized.fn(); return null; }
      return res.ok ? await res.json() : null;
    } catch {
      return null;
    }
  }
};

// Visibility-aware polling: runs `fn` immediately and every `ms`, but stops
// while the browser tab is hidden and fires again the moment it's visible.
// With ~30 pollers across the app, hidden tabs were hammering the RDS-backed
// API around the clock — this makes background tabs free.
export const usePoll = (fn, ms, delayMs = 0) => {
  const fnRef = useRef(fn);
  useEffect(() => { fnRef.current = fn; });
  useEffect(() => {
    let id = null, dId = null;
    const tick = () => fnRef.current();
    const start = () => {
      if (id != null || dId != null) return;
      // Optional first-fire delay staggers mount-time request fan-out so a
      // busy page doesn't wedge the backend's small DB pool (t_87ccf8a4).
      if (delayMs > 0) {
        dId = setTimeout(() => { dId = null; tick(); id = setInterval(tick, ms); }, delayMs);
      } else {
        tick(); id = setInterval(tick, ms);
      }
    };
    const stop = () => {
      if (dId != null) { clearTimeout(dId); dId = null; }
      if (id != null) { clearInterval(id); id = null; }
    };
    const onVis = () => (document.hidden ? stop() : start());
    document.addEventListener('visibilitychange', onVis);
    onVis();
    return () => { stop(); document.removeEventListener('visibilitychange', onVis); };
  }, [ms, delayMs]);
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
