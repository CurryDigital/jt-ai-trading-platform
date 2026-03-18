import React, { useState } from 'react';

/**
 * S019 Strategy Criteria Display Component
 * Shows BUY/SELL criteria breakdown for the Momentum+Quality+Trend strategy
 */

const S019_CRITERIA = {
  buy: [
    { id: 'trend', label: 'Trend', desc: 'Price > SMA20 > SMA50 > SMA200' },
    { id: 'momentum', label: 'Momentum', desc: '20d return > 5% AND 3mo > 10%' },
    { id: 'quality', label: 'Quality', desc: 'ROE > 15% AND Debt/Equity < 0.5' },
    { id: 'value', label: 'Value', desc: 'P/E < 25 AND P/B < 3' }
  ],
  sell: [
    { id: 'price_sma200', label: 'Price < SMA200', desc: 'Price below 200-day moving average' },
    { id: 'return_20d', label: '20-day return < -5%', desc: 'Negative 20-day momentum' },
    { id: 'roe_low', label: 'ROE < 10%', desc: 'Low return on equity' }
  ]
};

export const S019CriteriaDisplay = ({ ticker, signal, score, criteriaMet = [] }) => {
  const [expanded, setExpanded] = useState(false);
  
  // Parse criteria met from backend (could be array of criterion IDs or labels)
  const metSet = new Set(criteriaMet.map(c => 
    typeof c === 'string' ? c.toLowerCase().replace(/\s+/g, '_') : c
  ));
  
  const isBuySignal = signal === 'BUY';
  const isSellSignal = signal === 'SELL';
  
  // Count how many buy criteria are met
  const buyCriteriaMet = S019_CRITERIA.buy.filter(c => 
    metSet.has(c.id) || metSet.has(c.label.toLowerCase())
  ).length;
  
  // Count how many sell criteria are met  
  const sellCriteriaMet = S019_CRITERIA.sell.filter(c =>
    metSet.has(c.id) || metSet.has(c.label.toLowerCase())
  ).length;
  
  return (
    <div className="mt-2 bg-slate-800/50 rounded border border-white/5 overflow-hidden">
      {/* Header - Always visible */}
      <button 
        onClick={() => setExpanded(!expanded)}
        className="w-full px-2 py-1.5 flex items-center justify-between hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold text-slate-300">S019 Criteria</span>
          <span className="text-[9px] text-slate-500">{ticker}</span>
        </div>
        <div className="flex items-center gap-2">
          {/* Score pill */}
          <span className={`text-[9px] px-1.5 py-0.5 rounded font-mono ${
            score >= 75 ? 'bg-emerald-500/20 text-emerald-400' :
            score >= 50 ? 'bg-amber-500/20 text-amber-400' :
            'bg-rose-500/20 text-rose-400'
          }`}>
            {score}/100
          </span>
          {/* Expand icon */}
          <span className="text-[10px] text-slate-500">
            {expanded ? '▼' : '▶'}
          </span>
        </div>
      </button>
      
      {/* Expanded Details */}
      {expanded && (
        <div className="px-2 pb-2 space-y-2">
          {/* BUY Criteria Section */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-bold text-emerald-400">BUY Criteria (need ALL 4)</span>
              <span className="text-[9px] text-slate-500">{buyCriteriaMet}/4 met</span>
            </div>
            {S019_CRITERIA.buy.map((criterion) => {
              const isMet = metSet.has(criterion.id) || metSet.has(criterion.label.toLowerCase());
              return (
                <div key={criterion.id} className="flex items-start gap-2 text-[9px]">
                  <span className={`mt-0.5 ${isMet ? 'text-emerald-400' : 'text-slate-600'}`}>
                    {isMet ? '✓' : '○'}
                  </span>
                  <div className="flex-1">
                    <span className={isMet ? 'text-slate-300' : 'text-slate-500'}>
                      {criterion.label}
                    </span>
                    <span className="text-slate-600 ml-1">— {criterion.desc}</span>
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Divider */}
          <div className="border-t border-white/5" />
          
          {/* SELL Criteria Section */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-[9px] font-bold text-rose-400">SELL Triggers (ANY 2 = SELL)</span>
              <span className="text-[9px] text-slate-500">{sellCriteriaMet}/3 met</span>
            </div>
            {S019_CRITERIA.sell.map((criterion) => {
              const isMet = metSet.has(criterion.id) || metSet.has(criterion.label.toLowerCase());
              return (
                <div key={criterion.id} className="flex items-start gap-2 text-[9px]">
                  <span className={`mt-0.5 ${isMet ? 'text-rose-400' : 'text-slate-600'}`}>
                    {isMet ? '✗' : '○'}
                  </span>
                  <div className="flex-1">
                    <span className={isMet ? 'text-slate-300' : 'text-slate-500'}>
                      {criterion.label}
                    </span>
                    <span className="text-slate-600 ml-1">— {criterion.desc}</span>
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Legend */}
          <div className="pt-1 border-t border-white/5 text-[8px] text-slate-600">
            Score = % of BUY criteria met. SELL overrides if ≥2 triggers active.
          </div>
        </div>
      )}
    </div>
  );
};

export default S019CriteriaDisplay;
