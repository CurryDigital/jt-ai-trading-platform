import React, { useState, useEffect } from 'react';

// Technical Stock Detail Modal
// Shows price chart with SMA lines and RSI indicator

export const StockDetailModal = ({ ticker, isOpen, onClose }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeframe, setTimeframe] = useState('ytd'); // 1m, ytd, 12m, all

  useEffect(() => {
    if (isOpen && ticker) {
      fetchStockDetail();
    }
  }, [isOpen, ticker, timeframe]);

  const fetchStockDetail = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/stocks/${ticker}?timeframe=${timeframe}`);
      if (!response.ok) throw new Error('Failed to fetch');
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const timeframeLabels = {
    '1m': '1 Month',
    'ytd': 'YTD',
    '12m': '12 Months', 
    'all': 'All Time'
  };

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="relative w-full max-w-6xl max-h-[95vh] rounded-2xl bg-slate-900 border border-white/10 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
              <span className="text-xl font-black text-blue-400">{ticker?.slice(0, 2)}</span>
            </div>
            <div>
              <h2 className="text-2xl font-black text-white">{ticker}</h2>
              {data && (
                <div className="flex items-center gap-3 text-sm">
                  <span className="text-slate-400">{data.market}</span>
                  <span className="text-slate-600">•</span>
                  <span className="font-mono text-white">${data.price?.toFixed(2)}</span>
                  <PnLBadge value={data.daily_change} />
                </div>
              )}
            </div>
          </div>
          
          {/* Timeframe Selector */}
          <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-800/50 border border-white/5">
            {Object.entries(timeframeLabels).map(([key, label]) => (
              <button
                key={key}
                onClick={() => setTimeframe(key)}
                className={`px-3 py-1.5 rounded text-xs font-bold uppercase tracking-wider transition-all ${
                  timeframe === key
                    ? 'bg-white text-black'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          
          <button 
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
          >
            <svg width="24" height="24" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(95vh-100px)] space-y-6">
          {loading ? (
            <div className="flex items-center justify-center h-96">
              <div className="w-8 h-8 border-2 border-slate-600 border-t-blue-500 rounded-full animate-spin" />
            </div>
          ) : error ? (
            <div className="p-8 text-center text-rose-400">
              Error loading data: {error}
            </div>
          ) : data ? (
            <>
              {/* Technical Indicators Row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* RSI Card */}
                <IndicatorCard 
                  label="RSI (14)"
                  value={data.indicators?.rsi}
                  suffix=""
                  signal={data.indicators?.rsi_signal}
                  signalColors={{
                    'OVERBOUGHT': 'text-rose-400 bg-rose-500/10',
                    'OVERSOLD': 'text-emerald-400 bg-emerald-500/10',
                    'NEUTRAL': 'text-slate-400 bg-slate-500/10'
                  }}
                />
                
                {/* SMA Signal */}
                <IndicatorCard 
                  label="SMA Trend"
                  value={data.indicators?.sma_signal}
                  isText={true}
                  signal={data.indicators?.sma_signal}
                  signalColors={{
                    'BULLISH': 'text-emerald-400 bg-emerald-500/10',
                    'BEARISH': 'text-rose-400 bg-rose-500/10',
                    'NEUTRAL': 'text-slate-400 bg-slate-500/10'
                  }}
                />
                
                {/* Win Rate */}
                <IndicatorCard 
                  label="Win Rate"
                  value={data.win_rate}
                  suffix="%"
                  format={v => (v * 100).toFixed(0)}
                />
                
                {/* AI Score */}
                <IndicatorCard 
                  label="AI Score"
                  value={data.final_score}
                  suffix="%"
                  format={v => (v * 100).toFixed(0)}
                />
              </div>

              {/* Price Chart with SMA */}
              <div className="p-4 rounded-xl bg-slate-800/50 border border-white/5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Price & Moving Averages</h3>
                  <div className="flex items-center gap-3 text-xs">
                    <LegendItem color="#3b82f6" label="Price" />
                    <LegendItem color="#f59e0b" label="SMA 20" />
                    <LegendItem color="#8b5cf6" label="SMA 50" />
                    <LegendItem color="#ef4444" label="SMA 200" />
                  </div>
                </div>
                <TechnicalChart 
                  data={data.chart_data} 
                  showSMA={true}
                  height={280}
                />
              </div>

              {/* RSI Chart */}
              <div className="p-4 rounded-xl bg-slate-800/50 border border-white/5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">RSI (Relative Strength Index)</h3>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <span className="text-rose-400">Overbought (&gt;70)</span>
                    <span>•</span>
                    <span className="text-emerald-400">Oversold (&lt;30)</span>
                  </div>
                </div>
                <RSIChart data={data.chart_data} height={120} />
              </div>

              {/* SMA Levels */}
              {data.indicators?.sma_20 && (
                <div className="grid grid-cols-3 gap-4">
                  <SMALevelCard period="20" value={data.indicators.sma_20} price={data.price} />
                  {data.indicators.sma_50 && <SMALevelCard period="50" value={data.indicators.sma_50} price={data.price} />}
                  {data.indicators.sma_200 && <SMALevelCard period="200" value={data.indicators.sma_200} price={data.price} />}
                </div>
              )}

              {/* Strategy Info */}
              {data.strategy_tags?.length > 0 && (
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-slate-500 uppercase">Signals:</span>
                  {data.strategy_tags.map((tag, i) => (
                    <span key={i} className="px-2 py-1 rounded bg-blue-500/10 text-blue-400 text-xs font-bold">
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {/* Logic Summary */}
              {data.logic_summary && (
                <div className="p-4 rounded-lg bg-slate-800/30 border border-white/5">
                  <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">Analysis</p>
                  <p className="text-sm text-slate-300">{data.logic_summary}</p>
                </div>
              )}
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
};

const PnLBadge = ({ value }) => {
  const isPositive = value >= 0;
  return (
    <span className={`text-xs font-mono font-bold ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`}>
      {isPositive ? '+' : ''}{value?.toFixed(2)}%
    </span>
  );
};

const IndicatorCard = ({ label, value, suffix = '', signal, signalColors = {}, format, isText = false }) => {
  const displayValue = isText ? value : (format ? format(value) : value);
  const signalClass = signalColors[signal] || 'text-slate-400 bg-slate-500/10';
  
  return (
    <div className="p-4 rounded-xl bg-slate-800/50 border border-white/5">
      <p className="text-xs text-slate-500 uppercase tracking-wider mb-2">{label}</p>
      <div className="flex items-center justify-between">
        <span className="text-2xl font-black text-white">
          {displayValue !== null && displayValue !== undefined ? displayValue : '--'}
          {suffix && !isText && <span className="text-sm text-slate-500">{suffix}</span>}
        </span>
        {signal && (
          <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${signalClass}`}>
            {signal}
          </span>
        )}
      </div>
    </div>
  );
};

const LegendItem = ({ color, label }) => (
  <div className="flex items-center gap-1.5">
    <div className="w-3 h-0.5 rounded-full" style={{ backgroundColor: color }} />
    <span className="text-slate-400">{label}</span>
  </div>
);

const SMALevelCard = ({ period, value, price }) => {
  const diff = ((price - value) / value) * 100;
  const isAbove = diff > 0;
  
  return (
    <div className="p-3 rounded-lg bg-slate-800/30 border border-white/5">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-slate-500">SMA {period}</span>
        <span className={`text-xs font-bold ${isAbove ? 'text-emerald-400' : 'text-rose-400'}`}>
          {isAbove ? '+' : ''}{diff.toFixed(1)}%
        </span>
      </div>
      <p className="text-lg font-mono font-bold text-white">${value.toFixed(2)}</p>
    </div>
  );
};

const TechnicalChart = ({ data, showSMA = true, height = 280 }) => {
  if (!data || data.length === 0) return null;
  
  const width = 800;
  const padding = { top: 20, right: 20, bottom: 30, left: 50 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  
  // Get min/max for scaling
  const prices = data.map(d => d.price);
  const sma20s = data.map(d => d.sma_20).filter(Boolean);
  const sma50s = data.map(d => d.sma_50).filter(Boolean);
  const sma200s = data.map(d => d.sma_200).filter(Boolean);
  
  const allValues = [...prices, ...sma20s, ...sma50s, ...sma200s];
  const min = Math.min(...allValues);
  const max = Math.max(...allValues);
  const range = max - min || 1;
  
  const scaleY = (val) => chartHeight - ((val - min) / range) * chartHeight + padding.top;
  const scaleX = (i) => (i / (data.length - 1)) * chartWidth + padding.left;
  
  const createPath = (key) => {
    return data
      .map((d, i) => {
        if (d[key] === null || d[key] === undefined) return null;
        return `${scaleX(i)},${scaleY(d[key])}`;
      })
      .filter(Boolean)
      .join(' ');
  };
  
  const pricePath = createPath('price');
  const sma20Path = createPath('sma_20');
  const sma50Path = createPath('sma_50');
  const sma200Path = createPath('sma_200');
  
  // Grid lines
  const gridLines = [0, 0.25, 0.5, 0.75, 1].map(pos => ({
    y: padding.top + pos * chartHeight,
    label: (max - pos * range).toFixed(0)
  }));
  
  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* Grid lines */}
      {gridLines.map((line, i) => (
        <g key={i}>
          <line 
            x1={padding.left} 
            y1={line.y}
            x2={width - padding.right} 
            y2={line.y}
            stroke="rgba(255,255,255,0.05)"
            strokeDasharray="2"
          />
          <text x={padding.left - 10} y={line.y + 4} textAnchor="end" fill="#64748b" fontSize="10">
            ${line.label}
          </text>
        </g>
      ))}
      
      {/* SMA 200 */}
      {sma200Path && (
        <polyline fill="none" stroke="#ef4444" strokeWidth="1.5" points={sma200Path} opacity={0.8} />
      )}
      
      {/* SMA 50 */}
      {sma50Path && (
        <polyline fill="none" stroke="#8b5cf6" strokeWidth="1.5" points={sma50Path} opacity={0.8} />
      )}
      
      {/* SMA 20 */}
      {sma20Path && (
        <polyline fill="none" stroke="#f59e0b" strokeWidth="1.5" points={sma20Path} opacity={0.8} />
      )}
      
      {/* Price line - thicker on top */}
      <polyline fill="none" stroke="#3b82f6" strokeWidth="2" points={pricePath} />
      
      {/* X-axis labels (first, middle, last date) */}
      <text x={padding.left} y={height - 5} textAnchor="middle" fill="#64748b" fontSize="10">
        {data[0]?.date?.slice(5)}
      </text>
      <text x={width / 2} y={height - 5} textAnchor="middle" fill="#64748b" fontSize="10">
        {data[Math.floor(data.length / 2)]?.date?.slice(5)}
      </text>
      <text x={width - padding.right} y={height - 5} textAnchor="middle" fill="#64748b" fontSize="10">
        {data[data.length - 1]?.date?.slice(5)}
      </text>
    </svg>
  );
};

const RSIChart = ({ data, height = 120 }) => {
  if (!data || data.length === 0) return null;
  
  const width = 800;
  const padding = { top: 10, right: 20, bottom: 20, left: 50 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  
  const min = 0;
  const max = 100;
  const range = 100;
  
  const scaleY = (val) => chartHeight - ((val - min) / range) * chartHeight + padding.top;
  const scaleX = (i) => (i / (data.length - 1)) * chartWidth + padding.left;
  
  const rsiPath = data
    .map((d, i) => {
      if (d.rsi === null || d.rsi === undefined) return null;
      return `${scaleX(i)},${scaleY(d.rsi)}`;
    })
    .filter(Boolean)
    .join(' ');
  
  // Overbought (70) and Oversold (30) lines
  const overboughtY = scaleY(70);
  const oversoldY = scaleY(30);
  const midY = scaleY(50);
  
  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* Background zones */}
      <rect x={padding.left} y={padding.top} width={chartWidth} height={oversoldY - padding.top} fill="rgba(16, 185, 129, 0.05)" />
      <rect x={padding.left} y={overboughtY} width={chartWidth} height={padding.top + chartHeight - overboughtY} fill="rgba(244, 63, 94, 0.05)" />
      
      {/* Reference lines */}
      <line x1={padding.left} y1={overboughtY} x2={width - padding.right} y2={overboughtY} stroke="#f43f5e" strokeDasharray="4" opacity={0.5} />
      <line x1={padding.left} y1={midY} x2={width - padding.right} y2={midY} stroke="#64748b" strokeDasharray="2" opacity={0.3} />
      <line x1={padding.left} y1={oversoldY} x2={width - padding.right} y2={oversoldY} stroke="#10b981" strokeDasharray="4" opacity={0.5} />
      
      {/* Labels */}
      <text x={padding.left - 5} y={overboughtY + 3} textAnchor="end" fill="#f43f5e" fontSize="9">70</text>
      <text x={padding.left - 5} y={midY + 3} textAnchor="end" fill="#64748b" fontSize="9">50</text>
      <text x={padding.left - 5} y={oversoldY + 3} textAnchor="end" fill="#10b981" fontSize="9">30</text>
      
      {/* RSI line */}
      {rsiPath && (
        <polyline fill="none" stroke="#06b6d4" strokeWidth="2" points={rsiPath} />
      )}
      
      {/* X-axis labels */}
      <text x={padding.left} y={height - 3} textAnchor="middle" fill="#64748b" fontSize="9">
        {data[0]?.date?.slice(5)}
      </text>
      <text x={width - padding.right} y={height - 3} textAnchor="middle" fill="#64748b" fontSize="9">
        {data[data.length - 1]?.date?.slice(5)}
      </text>
    </svg>
  );
};

export default StockDetailModal;
