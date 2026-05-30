export function formatTimeAgo(timestamp) {
  if (!timestamp) return '';
  const diff = Date.now() - new Date(timestamp).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export function extractSymbols(name) {
  if (!name) return [];
  const matches = name.match(/[A-Z]{1,5}/g) || [];
  const exclude = new Set(['SL', 'TP', 'RSI', 'MACD', 'EMA', 'SMA', 'ATR', 'VWAP', 'IV', 'RV', 'USD', 'EUR', 'GBP', 'JPY', 'BTC', 'ETH']);
  return matches.filter(s => !exclude.has(s) && s.length >= 2);
}

export const STATUS_COLORS = {
  pending: 'bg-slate-600/20 text-slate-400',
  backtesting: 'bg-blue-500/20 text-blue-400',
  risk_review: 'bg-amber-500/20 text-amber-400',
  qa_review: 'bg-violet-500/20 text-violet-400',
  approved: 'bg-emerald-500/20 text-emerald-400',
  deployed: 'bg-emerald-500/30 text-emerald-300',
  rejected: 'bg-rose-500/20 text-rose-400',
  retired: 'bg-slate-700/30 text-slate-500',
  golden: 'bg-amber-500/30 text-amber-300',
};

export const WORK_TYPE_COLORS = {
  risk_review: 'bg-amber-500/20 text-amber-400',
  qa_review: 'bg-violet-500/20 text-violet-400',
  backtest: 'bg-blue-500/20 text-blue-400',
  research: 'bg-cyan-500/20 text-cyan-400',
};

export const LEGACY_AGENT_MAP = {
  'research-agent': { name: 'Research', icon: '🔍' },
  'qa-agent':       { name: 'QA', icon: '🚦' },
  'risk-agent':     { name: 'Risk', icon: '🛡️' },
  'etl-agent':      { name: 'ETL', icon: '🏭' },
  'scrum-agent':    { name: 'ScrumMaster', icon: '📋' },
};

export function resolveAgent(agentId, registry = {}) {
  if (registry[agentId]) return registry[agentId];
  if (LEGACY_AGENT_MAP[agentId]) return LEGACY_AGENT_MAP[agentId];
  return { name: agentId, icon: '🤖' };
}
