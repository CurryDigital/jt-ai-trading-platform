// Utils - Compact formatting functions
export const fmt = (n, d = 2) => n == null || isNaN(n) ? '—' : n.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
export const fmtK = (n) => n == null ? '—' : Math.abs(n) >= 1e6 ? `$${(n/1e6).toFixed(1)}M` : Math.abs(n) >= 1e3 ? `$${(n/1e3).toFixed(1)}K` : `$${n.toFixed(0)}`;
export const fmtPct = (n) => n == null ? '—' : `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`;
export const pnlCl = (v) => v == null ? 'text-slate-500' : v >= 0 ? 'text-emerald-400' : 'text-rose-400';
export const pnlBg = (v) => v == null ? 'bg-slate-800' : v >= 0 ? 'bg-emerald-500/10' : 'bg-rose-500/10';

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
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  
  React.useEffect(() => {
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
  }, urls);
  
  return { data, loading };
};
