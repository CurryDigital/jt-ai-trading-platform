import React, { useState, useEffect, useMemo } from 'react';

// --- UTILS & HELPERS ---
const parseRationale = (raw) => {
  if (!raw) return { mood: 'Neutral', highlights: [], body: '', industries: { short_term: [], long_term: [] } };
  if (typeof raw !== 'string') raw = JSON.stringify(raw);
  try {
    const data = JSON.parse(raw);
    return {
      mood: data.market_mood || 'Neutral',
      highlights: [data.conclusion].filter(Boolean),
      body: data.rationale || '',
      industries: data.recommended_industries || { short_term: [], long_term: [] }
    };
  } catch {
    const s = String(raw);
    return { mood: 'Neutral', highlights: [], body: s.slice(0, 160) + '...', industries: { short_term: [], long_term: [] } };
  }
};

const getStatusColor = (val, type = 'text') => {
  const isPos = typeof val === 'string' ? val.includes('+') : val > 0;
  if (type === 'text') return isPos ? 'text-emerald-400' : 'text-rose-400';
  if (type === 'bg') return isPos ? 'bg-emerald-500/10' : 'bg-rose-500/10';
  if (type === 'border') return isPos ? 'border-emerald-500/20' : 'border-rose-500/20';
  return '';
};

// --- CORE COMPONENTS ---

const StrategyInfoModal = ({ isOpen, onClose, tab }) => {
  if (!isOpen) return null;
  const content = {
    inventory: {
      title: "Portfolio Management",
      rationale: "Live capital deployment monitoring. This console integrates multi-factor risk assessment with real-time mark-to-market valuations.",
      kpis: [
        { name: "Avg Cost", desc: "Weighted entry price basis." },
        { name: "Mark Price", desc: "Real-time market value fetched via cluster sync." },
        { name: "P/L Yield", desc: "Total return relative to basis, including swap adjustments." }
      ]
    },
    research: {
      title: "Neural Intelligence",
      rationale: "Aggregated sentiment and regime analysis from the AI Swarm. Filters geopolitical noise into actionable market conclusions.",
      kpis: [
        { name: "Swarm Score", desc: "Neural confidence level (0-100%)." },
        { name: "Market Regime", desc: "Detected market state: Growth, Panic, or Stagnant." },
        { name: "Sentiment", desc: "NLP score of live news feeds." }
      ]
    },
    signals: {
      title: "Alpha Vectors",
      rationale: "Quantitative statistical drift models (Prophet) cross-validated by technical indicators and historical win rates.",
      kpis: [
        { name: "7D Prophet", desc: "Predicted 7-day price drift using seasonal decomposition." },
        { name: "Sharpe Ratio", desc: "Risk-adjusted return metric (Target > 1.0)." },
        { name: "Max Drawdown", desc: "Peak-to-trough historical risk profile." }
      ]
    }
  }[tab] || { title: "Strategy Guide", rationale: "Institutional trading protocols.", kpis: [] };

  return (
    <div className="fixed inset-0 z-[250] flex items-center justify-center p-4 md:p-6 bg-black/80 backdrop-blur-md animate-in fade-in duration-300">
      <div className="glass max-w-xl w-full rounded-[2.5rem] p-8 md:p-10 shadow-3xl border-white/10 relative">
        <button onClick={onClose} className="absolute top-6 right-6 p-2 rounded-full hover:bg-white/5 transition-colors text-slate-500">
          <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M15 5L5 15M5 5l10 10" /></svg>
        </button>
        <div className="space-y-6">
           <div className="space-y-1">
             <span className="text-[10px] font-black text-blue-500 uppercase tracking-[0.3em] font-outfit">Briefing</span>
             <h2 className="text-3xl font-black text-white font-outfit italic tracking-tight uppercase leading-none">{content.title}</h2>
           </div>
           <p className="text-base text-slate-300 italic font-medium leading-relaxed font-outfit">"{content.rationale}"</p>
           <div className="grid grid-cols-1 gap-4 pt-4 border-t border-white/5">
             {content.kpis.map((kpi, i) => (
               <div key={i} className="flex items-start gap-3">
                 <div className="h-1.5 w-1.5 rounded-full bg-blue-500 mt-1.5 shadow-[0_0_8px_#3b82f6]" />
                 <div>
                   <span className="text-xs font-bold text-white uppercase tracking-wider">{kpi.name}</span>
                   <p className="text-[11px] text-slate-500 font-medium">{kpi.desc}</p>
                 </div>
               </div>
             ))}
           </div>
           <button onClick={onClose} className="w-full py-4 rounded-2xl bg-white text-black text-[11px] font-black uppercase tracking-widest hover:bg-blue-500 hover:text-white transition-all shadow-xl font-outfit mt-4">Close Briefing</button>
        </div>
      </div>
    </div>
  );
};

const Sparkline = ({ data, color = "#3b82f6", width = 80, height = 24 }) => {
  if (!data || data.length === 0) return <div style={{width, height}} className="bg-white/5 rounded animate-pulse-soft" />;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const points = data.map((val, i) => 
    `${(i / (data.length - 1)) * width},${height - ((val - min) / range) * height}`
  ).join(' ');
  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline fill="none" stroke={color} strokeWidth="2.5" points={points} strokeLinejoin="round" strokeLinecap="round" className="drop-shadow-[0_0_8px_rgba(59,130,246,0.2)]" />
    </svg>
  );
};

const MetricBlock = ({ label, value, sub, color = 'text-white' }) => {
  const displayValue = (value === null || value === undefined || value === '') ? '---' : value;
  return (
    <div className="glass p-2.5 md:p-3 rounded-2xl border-white/5 flex flex-col justify-between font-outfit">
      <span className="text-[7px] md:text-[8px] text-slate-500 uppercase font-black tracking-widest block mb-1 leading-none">{label}</span>
      <div className="flex items-baseline gap-1">
        <span className={`text-sm md:text-base font-black font-mono leading-none ${color}`}>{displayValue}</span>
      </div>
    </div>
  );
};

const MacroPill = ({ label, value, change, est }) => {
  const isDrop = change < 0;
  const indexNames = { 'US': 'DJI', 'HK': 'HSI', 'EU': 'STOXX50', 'CN': 'SSE', 'SG': 'STI' };
  return (
    <div className="flex flex-col px-4 md:px-6 border-r border-white/5 last:border-0 min-w-[140px] md:min-w-[180px] group hover:bg-white/[0.03] transition-all py-3 cursor-default">
      <span className="text-[8px] font-black text-slate-500 uppercase tracking-widest font-outfit mb-1">{indexNames[label] || label}</span>
      <div className="flex items-center gap-2 mb-2">
          <span className="text-base md:text-lg font-bold text-white font-mono tracking-tighter leading-none">{value?.toLocaleString() || '---'}</span>
          <span className={`text-[9px] font-bold font-mono ${isDrop ? 'text-rose-500' : 'text-emerald-500'}`}>
              {isDrop ? '▼' : '▲'}{Math.abs(change || 0).toFixed(1)}%
          </span>
      </div>
      <div className="flex justify-between gap-1">
          {['1D', '1W'].map(p => (
              <span key={p} className={`text-[8px] font-bold font-mono tracking-tighter ${est?.[p.toLowerCase()]?.includes('+') ? 'text-blue-400' : 'text-orange-400'}`}>
                {p}:{est?.[p.toLowerCase()]?.replace('%','') || '-'}
              </span>
          ))}
      </div>
    </div>
  );
};

const NarrativeCard = ({ title, data }) => {
  const { mood, highlights, body, industries } = useMemo(() => parseRationale(data.rationale), [data.rationale]);
  const isUp = data.change >= 0;
  return (
    <div className="glass glass-hover p-5 md:p-6 rounded-3xl space-y-5 group relative overflow-hidden">
      <div className={`absolute top-0 right-0 w-24 h-24 -mr-8 -mt-8 rounded-full blur-3xl opacity-10 ${isUp ? 'bg-emerald-500' : 'bg-rose-500'}`} />
      
      <div className="flex justify-between items-start relative z-10">
        <div className="flex flex-col">
          <h4 className="text-lg font-black text-white font-outfit tracking-tight uppercase">{title} Strategy</h4>
          <div className="flex items-center gap-2 mt-1">
            <span className={`text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded ${mood.includes('Bull') ? 'bg-emerald-500/10 text-emerald-400' : (mood.includes('Bear') ? 'bg-rose-500/10 text-rose-400' : 'bg-slate-500/10 text-slate-400')}`}>
                Agent Mood: {mood}
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end">
            <span className={`text-xl font-bold font-mono leading-none ${isUp ? 'text-emerald-500' : 'text-rose-500'}`}>
                {isUp ? '▲' : '▼'}{Math.abs(data.change).toFixed(2)}%
            </span>
            <span className="text-[7px] font-black text-slate-600 uppercase tracking-widest mt-1">Market Pulse</span>
        </div>
      </div>

      <div className="space-y-4 relative z-10">
        <div className="space-y-2">
            <h5 className="text-[9px] font-black text-blue-500 uppercase tracking-widest">Recommended Industries</h5>
            <div className="flex flex-wrap gap-2">
                {industries.short_term.map(ind => (
                    <span key={ind} className="px-2 py-1 rounded-md bg-white/5 border border-white/5 text-[9px] font-bold text-slate-300 uppercase tracking-tighter italic">ST:{ind}</span>
                ))}
                {industries.long_term.map(ind => (
                    <span key={ind} className="px-2 py-1 rounded-md bg-blue-500/10 border border-blue-500/20 text-[9px] font-bold text-blue-400 uppercase tracking-tighter italic font-outfit">LT:{ind}</span>
                ))}
            </div>
        </div>

        <div className="space-y-1.5 border-t border-white/5 pt-4">
            {highlights.map((h, i) => (
                <p key={i} className="text-xs text-white font-bold leading-tight font-outfit uppercase tracking-tight">"{h}"</p>
            ))}
            <p className="text-[11px] text-slate-400 leading-relaxed italic">{body}</p>
        </div>
      </div>
    </div>
  );
};

const AlphaPill = ({ item }) => (
  <div className="flex justify-between items-center p-3 md:p-4 glass glass-hover rounded-xl group border-l-2 border-l-transparent hover:border-l-amber-500">
    <div className="flex flex-col">
      <span className="text-sm md:text-base font-black text-white font-outfit italic tracking-tighter group-hover:text-amber-400 transition-colors uppercase leading-none font-outfit">{item.ticker}</span>
      <div className="flex items-center gap-2 mt-2">
        <span className="text-[7px] md:text-[8px] text-slate-500 font-bold uppercase tracking-widest leading-none font-outfit">{item.horizon === 'Short Term' ? 'ST' : 'LT'}</span>
        {item.metrics?.sharpe && <span className="text-[7px] text-blue-400 font-bold font-mono leading-none">S:{item.metrics.sharpe}</span>}
        {item.metrics?.mdd && <span className="text-[7px] text-rose-400 font-bold font-mono leading-none">D:{item.metrics.mdd}</span>}
      </div>
    </div>
    <div className="text-right">
      <span className={`text-xs md:text-sm font-black block font-mono ${item.estimates?.['7d']?.includes('+') ? 'text-emerald-400' : 'text-rose-400'}`}>
        {item.estimates?.['7d']}
      </span>
      <div className="flex items-center gap-1 justify-end mt-1">
        <span className="text-[7px] md:text-[8px] font-black text-amber-500 uppercase tracking-tighter">Conf</span>
        <span className="text-[9px] md:text-[10px] font-black text-white font-mono">{(item.total_conf * 100).toFixed(0)}%</span>
      </div>
    </div>
  </div>
);

const StrategyDeployModal = ({ isOpen, onClose, template, ticker, onConfirm }) => {
  if (!isOpen || !template) return null;
  return (
    <div className="fixed inset-0 z-[300] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-300">
      <div className="glass max-w-2xl w-full rounded-[2.5rem] p-8 shadow-3xl border-white/10 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
            <span className="text-9xl font-black text-white font-outfit uppercase">?</span>
        </div>
        
        <div className="relative z-10 space-y-8">
            <div className="space-y-2">
                <span className="text-[10px] font-black text-blue-500 uppercase tracking-[0.3em] font-outfit">Strategy Configuration</span>
                <h2 className="text-3xl md:text-4xl font-black text-white font-outfit italic tracking-tight uppercase leading-none">
                    Deploy <span className="text-blue-400">{template.name}</span>
                </h2>
                <p className="text-slate-400 font-medium italic font-outfit text-sm max-w-md">{template.description}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass p-5 rounded-3xl border-white/5 space-y-3">
                    <h3 className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">Logic Core</h3>
                    <p className="text-xs text-white font-bold leading-relaxed font-outfit uppercase">"{template.logic}"</p>
                    <div className="pt-2 border-t border-white/5 flex flex-wrap gap-2">
                         <span className="px-2 py-1 rounded bg-white/5 text-[8px] font-black text-slate-400 uppercase tracking-widest">Freq: {template.frequency}</span>
                    </div>
                </div>
                
                <div className="glass p-5 rounded-3xl border-white/5 space-y-3">
                     <h3 className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">Backtest Audit (30D)</h3>
                     <div className="grid grid-cols-2 gap-4">
                         <div className="flex flex-col">
                             <span className="text-[8px] text-slate-600 uppercase font-black">Accuracy</span>
                             <span className="text-lg font-black text-emerald-400 font-mono">{template.backtest_metrics?.['1d_accuracy']}</span>
                         </div>
                         <div className="flex flex-col">
                             <span className="text-[8px] text-slate-600 uppercase font-black">Return</span>
                             <span className="text-lg font-black text-emerald-400 font-mono">{template.backtest_metrics?.['30d_return']}</span>
                         </div>
                         <div className="flex flex-col">
                             <span className="text-[8px] text-slate-600 uppercase font-black">Drawdown</span>
                             <span className="text-lg font-black text-rose-400 font-mono">{template.backtest_metrics?.['max_drawdown']}</span>
                         </div>
                         <div className="flex flex-col">
                             <span className="text-[8px] text-slate-600 uppercase font-black">Sharpe</span>
                             <span className="text-lg font-black text-blue-400 font-mono">{template.backtest_metrics?.['sharpe_ratio']}</span>
                         </div>
                     </div>
                </div>
            </div>

            <div className="glass p-5 rounded-3xl border-white/5 space-y-2 bg-amber-500/5 border-amber-500/10">
                 <h3 className="text-[9px] font-black text-amber-500 uppercase tracking-widest font-outfit">Risk Management Rules</h3>
                 <p className="text-xs text-amber-100/80 font-mono font-bold">{template.risk_management}</p>
            </div>

            <div className="flex items-center gap-4 pt-4">
                <button onClick={onClose} className="flex-1 py-4 rounded-2xl bg-white/5 hover:bg-white/10 text-white text-[10px] font-black uppercase tracking-widest transition-all font-outfit">Cancel</button>
                <button onClick={() => onConfirm(ticker, template.id)} className="flex-[2] py-4 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white text-[10px] font-black uppercase tracking-widest transition-all shadow-xl glow-blue font-outfit flex items-center justify-center gap-2">
                    <span>Confirm & Activate</span>
                    <span className="opacity-50 text-[8px] font-mono">({ticker})</span>
                </button>
            </div>
        </div>
      </div>
    </div>
  );
};

const HighDensityCard = ({ item, type = "STOCK" }) => {
  const isUp = item.change >= 0;
  const metrics = type === 'STOCK' ? [
    { label: 'P/E', value: item.metrics?.pe || '---', color: 'text-orange-400' },
    { label: 'FCF', value: item.metrics?.fcf || '---', color: 'text-emerald-400' },
    { label: 'Sharpe', value: item.metrics?.sharpe || '---', color: 'text-blue-400' },
    { label: 'MDD', value: item.metrics?.mdd || '---', color: 'text-rose-400' },
    { label: 'Corr', value: item.metrics?.corr ?? '0.5', color: 'text-slate-400' }
  ] : type === 'CRYPTO' ? [
    { label: 'MVRV Z', value: item.mvrv_z_score?.toFixed(2) || '---', color: 'text-blue-400' },
    { label: 'F&G', value: item.fear_greed_index || '---', color: 'text-amber-400' },
    { label: 'Fund', value: item.funding_rate !== undefined && item.funding_rate !== null ? `${item.funding_rate.toFixed(3)}%` : '---', color: 'text-emerald-400' },
    { label: 'Heat', value: item.gas_price_gwei !== undefined && item.gas_price_gwei !== null ? `${item.gas_price_gwei.toFixed(1)}g` : '---', color: 'text-rose-400' }
  ] : type === 'COMMODITY' ? [
    { label: 'Basis', value: 'Cash', color: 'text-amber-400' },
    { label: 'Unit', value: item.ticker.includes('=F') ? 'Contract' : 'Spot', color: 'text-slate-400' },
    { label: 'Sharpe', value: item.metrics?.sharpe || '---', color: 'text-blue-400' },
    { label: 'Win', value: `${(item.win_rate * 100).toFixed(0)}%`, color: 'text-emerald-400' }
  ] : [];

  return (
    <div className="p-4 md:p-6 hover:bg-white/[0.03] transition-all group border-b border-white/5 last:border-0 relative">
        <div className="flex flex-col xl:flex-row xl:justify-between items-start gap-4 md:gap-8">
            <div className="flex-1 space-y-4 md:space-y-6 w-full text-left">
                <div className="flex items-center justify-between w-full">
                    <div className="flex items-center gap-4">
                        <div className="flex flex-col">
                            <div className="flex items-baseline gap-3">
                                <span className="text-xl md:text-3xl font-black text-white font-outfit italic tracking-tight group-hover:text-blue-400 transition-colors uppercase leading-none font-outfit font-black">{item.ticker || item.pair}</span>
                                <span className="text-sm md:text-lg font-bold text-slate-500 font-mono tracking-tighter leading-none font-mono">${item.price}</span>
                                <div className={`px-1.5 md:px-2 py-0.5 rounded text-[8px] md:text-[10px] font-bold font-mono ${isUp ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                                    {isUp ? '▲' : '▼'}{Math.abs(item.change || 0).toFixed(2)}%
                                </div>
                            </div>
                            <div className="flex flex-wrap items-center gap-2 mt-2">
                                <span className={`text-[8px] md:text-[9px] font-black uppercase tracking-[0.2em] px-2 py-0.5 rounded-md font-outfit ${item.total_conf > 0.82 ? 'bg-blue-500/20 text-blue-400' : 'bg-slate-500/20 text-slate-400'}`}>
                                    {item.action || (item.total_conf > 0.82 ? 'STRONG BUY' : 'HOLD')}
                                </span>
                                <span className="text-[8px] md:text-[9px] font-black text-slate-500 uppercase tracking-widest font-mono font-bold italic">WIN: {(item.win_rate * 100).toFixed(0)}%</span>
                                {item.candlestick_pattern && (
                                    <span className="text-[8px] font-black text-amber-500 bg-amber-500/10 px-2 py-0.5 rounded-md border border-amber-500/20 uppercase tracking-widest leading-none">
                                        CDL: {item.candlestick_pattern}
                                    </span>
                                )}
                            </div>
                        </div>
                        <div className="hidden sm:block glass p-1.5 rounded-xl border-white/5 shadow-inner">
                            <Sparkline data={item.sparkline} color={item.total_conf > 0.7 ? "#3b82f6" : "#64748b"} width={100} height={32} />
                        </div>
                    </div>
                    <div className="flex flex-col text-right">
                       <span className="text-[7px] md:text-[8px] text-slate-600 uppercase font-black tracking-widest">Score</span>
                       <span className="text-2xl md:text-3xl font-black text-white italic font-outfit leading-none">{(item.total_conf * 100).toFixed(0)}</span>
                    </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-5 gap-3 md:gap-4">
                    {metrics.map((m, i) => <MetricBlock key={i} {...m} />)}
                </div>

                <div className="grid grid-cols-3 gap-3 md:gap-6 py-3 md:py-4 border-y border-white/5 font-mono text-left">
                    {[{ label: '1D Est', val: item.estimates?.['1d'] }, { label: '7D Est', val: item.estimates?.['7d'] }, { label: '1M Est', val: item.estimates?.['1m'] }].map(est => (
                        <div key={est.label} className="flex flex-col">
                            <span className="text-[8px] md:text-[9px] font-black text-slate-600 uppercase tracking-widest mb-1 font-outfit">{est.label}</span>
                            <span className={`text-sm md:text-base font-black ${est.val?.includes('+') ? 'text-blue-400' : 'text-orange-400'}`}>{est.val || '---'}</span>
                        </div>
                    ))}
                </div>
                
                <p className="text-[11px] md:text-[13px] text-slate-300 italic font-medium leading-relaxed text-left border-l-2 border-blue-500/20 pl-3 md:pl-4 line-clamp-2 md:line-clamp-none font-outfit">
                  "{item.logic || item.reasoning}"
                </p>
            </div>
            
            <div className="w-full xl:w-[140px] flex xl:flex-col items-center justify-between xl:justify-start gap-4 xl:gap-6 xl:pt-4">
                <div className="flex-1 xl:w-full space-y-2 md:space-y-3">
                    <div className="space-y-1">
                        <div className="flex justify-between text-[7px] md:text-[8px] font-black uppercase text-slate-600 font-outfit"><span>Quant</span><span>{(item.trad_conf * 100).toFixed(0)}%</span></div>
                        <div className="h-1 md:h-1.5 bg-white/5 rounded-full overflow-hidden"><div className="h-full bg-blue-500 shadow-[0_0_8px_#3b82f6]" style={{ width: `${(item.trad_conf || 0.6) * 100}%` }} /></div>
                    </div>
                    <div className="space-y-1">
                        <div className="flex justify-between text-[7px] md:text-[8px] font-black uppercase text-slate-600 font-outfit"><span>Neural</span><span>{(item.swarm_conf * 100).toFixed(0)}%</span></div>
                        <div className="h-1 md:h-1.5 bg-white/5 rounded-full overflow-hidden"><div className="h-full bg-green-500 shadow-[0_0_8px_#10b981]" style={{ width: `${(item.swarm_conf || 0.8) * 100}%` }} /></div>
                    </div>
                </div>
                <button className="sm:hidden px-3 py-1.5 rounded-lg bg-blue-500/10 text-blue-400 text-[10px] font-black uppercase border border-blue-500/20 font-outfit shadow-xl">Analyze</button>
            </div>
        </div>
    </div>
  );
};

const EquityCurve = ({ data }) => {
  if (!data || data.length < 2) return <div className="h-[340px] glass rounded-[2.5rem] animate-pulse-soft" />;
  const width = 1000; const height = 340; const padding = 60;
  const maxVal = Math.max(...data.map(d => Math.max(d.strat, d.bench))) * 1.05;
  const minVal = Math.min(...data.map(d => Math.min(d.strat, d.bench))) * 0.95;
  const range = maxVal - minVal;
  const getX = (i) => padding + (i / (data.length - 1)) * (width - 2 * padding);
  const getY = (v) => height - padding - ((v - minVal) / range) * (height - 2 * padding);
  const stratPoints = data.map((d, i) => `${getX(i)},${getY(d.strat)}`).join(' ');
  const benchPoints = data.map((d, i) => `${getX(i)},${getY(d.bench)}`).join(' ');
  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible drop-shadow-2xl">
      <defs>
        <linearGradient id="stratGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[0, 0.25, 0.5, 0.75, 1].map(f => (
          <line key={f} x1={padding} y1={padding + f * (height-2*padding)} x2={width-padding} y2={padding + f * (height-2*padding)} stroke="white" strokeOpacity="0.05" strokeWidth="1" />
      ))}
      <path d={`M ${getX(0)},${height-padding} ${stratPoints} L ${getX(data.length-1)},${height-padding} Z`} fill="url(#stratGradient)" />
      <polyline fill="none" stroke="#475569" strokeWidth="2" strokeDasharray="6 4" points={benchPoints} opacity="0.4" />
      <polyline fill="none" stroke="#3b82f6" strokeWidth="4" points={stratPoints} strokeLinejoin="round" strokeLinecap="round" />
      {data.filter((_,i) => i % 10 === 0 || i === data.length-1).map((d, i) => (
          <text key={i} x={getX(data.indexOf(d))} y={height-25} fill="#64748b" fontSize="10" fontWeight="bold" textAnchor="middle" className="font-mono">{d.ts}</text>
      ))}
    </svg>
  );
};

const StrategyMatrix = ({ matrix, onDeploy, activeStrategies, mode = 'simulation', onOpenBulk }) => {
  if (!matrix || !matrix.discovery || !matrix.active) {
      return (
        <div className="glass rounded-[2rem] p-12 text-center border-white/5 animate-pulse">
            <span className="text-slate-500 font-black uppercase tracking-[0.3em] italic">Syncing_Neural_Matrix...</span>
        </div>
      );
  }
  
  const [allocations, setAllocations] = useState({});
  const handleAllocationChange = (key, value) => setAllocations(prev => ({ ...prev, [key]: value }));
  const isLive = mode === 'live';

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
                <h3 className="text-xl font-black text-white uppercase tracking-widest font-outfit opacity-60 italic">Strategy Intelligence Matrix</h3>
                <span className={`px-2 py-1 rounded ${isLive ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-blue-500/10 text-blue-400 border-blue-500/20'} text-[9px] font-black border uppercase tracking-widest`}>
                    {isLive ? 'Live Execution' : 'Simulation Console'}
                </span>
                {isLive && (
                    <button onClick={onOpenBulk} className="ml-4 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-black uppercase transition-all shadow-lg flex items-center gap-2">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="4"><path d="M12 5v14M5 12h14"/></svg>
                        <span>Deploy Cluster</span>
                    </button>
                )}
            </div>
            {isLive && (
                <div className="flex gap-4">
                    <div className="flex flex-col text-right">
                        <span className="text-[7px] text-slate-600 font-black uppercase tracking-widest">Aggregate_Live_PnL</span>
                        <span className="text-sm font-black text-white font-mono">
                            ${Object.values(matrix?.active || {}).reduce((acc, s) => acc + (Number(s?.total_pnl) || 0), 0).toLocaleString()}
                        </span>
                    </div>
                </div>
            )}
        </div>

        <div className="glass rounded-[1.5rem] md:rounded-[2.5rem] overflow-hidden border-white/10 shadow-2xl">
            <div className="hidden md:block overflow-x-auto">
                <table className="w-full text-left font-outfit uppercase">
                    <thead className="bg-white/[0.03] text-slate-500 text-[10px] font-black tracking-[0.2em]">
                        <tr>
                            <th className="px-6 py-4">Strategy / Pair</th>
                            {isLive ? (
                                <>
                                    <th className="px-6 py-4">Actualized (Realized)</th>
                                    <th className="px-6 py-4">Inventory (Unrealized)</th>
                                    <th className="px-6 py-4">Avg Buy / Market</th>
                                    <th className="px-6 py-4">Inventory Qty</th>
                                    <th className="px-6 py-4">Live Trades</th>
                                    <th className="px-6 py-4">Win/Loss</th>
                                </>
                            ) : (
                                <>
                                    <th className="px-6 py-4">Win% / Logic</th>
                                    <th className="px-6 py-4">Trades (30D)</th>
                                    <th className="px-6 py-4">Daily Est.</th>
                                    <th className="px-6 py-4 text-emerald-400">Monthly Est.</th>
                                    <th className="px-6 py-4">Cap ($)</th>
                                </>
                            )}
                            <th className="px-6 py-4 text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                    {matrix?.discovery && Object.entries(matrix.discovery).flatMap(([tid, pairs]) => {
                        const template = matrix?.active ? matrix.active[tid] : null;
                        if (!pairs) return [];
                        return Object.entries(pairs).map(([pair, stats]) => {
                            const activeStrat = (activeStrategies || []).find(s => s.target_ticker === pair && s.params?.template_id === tid);
                            const isActive = !!activeStrat;
                            if (isLive && !isActive) return null;
                            const livePerf = template?.pairs?.[pair] || null;
                            const allocationKey = `${tid}-${pair}`;
                            const currentCapital = isActive ? (Number(activeStrat?.params?.allocated_capital) || 10000) : (Number(allocations[allocationKey]) || 10000);
                            const estReturn = ((Number(stats?.avg_pnl_per_trade_pct) || 0) * (Number(stats?.trades_30d) || 0) * (currentCapital || 0)) / 100;
                            return (
                                <tr key={allocationKey} className={`hover:bg-white/[0.02] transition-colors group ${isActive ? (isLive ? 'bg-emerald-500/[0.02]' : 'bg-blue-500/[0.02]') : ''}`}>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-col text-left">
                                            <span className="text-sm font-black text-white italic">{(pair || "").replace('=X','')}</span>
                                            <span className="text-[9px] text-slate-500 font-bold tracking-widest">{template?.name || "Strategy"}</span>
                                        </div>
                                    </td>
                                    {isLive ? (
                                        <>
                                            <td className="px-6 py-4">
                                                <span className={`text-sm font-black font-mono ${(Number(livePerf?.realized_pnl) || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                                    {`${(Number(livePerf?.realized_pnl) || 0) >= 0 ? '+' : ''}$${(Number(livePerf?.realized_pnl) || 0).toLocaleString(undefined, {minimumFractionDigits: 2})}`}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`text-sm font-black font-mono ${(Number(livePerf?.unrealized_pnl) || 0) >= 0 ? 'text-blue-400' : 'text-orange-400'}`}>
                                                    {`${(Number(livePerf?.unrealized_pnl) || 0) >= 0 ? '+' : ''}$${(Number(livePerf?.unrealized_pnl) || 0).toLocaleString(undefined, {minimumFractionDigits: 2})}`}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex flex-col text-left font-mono">
                                                    <span className="text-xs font-bold text-white">${(Number(livePerf?.avg_buy_price) || 0).toFixed(4)}</span>
                                                    <span className="text-[9px] text-slate-500 font-black italic">Mkt: ${(Number(livePerf?.market_price) || 0).toFixed(4)}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className="text-sm font-black text-white font-mono">{Number(livePerf?.inventory_qty) || 0} Units</span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className="text-sm font-black text-slate-300 font-mono">{Number(livePerf?.trades) || 0}</span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="flex flex-col text-left">
                                                        <span className="text-[8px] text-slate-600 font-black uppercase">Wins</span>
                                                        <span className="text-xs font-bold text-emerald-400 font-mono">{Number(livePerf?.wins) || 0}</span>
                                                    </div>
                                                    <div className="h-4 w-px bg-white/5" />
                                                    <div className="flex flex-col text-left">
                                                        <span className="text-[8px] text-slate-600 font-black uppercase">Loss</span>
                                                        <span className="text-xs font-bold text-rose-400 font-mono">{Number(livePerf?.losses) || 0}</span>
                                                    </div>
                                                </div>
                                            </td>
                                        </>
                                    ) : (
                                        <>
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-2">
                                                    <span className="text-sm font-black font-mono text-emerald-400">{stats.accuracy}%</span>
                                                    <span className="text-[8px] text-slate-600 font-bold bg-white/5 px-1.5 py-0.5 rounded">MOD:{stats.risk_score.toFixed(1)}</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 font-mono text-slate-300 text-xs">{stats.trades_30d}</td>
                                            <td className="px-6 py-4 font-mono text-xs text-blue-400">+${(estReturn / 30).toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
                                            <td className="px-6 py-4 font-mono font-black text-emerald-400">+${estReturn.toLocaleString(undefined, {maximumFractionDigits: 0})}</td>
                                            <td className="px-6 py-4">
                                                <input type="number" value={currentCapital} disabled={isActive} onChange={e => handleAllocationChange(allocationKey, Number(e.target.value))} className={`bg-black/40 border rounded-lg px-3 py-1.5 text-white font-mono text-xs w-20 focus:border-blue-500 outline-none transition-colors ${isActive ? 'border-transparent text-slate-400' : 'border-white/10'}`} />
                                            </td>
                                        </>
                                    )}
                                    <td className="px-6 py-4 text-right">
                                        <button onClick={() => isActive ? (confirm('Terminate Strategy?') && onDeploy(pair, tid, currentCapital, 'terminate', activeStrat.id)) : onDeploy(pair, tid, currentCapital, 'deploy')} className={`px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest ${isActive ? 'border border-rose-500/20 text-rose-500/70 hover:bg-rose-500 hover:text-white' : (isLive ? 'bg-emerald-600 hover:bg-emerald-500' : 'bg-blue-600 hover:bg-blue-500') + ' text-white'} transition-all shadow-lg font-outfit`}>
                                            {isActive ? 'Terminate' : 'Deploy'}
                                        </button>
                                    </td>
                                </tr>
                            );
                        });
                    })}
                    </tbody>
                </table>
            </div>
            <div className="md:hidden divide-y divide-white/5 bg-black/20">
                {matrix?.discovery && Object.entries(matrix.discovery).flatMap(([tid, pairs]) => {
                    const template = matrix?.active ? matrix.active[tid] : null;
                    return Object.entries(pairs).map(([pair, stats]) => {
                        const activeStrat = (activeStrategies || []).find(s => s.target_ticker === pair && s.params?.template_id === tid);
                        const isActive = !!activeStrat;
                        if (isLive && !isActive) return null;
                        const livePerf = template?.pairs?.[pair] || null;
                        const currentCapital = isActive ? (Number(activeStrat?.params?.allocated_capital) || 10000) : (Number(allocations[`${tid}-${pair}`]) || 10000);
                        const isPos = (Number(livePerf?.realized_pnl) || 0) >= 0;
                        return (
                            <div key={`${tid}-${pair}`} className={`p-5 space-y-4 ${isActive ? (isLive ? 'bg-emerald-500/5' : 'bg-blue-500/5') : ''}`}>
                                <div className="flex justify-between items-start">
                                    <div className="flex flex-col">
                                        <span className="text-lg font-black text-white italic">{(pair || "").replace('=X','')}</span>
                                        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-tighter">{template?.name || "Strategy"}</span>
                                    </div>
                                    <button onClick={() => isActive ? (confirm('Terminate Strategy?') && onDeploy(pair, tid, currentCapital, 'terminate', activeStrat.id)) : onDeploy(pair, tid, currentCapital, 'deploy')} className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest ${isActive ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : (isLive ? 'bg-emerald-600' : 'bg-blue-600') + ' text-white shadow-lg'}`}>
                                        {isActive ? 'Stop' : 'Deploy'}
                                    </button>
                                </div>
                                {isLive ? (
                                    <div className="grid grid-cols-2 gap-4 pt-2">
                                        <div className="space-y-1"><span className="text-[8px] text-slate-500 font-black uppercase">Actualized</span><div className={`text-sm font-black font-mono ${isPos ? 'text-emerald-400' : 'text-rose-400'}`}>{isPos ? '+' : ''}${(Number(livePerf?.realized_pnl) || 0).toFixed(2)}</div></div>
                                        <div className="space-y-1"><span className="text-[8px] text-slate-500 font-black uppercase">Inventory</span><div className={`text-sm font-black font-mono ${(Number(livePerf?.unrealized_pnl) || 0) >= 0 ? 'text-blue-400' : 'text-rose-400'}`}>${(Number(livePerf?.unrealized_pnl) || 0).toFixed(2)}</div></div>
                                        <div className="space-y-1"><span className="text-[8px] text-slate-500 font-black uppercase">Units / Trades</span><div className="text-xs font-black text-white font-mono">{Number(livePerf?.inventory_qty) || 0}U / {Number(livePerf?.trades) || 0}Ex</div></div>
                                        <div className="space-y-1 text-right"><span className="text-[8px] text-slate-500 font-black uppercase">Avg / Mkt</span><div className="text-[10px] font-bold text-white font-mono">${(Number(livePerf?.avg_buy_price) || 0).toFixed(2)} / <span className="text-emerald-400">${(Number(livePerf?.market_price) || 0).toFixed(2)}</span></div></div>
                                    </div>
                                ) : (
                                    <div className="flex justify-between items-end pt-2">
                                        <div className="flex gap-4">
                                            <div className="flex flex-col"><span className="text-[8px] text-slate-500 font-black uppercase">Win%</span><span className="text-sm font-black text-emerald-400 font-mono">{stats.accuracy}%</span></div>
                                            <div className="flex flex-col"><span className="text-[8px] text-slate-500 font-black uppercase">Trades</span><span className="text-sm font-black text-white font-mono">{stats.trades_30d}</span></div>
                                        </div>
                                        <div className="flex flex-col items-end"><span className="text-[8px] text-slate-500 font-black uppercase">Allocated ($)</span><input type="number" value={currentCapital} disabled={isActive} onChange={e => handleAllocationChange(`${tid}-${pair}`, Number(e.target.value))} className="bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-white font-mono text-xs w-24 text-right" /></div>
                                    </div>
                                )}
                            </div>
                        );
                    });
                })}
            </div>
        </div>
    </div>
  );
};

const BulkDeployModal = ({ isOpen, onClose, matrix, onConfirm }) => {
  const [selected, setSelected] = useState([]);
  const [capital, setCapital] = useState(10000);
  if (!isOpen || !matrix?.discovery) return null;
  const toggleSelect = (pair, tid) => {
    const key = `${tid}|${pair}`;
    setSelected(prev => prev.includes(key) ? prev.filter(k => k !== key) : [...prev, key]);
  };
  const handleApply = () => {
    const selections = selected.map(k => {
      const [tid, pair] = k.split('|');
      return { pair, template_id: tid, capital };
    });
    onConfirm(selections);
    setSelected([]);
  };
  return (
    <div className="fixed inset-0 z-[350] flex items-center justify-center p-4 bg-black/90 backdrop-blur-xl animate-in fade-in duration-300">
      <div className="glass max-w-4xl w-full rounded-[2.5rem] p-8 md:p-10 shadow-3xl border-white/10 relative flex flex-col max-h-[90vh]">
        <button onClick={onClose} className="absolute top-8 right-8 p-2 rounded-full hover:bg-white/5 transition-colors text-slate-500">
          <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M18 6L6 18M6 6l12 12" /></svg>
        </button>
        <div className="space-y-2 mb-8">
          <span className="text-[10px] font-black text-emerald-500 uppercase tracking-[0.3em] font-outfit">Cluster Deployment</span>
          <h2 className="text-3xl font-black text-white font-outfit italic tracking-tight uppercase leading-none">Bulk Activate Strategies</h2>
          <p className="text-slate-400 font-medium text-sm">Select high-probability vectors for immediate paper trading deployment.</p>
        </div>
        <div className="flex items-center gap-6 mb-8 p-6 bg-white/5 rounded-3xl border border-white/5">
           <div className="flex flex-col gap-1.5 flex-1">
              <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Base Capital per Strategy ($)</span>
              <input type="number" value={capital} onChange={e => setCapital(Number(e.target.value))} className="bg-black/40 border border-white/10 rounded-xl px-5 py-3 text-white font-mono text-sm focus:border-emerald-500 outline-none transition-all w-full" />
           </div>
           <div className="text-right">
              <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest block mb-1">Selections</span>
              <span className="text-2xl font-black text-emerald-400 font-mono">{selected.length}</span>
           </div>
        </div>
        <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
           <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(matrix.discovery).flatMap(([tid, pairs]) => {
                const template = matrix.active[tid] || { name: tid };
                return Object.entries(pairs).map(([pair, stats]) => {
                  const isSel = selected.includes(`${tid}|${pair}`);
                  return (
                    <div key={`${tid}|${pair}`} onClick={() => toggleSelect(pair, tid)} className={`p-5 rounded-2xl border cursor-pointer transition-all flex justify-between items-center group ${isSel ? 'bg-emerald-500/10 border-emerald-500/40 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : 'bg-white/5 border-white/5 hover:border-white/20'}`}>
                      <div className="flex flex-col">
                        <span className="text-base font-black text-white italic group-hover:text-emerald-400 transition-colors">{(pair || "").replace('=X','')}</span>
                        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-tighter">{template.name}</span>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                         <span className="text-xs font-black text-emerald-400 font-mono">{stats.accuracy}% Win</span>
                         <div className={`h-5 w-5 rounded-md border-2 flex items-center justify-center transition-all ${isSel ? 'bg-emerald-500 border-emerald-500' : 'border-white/10'}`}>
                            {isSel && <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="4"><path d="M20 6L9 17L4 12" /></svg>}
                         </div>
                      </div>
                    </div>
                  );
                });
              })}
           </div>
        </div>
        <div className="pt-8 mt-4 border-t border-white/5 flex gap-4">
           <button onClick={onClose} className="flex-1 py-4 rounded-2xl bg-white/5 hover:bg-white/10 text-white text-[11px] font-black uppercase tracking-widest transition-all">Cancel</button>
           <button disabled={selected.length === 0} onClick={handleApply} className="flex-[2] py-4 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-black uppercase tracking-widest transition-all shadow-xl glow-emerald disabled:opacity-30 disabled:grayscale">Deploy {selected.length} Strategies</button>
        </div>
      </div>
    </div>
  );
};

const InventoryCommandTable = ({ positions, onClosePosition }) => {
  const [customPct, setCustomPct] = useState(100);
  return (
    <div className="glass rounded-[1.5rem] md:rounded-[2.5rem] overflow-hidden border-white/10 shadow-2xl">
        <div className="p-6 border-b border-white/5 flex justify-between items-center bg-white/[0.02]">
            <h3 className="text-xl font-black text-white uppercase italic tracking-tightest font-outfit">Inventory Command</h3>
            <span className="text-[10px] font-black text-blue-500 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20 tracking-widest uppercase">Live Holdings</span>
        </div>
        <div className="overflow-x-auto custom-scrollbar">
            <table className="w-full text-left font-outfit uppercase min-w-[700px]">
                <thead className="bg-black/40 text-slate-500 text-[10px] font-black tracking-[0.2em]">
                    <tr>
                        <th className="px-6 py-4">Asset</th>
                        <th className="px-6 py-4">Position</th>
                        <th className="px-6 py-4">Avg Long/Short</th>
                        <th className="px-6 py-4">Mkt Price</th>
                        <th className="px-6 py-4">Unrealized</th>
                        <th className="px-6 py-4 text-right">Liquidation Control</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                    {!Array.isArray(positions) || positions.length === 0 ? (
                        <tr><td colSpan="6" className="px-6 py-12 text-center text-slate-600 italic font-medium uppercase tracking-widest">No Active Positions in Cluster</td></tr>
                    ) : (
                        positions.map((p, i) => {
                            const isLong = (p.position || 0) > 0;
                            const pnl = p.unrealizedPnl || 0;
                            return (
                                <tr key={i} className="hover:bg-white/[0.02] transition-colors group">
                                    <td className="px-6 py-4"><span className="text-lg font-black text-white italic tracking-tighter">{p.symbol}</span></td>
                                    <td className="px-6 py-4"><span className={`px-2 py-1 rounded text-[10px] font-black ${isLong ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>{isLong ? 'LONG' : 'SHORT'} {Math.abs(p.position).toLocaleString()}</span></td>
                                    <td className="px-6 py-4 font-mono text-xs text-slate-300 font-bold">${(p.avgCost || 0).toFixed(4)}</td>
                                    <td className="px-6 py-4 font-mono text-xs text-white font-black">${(p.mktPrice || 0).toFixed(4)}</td>
                                    <td className="px-6 py-4"><span className={`text-sm font-black font-mono ${pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{pnl >= 0 ? '+' : ''}${pnl.toLocaleString(undefined, {minimumFractionDigits: 2})}</span></td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex items-center justify-end gap-3">
                                            <div className="flex items-center bg-black/40 rounded-lg border border-white/10 px-2 py-1">
                                                <input type="number" value={customPct} onChange={e => setCustomPct(Math.min(100, Math.max(1, Number(e.target.value))))} className="bg-transparent w-8 text-[10px] font-black text-white outline-none text-center font-mono" />
                                                <span className="text-[8px] text-slate-500 font-black">%</span>
                                            </div>
                                            <button onClick={() => onClosePosition(p.symbol, customPct)} className={`px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all ${customPct === 100 ? 'bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-900/20' : 'bg-white/5 text-slate-400 border border-white/10 hover:bg-white/10 hover:text-white'}`}>Execute_Exit</button>
                                        </div>
                                    </td>
                                </tr>
                            );
                        })
                    )}
                </tbody>
            </table>
        </div>
    </div>
  );
};

const App = () => {
  const [activeTab, setActiveTab] = useState('quant');
  const [analysisStatus, setAnalysisStatus] = useState({});
  const [signals, setSignals] = useState([]);
  const [fx, setFx] = useState([]);
  const [crypto, setCrypto] = useState([]);
  const [commodities, setCommodities] = useState([]);
  const [hft, setHft] = useState([]);
  const [velocitySummary, setVelocitySummary] = useState({ inventory_value: 0, today_pnl: 0, active_positions: 0, executions_today: 0 });
  const [velocityTrades, setVelocityTrades] = useState([]);
  const [macro, setMacro] = useState({ indices: {}, system_risk: 'LOW', shock_text: 'System Nominal' });
  const [inventory, setInventory] = useState([]);
  const [outlook, setOutlook] = useState({ market_mood: '...', swarm_conclusion: '...' });
  const [performance, setPerformance] = useState({ metrics: [], curve: [] });
  const [strategyConfigs, setStrategyConfigs] = useState([]);
  const [syncSchedules, setSyncSchedules] = useState([]);
  const [maintenanceStatus, setMaintenanceStatus] = useState({});
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [ibStatus, setIbStatus] = useState({ status: 'Disconnected', socket: 'Offline', web: 'Unauthorized' });
  const [ibAccount, setIbAccount] = useState(null);
  const [ibPositions, setIbPositions] = useState([]);
  const [pendingConfigs, setPendingConfigs] = useState({});
  const [pendingSchedules, setPendingSchedules] = useState({});
  const [isApplying, setIsApplying] = useState(false);
  const [newAsset, setNewAsset] = useState({ ticker: '', asset_class: 'STOCK', quantity: 0, buy_price: 0 });
  const [quantStrategies, setQuantStrategies] = useState([]);
  const [quantMatrix, setQuantMatrix] = useState({});
  const [strategyTemplates, setStrategyTemplates] = useState({});
  const [deployModalData, setDeployModalData] = useState({ isOpen: false, templateId: null, ticker: null });
  const [isDeploying, setIsDeploying] = useState(false);
  const [quantTab, setQuantTab] = useState('simulation'); // 'simulation' | 'live'
  const [isBulkOpen, setIsBulkOpen] = useState(false);

  const fetchQuantStrategies = async () => {
    try {
        const resp = await fetch(`/api/quant/strategies`);
        if (resp.ok) setQuantStrategies(await resp.json());
        const matrixResp = await fetch(`/api/quant/performance/matrix`);
        if (matrixResp.ok) setQuantMatrix(await matrixResp.json());
    } catch (e) { console.error(e); }
  };

  const fetchStrategyTemplates = async () => {
    try {
        const resp = await fetch(`/api/quant/templates`);
        if (resp.ok) setStrategyTemplates(await resp.json());
    } catch (e) { console.error(e); }
  };

  const initiateDeploy = (ticker, templateId, capital, action, stratId) => {
      if (action === 'terminate' && stratId) {
          fetch(`/api/quant/strategies/delete/${stratId}`, {method: 'DELETE'}).then(fetchQuantStrategies);
          return;
      }
      setDeployModalData({ isOpen: true, templateId, ticker, capital });
  };

  const confirmDeploy = async (pair, templateId) => {
    const capital = deployModalData.capital || 10000;
    setDeployModalData({ isOpen: false, templateId: null, ticker: null, capital: null });
    setIsDeploying(true);
    try {
        await fetch(`/api/quant/strategies/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pair, lot_size: capital, template_id: templateId }) 
        });
        await fetchQuantStrategies();
    } catch (e) { console.error(e); } 
    finally { setIsDeploying(false); }
  };

  const API_BASE = "/api";
  const [selectedAccountId, setSelectedAccountId] = useState(null);

  const connectIb = async () => {
      try {
          setIbStatus(prev => ({ ...prev, socket: 'Connecting...' }));
          const resp = await fetch(`${API_BASE}/velocity/ib/connect`, { method: 'POST' });
          if (resp.ok) {
              const data = await resp.json();
              if (data.status === 'success') {
                  setIbStatus(prev => ({ ...prev, socket: 'Online' }));
                  alert("IB Socket Connected");
              } else {
                  setIbStatus(prev => ({ ...prev, socket: 'Error' }));
                  alert("Connection Failed: " + data.message);
              }
          }
      } catch (e) { console.error(e); }
  };

  const fetchIbData = async (accountIdOverride) => {
    try {
      const statusCheck = async () => {
          const acc = await fetch('/v1/api/iserver/accounts', { credentials: 'include' });
          const authResp = await fetch('/v1/api/iserver/auth/status', { credentials: 'include' });
          return authResp.ok ? await authResp.json() : null;
      };
      const authData = await statusCheck();
      if (authData && authData.authenticated) {
          setIbStatus(prev => ({ ...prev, web: 'Authenticated', status: 'Connected' }));
          // Keep session alive
          fetch(`${API_BASE}/velocity/ib/sync-session`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include' }).catch(() => {});
          
          const accResp = await fetch('/v1/api/portfolio/accounts', { credentials: 'include' });
          if (accResp.ok) {
            const accData = await accResp.json();
            if (accData && accData.length > 0) {
              const targetId = accountIdOverride || selectedAccountId || (accData.find(a => a.id.startsWith('DU')) || accData[0]).id;
              if (!selectedAccountId) setSelectedAccountId(targetId);
              
              // Parallel fetch for speed
              const [summaryResp, posResp, ledgerResp] = await Promise.all([
                  fetch(`/v1/api/portfolio/${targetId}/summary`, { credentials: 'include' }),
                  fetch(`/v1/api/portfolio/${targetId}/positions/0`, { credentials: 'include' }),
                  fetch(`/v1/api/portfolio/${targetId}/ledger`, { credentials: 'include' })
              ]);

              // Process Summary
              let summaryData = {};
              if (summaryResp.ok) summaryData = await summaryResp.json();
              
              const processedAccounts = accData.map(a => {
                  const isTarget = a.id === targetId;
                  return {
                    ...a,
                    netLiquidation: (isTarget ? (summaryData.netliquidation?.amount || summaryData.netLiquidation?.amount) : null) || a.netLiquidationValue || a.netLiquidation || a.totalCashValue || a.amount || a.equity || 0,
                    buyingPower: (isTarget ? (summaryData.buyingpower?.amount || summaryData.buyingPower?.amount) : null) || a.buyingPower || a.availableFunds || a.cash || 0
                  };
              });
              setIbAccount(processedAccounts);

              // Process Positions (Only update if successful to avoid flickering)
              if (posResp.ok) {
                  let combinedPositions = await posResp.json();
                  
                  if (ledgerResp.ok) {
                      const ledgerData = await ledgerResp.json();
                      Object.entries(ledgerData).forEach(([curr, details]) => {
                          if (curr !== 'BASE' && Math.abs(details.cashbalance) > 1) {
                              if (!combinedPositions.find(p => p.symbol === curr)) {
                                  combinedPositions.push({ symbol: curr, position: details.cashbalance, avgCost: 1.0, mktPrice: details.marketvalue / details.cashbalance || 1.0, unrealizedPnl: details.unrealizedpnl || 0, secType: 'CASH' });
                              }
                          }
                      });
                  }
                  setIbPositions(combinedPositions);
              }
            }
          }
      } else { setIbStatus(prev => ({ ...prev, web: 'Unauthorized' })); }
    } catch (e) { console.error("IB Data Fetch Error:", e); }
  };

  const activeAccount = useMemo(() => {
    if (!ibAccount || !selectedAccountId) return null;
    return ibAccount.find(a => a.id === selectedAccountId) || ibAccount[0];
  }, [ibAccount, selectedAccountId]);

  const fetchData = async () => {
    try {
      const endpoints = ['macro/pulse', 'signals/1', 'fx/pairs', 'crypto/pairs', 'commodities/all', 'hft/matrix', 'inventory/evaluate', 'market/outlook', 'performance/strategy', 'metadata/strategy_configs', 'metadata/sync_schedules', 'velocity/ib/status', 'velocity/summary', 'velocity/trades'];
      const responses = await Promise.all(endpoints.map(e => fetch(`${API_BASE}/${e}`)));
      const data = await Promise.all(responses.map(r => r.ok ? r.json() : null));
      if (data[0]) setMacro(data[0]); if (data[1]) setSignals(data[1]); if (data[2]) setFx(data[2]); if (data[3]) setCrypto(data[3]); if (data[4]) setCommodities(data[4]); if (data[5]) setHft(data[5]); if (data[6]) setInventory(data[6]); if (data[7]) setOutlook(data[7]); if (data[8]) setPerformance(data[8]); if (data[9]) setStrategyConfigs(data[9]); if (data[10]) setSyncSchedules(data[10]); if (data[11]) setIbStatus(data[11]); if (data[12]) setVelocitySummary(data[12]); if (data[13]) setVelocityTrades(data[13]);
    } catch (e) { console.error(e); }
  };

  const closePosition = async (ticker, percent) => {
    if (!confirm(`Confirm LIQUIDATION: Close ${percent}% of ${ticker}?`)) return;
    try {
        const pos = ibPositions.find(p => p.symbol === ticker); if (!pos) return;
        const qtyToClose = Math.floor(Math.abs(pos.position) * (percent / 100)); if (qtyToClose === 0) return;
        const action = pos.position > 0 ? 'SELL' : 'BUY';
        const resp = await fetch(`${API_BASE}/velocity/trade/execute`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ticker, action, quantity: qtyToClose, account_id: selectedAccountId || (ibAccount && ibAccount[0]?.id) }) });
        if (resp.ok) { alert(`Order Sent: ${action} ${qtyToClose} ${ticker}`); fetchIbData(selectedAccountId); }
    } catch (e) { console.error(e); }
  };

  const handleBulkDeploy = async (selections) => {
      try {
          const resp = await fetch(`${API_BASE}/quant/strategies/bulk-create`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ selections }) });
          if (resp.ok) { setIsBulkOpen(false); fetchQuantStrategies(); alert("Cluster Deployment Initiated."); }
      } catch (e) { console.error(e); }
  };

  useEffect(() => {
    fetchData(); fetchIbData(); fetchQuantStrategies(); fetchStrategyTemplates();
    const interval = setInterval(() => { fetchData(); fetchIbData(); fetchQuantStrategies(); }, 15000); 
    return () => clearInterval(interval);
  }, []);

  const getHKTTime = () => new Date().toLocaleTimeString('en-HK', { timeZone: 'Asia/Hong_Kong', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });

  return (
    <div className="min-h-screen bg-[#05070a] text-slate-300 flex flex-col font-sans selection:bg-blue-500/30 overflow-x-hidden">
      <StrategyInfoModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} tab={activeTab} />
      <StrategyDeployModal isOpen={deployModalData.isOpen} onClose={() => setDeployModalData({ isOpen: false, templateId: null, ticker: null })} template={strategyTemplates[deployModalData.templateId]} ticker={deployModalData.ticker} onConfirm={confirmDeploy} />
      <BulkDeployModal isOpen={isBulkOpen} onClose={() => setIsBulkOpen(false)} matrix={quantMatrix} onConfirm={handleBulkDeploy} />
      
      <div className="md:h-24 glass border-b border-white/5 flex flex-wrap items-center px-4 md:px-8 sticky top-0 z-[100] backdrop-blur-2xl shadow-2xl">
        <div className="flex flex-wrap divide-x divide-white/5 shrink-0">
            {['US', 'HK', 'EU', 'CN', 'SG'].map(idx => (
                <MacroPill key={idx} label={idx} value={macro.indices?.[idx]?.value} change={macro.indices?.[idx]?.change} est={macro.indices?.[idx]?.estimates} />
            ))}
        </div>
        <div className="ml-auto hidden lg:flex items-center gap-8 pl-10 pr-4 shrink-0">
           <div className="flex flex-col text-right">
              <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit mb-1 leading-none">Cluster State</span>
              <div className="flex items-center gap-2 justify-end"><div className="h-1.5 w-1.5 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_#10b981]" /><span className="text-xs font-bold text-white font-mono uppercase leading-none">Sync_OK</span></div>
           </div>
           <div className="flex flex-col text-right min-w-[80px]"><span className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit leading-none mb-1">Local HKT</span><span className="text-xs font-bold text-blue-400 font-mono italic leading-none">{getHKTTime()}</span></div>
        </div>
      </div>

      <header className="px-6 md:px-12 py-8 md:py-10 bg-gradient-to-b from-blue-500/[0.02] to-transparent sticky top-20 md:top-24 z-[90] backdrop-blur-xl border-b border-white/5">
        <div className="max-w-[1600px] mx-auto flex flex-col lg:flex-row lg:items-center justify-between gap-8 md:gap-10">
            <div className="flex items-center gap-6">
                <div className="h-12 w-12 glass rounded-xl flex items-center justify-center border-blue-500/20 group cursor-pointer hover:scale-105 transition-all"><div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg"><span className="text-lg font-black text-white italic">O</span></div></div>
                <div className="flex flex-col text-left"><h1 className="text-2xl md:text-3xl font-black text-white tracking-tight uppercase italic font-outfit leading-none font-outfit uppercase font-black">ORCHESTRA <span className="text-blue-500 text-[10px] md:text-[12px] font-mono ml-3 not-italic tracking-widest">v2.9 ELITE</span></h1><div className="flex items-center gap-2 mt-2"><span className="text-[9px] md:text-[11px] font-black text-slate-500 uppercase tracking-[0.2em] font-outfit">Institutional Command</span></div></div>
            </div>
            <nav className="flex flex-wrap gap-1.5 p-1 glass rounded-2xl shadow-inner">
                {[{id: 'inventory', label: 'Command'}, {id: 'research', label: 'Intelligence'}, {id: 'signals', label: 'Alpha'}, {id: 'fx', label: 'Forex'}, {id: 'crypto', label: 'Digital'}, {id: 'commodities', label: 'Assets'}, {id: 'quant', label: 'Quant'}, {id: 'performance', label: 'Performance'}, {id: 'config', label: 'System'}].map(tab => (
                    <button key={tab.id} onClick={() => setActiveTab(tab.id)} className={`px-4 md:px-6 py-2 md:py-3 rounded-lg md:rounded-xl text-[10px] md:text-[11px] font-black uppercase tracking-widest transition-all whitespace-nowrap font-outfit ${activeTab === tab.id ? 'bg-white text-black shadow-2xl font-black' : 'text-slate-500 hover:text-slate-200 hover:bg-white/5'}`}>{tab.label}</button>
                ))}
            </nav>
        </div>
      </header>
      
      {activeTab === 'quant' && (
          <div className="max-w-[1600px] mx-auto px-6 md:px-12 pb-6 border-b border-white/5"><div className="flex gap-4"><button onClick={() => setQuantTab('simulation')} className={`text-[10px] font-black uppercase tracking-widest pb-2 border-b-2 transition-all ${quantTab === 'simulation' ? 'border-blue-500 text-white' : 'border-transparent text-slate-500'}`}>Simulation Lab</button><button onClick={() => setQuantTab('live')} className={`text-[10px] font-black uppercase tracking-widest pb-2 border-b-2 transition-all ${quantTab === 'live' ? 'border-emerald-500 text-white' : 'border-transparent text-slate-500'}`}>Live Trading</button></div></div>
      )}

      <main className="flex-1 p-6 md:p-12 max-w-[1600px] mx-auto w-full mb-32 space-y-10 md:space-y-16">
        
        {activeTab === 'inventory' && (
            <div className="space-y-12 text-left animate-in fade-in slide-in-from-bottom-6 duration-700">
                <div className="glass p-8 md:p-12 rounded-[2.5rem] shadow-2xl flex flex-wrap gap-6 md:gap-10 items-end relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-12 opacity-[0.03] text-7xl md:text-9xl font-black italic select-none font-outfit uppercase">DEPLOY</div>
                    <div className="flex flex-col gap-2 min-w-[160px] md:min-w-[200px] w-full md:w-auto font-outfit uppercase"><span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">Ticker</span><input className="bg-black/60 border border-white/10 rounded-2xl px-5 py-3.5 text-white outline-none focus:border-blue-500 font-mono text-sm uppercase" placeholder="NVDA / BTC-USD" value={newAsset.ticker} onChange={e => setNewAsset({...newAsset, ticker: e.target.value.toUpperCase()})} /></div>
                    <div className="flex flex-col gap-2 flex-1 md:flex-none font-outfit uppercase"><span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">Class</span><select className="bg-black/60 border border-white/10 rounded-2xl px-5 py-3.5 text-white outline-none focus:border-blue-500 appearance-none font-outfit font-bold pr-12 uppercase" value={newAsset.asset_class} onChange={e => setNewAsset({...newAsset, asset_class: e.target.value})}><option value="STOCK">STOCK</option><option value="FX">FX</option><option value="CRYPTO">CRYPTO</option><option value="COMMODITY">COMMODITY</option></select></div>
                    <div className="flex flex-col gap-2 font-outfit uppercase"><span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">Qty</span><input type="number" className="bg-black/60 border border-white/10 rounded-2xl px-5 py-3.5 text-white outline-none focus:border-blue-500 font-mono text-sm w-full md:w-32" value={newAsset.quantity} onChange={e => setNewAsset({...newAsset, quantity: parseFloat(e.target.value) || 0})} /></div>
                    <button className="w-full md:w-auto px-12 py-4 rounded-2xl text-[12px] font-black uppercase tracking-[0.2em] bg-blue-600 hover:bg-blue-500 text-white shadow-xl glow-blue font-outfit">Execute</button>
                </div>
                <div className="glass rounded-[3rem] overflow-hidden shadow-2xl">
                    <div className="p-8 md:p-12 border-b border-white/10 flex flex-col md:flex-row justify-between items-center gap-6 bg-white/[0.02]"><div className="flex items-center gap-4"><h3 className="text-xl md:text-3xl font-black text-white uppercase italic tracking-tightest font-outfit leading-none">Portfolio</h3><span className="px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-[10px] font-black border border-blue-500/20 uppercase tracking-widest">{inventory.length} POSITIONS</span></div></div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 divide-y md:divide-y-0 md:gap-px bg-white/5">
                        {inventory.map((i, idx) => (
                            <div key={idx} className="bg-[#05070a] p-8 space-y-6 hover:bg-white/[0.02] transition-colors group">
                                <div className="flex justify-between items-start"><div className="flex flex-col"><span className="text-3xl font-black text-white italic font-outfit tracking-tighter uppercase leading-none font-outfit font-black">{i.ticker}</span><span className="text-[9px] text-slate-600 font-bold uppercase tracking-[0.2em] mt-2 font-outfit">{i.asset_class} SECURITY</span></div><span className={`px-3 py-1 rounded-lg text-xs font-black font-mono border ${getStatusColor(i.win_loss, 'text')} ${getStatusColor(i.win_loss, 'bg')} ${getStatusColor(i.win_loss, 'border')}`}>{i.win_loss}</span></div>
                                <div className="grid grid-cols-2 gap-6 py-5 border-y border-white/5"><div className="space-y-1"><span className="text-[8px] text-slate-500 uppercase font-black tracking-widest font-outfit">Volume</span><span className="text-base font-bold text-white font-mono">{i.quantity}</span></div><div className="space-y-1 text-right font-outfit"><span className="text-[8px] text-slate-500 uppercase font-black tracking-widest">Mark_Price</span><span className="text-base font-bold text-white font-mono">${i.current?.toLocaleString()}</span></div></div>
                                <div className="flex justify-between items-center"><div className="flex gap-5 font-mono">{[{l: '1D', v: i.est_1d}, {l: '1W', v: i.est_7d}].map(e => (<div key={e.l} className="flex flex-col"><span className="text-[8px] text-slate-600 uppercase font-black mb-1 leading-none font-outfit">{e.l}</span><span className={`text-[13px] font-black leading-none ${e.v?.includes('+') ? 'text-blue-400' : 'text-orange-400'}`}>{e.v || '---'}</span></div>))}</div></div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        )}

        {activeTab === 'research' && (
            <div className="space-y-12 text-left animate-in fade-in slide-in-from-bottom-6 duration-700">
                <div className="grid lg:grid-cols-12 gap-10">
                    <div className="lg:col-span-8 space-y-10">
                        <div className="glass rounded-[3rem] p-10 md:p-14 border-white/10 shadow-2xl relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-12 opacity-[0.03] text-7xl font-black italic font-outfit tracking-tighter leading-none uppercase">SWARM</div>
                            <div className="flex justify-between items-start mb-10 font-outfit"><span className="text-[11px] font-black text-blue-500 uppercase tracking-[0.5em] font-outfit uppercase">Neural Consensus Outlook</span></div>
                            <div className="space-y-6 md:space-y-8 relative z-10 font-outfit">
                                <span className="text-3xl md:text-5xl font-black text-white italic tracking-tighter drop-shadow-4xl font-outfit leading-none uppercase">{outlook.market_mood || 'Analyzing...'}</span>
                                <div className="space-y-3 md:space-y-4">
                                   <div className="flex items-center gap-2 md:gap-3"><span className="h-px w-6 md:w-10 bg-blue-500/30" /><span className="text-[8px] md:text-[10px] font-black text-slate-500 uppercase tracking-widest font-outfit italic leading-none">Institutional Grade Conclusion</span></div>
                                   <p className="text-lg md:text-2xl text-slate-100 italic leading-snug font-outfit tracking-tight border-l-4 border-blue-600/20 pl-6 md:pl-10 text-left font-medium max-w-4xl">"{outlook.swarm_conclusion || 'Assembling cross-market intelligence...'}"</p>
                                </div>
                            </div>
                        </div>
                        <div className="space-y-8"><div className="flex items-baseline gap-6 pb-6 border-b border-white/5 font-outfit uppercase"><h3 className="text-xl md:text-2xl font-black text-white italic tracking-tighter">Strategic Alpha</h3><span className="h-px flex-1 bg-white/5" /></div><div className="grid grid-cols-1 md:grid-cols-2 gap-6">{signals.slice(0, 4).map((s, i) => <NarrativeCard key={i} title={s.sector || 'Alpha'} data={s} />)}</div></div>
                    </div>
                    <div className="lg:col-span-4 space-y-10"><div className="glass rounded-[2.5rem] p-8 border-white/10 h-full"><div className="flex items-baseline justify-between mb-8 font-outfit uppercase"><h3 className="text-xl font-black text-white italic tracking-tighter">High Conviction</h3><span className="text-[9px] font-black text-blue-500 bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20">LIVE FEED</span></div><div className="space-y-4">{signals.slice(0, 6).map((s, i) => <AlphaPill key={i} item={s} />)}</div></div></div>
                </div>
            </div>
        )}

        {activeTab === 'signals' && (
            <div className="space-y-12 text-left animate-in fade-in slide-in-from-bottom-6 duration-700">
                <div className="flex items-baseline gap-6 pb-8 border-b border-white/5 font-outfit uppercase"><h2 className="text-2xl md:text-3xl font-black text-white italic font-outfit leading-none uppercase tracking-tightest font-outfit uppercase">Alpha Universe</h2><button onClick={() => setIsModalOpen(true)} className="h-10 w-10 rounded-full glass border-white/20 flex items-center justify-center text-lg font-black text-slate-400 hover:text-blue-400 transition-all shadow-xl">?</button><span className="h-px flex-1 bg-white/5" /></div>
                <div className="glass rounded-[3rem] overflow-hidden shadow-2xl border-white/10 divide-y divide-white/5">{signals.map((item, idx) => <HighDensityCard key={idx} item={item} type="STOCK" />)}</div>
            </div>
        )}

        {activeTab === 'fx' && (
            <div className="space-y-12 text-left animate-in fade-in slide-in-from-bottom-6 duration-700">
                <div className="flex items-baseline gap-6 pb-8 border-b border-white/5 font-outfit uppercase"><h2 className="text-2xl md:text-3xl font-black text-white italic font-outfit leading-none uppercase tracking-tightest">Forex Liquidity</h2><button onClick={() => setIsModalOpen(true)} className="h-10 w-10 rounded-full glass border-white/20 flex items-center justify-center text-lg font-black text-slate-400 hover:text-blue-400 transition-all shadow-xl">?</button><span className="h-px flex-1 bg-white/5" /></div>
                <div className="glass rounded-[3rem] overflow-hidden shadow-2xl border-white/10 divide-y divide-white/5">{fx.map((item, idx) => (<div key={idx} className="flex flex-col"><HighDensityCard item={item} type="FX" /></div>))}</div>
            </div>
        )}

        {activeTab === 'crypto' && (
            <div className="space-y-12 text-left animate-in fade-in slide-in-from-bottom-6 duration-700">
                <div className="flex items-baseline gap-6 pb-8 border-b border-white/5 font-outfit uppercase"><h2 className="text-2xl md:text-3xl font-black text-white italic font-outfit leading-none uppercase tracking-tightest font-outfit">Digital Assets</h2><span className="h-px flex-1 bg-white/5" /></div>
                <div className="glass rounded-[3rem] overflow-hidden shadow-2xl border-white/10 divide-y divide-white/5">{crypto.map((item, idx) => <HighDensityCard key={idx} item={item} type="CRYPTO" />)}</div>
            </div>
        )}

        {activeTab === 'commodities' && (
            <div className="space-y-12 text-left animate-in fade-in slide-in-from-bottom-6 duration-700">
                <div className="flex items-baseline gap-6 pb-8 border-b border-white/5 font-outfit uppercase"><h2 className="text-2xl md:text-3xl font-black text-white italic font-outfit leading-none uppercase tracking-tightest font-outfit">Hard Assets</h2><span className="h-px flex-1 bg-white/5" /></div>
                <div className="glass rounded-[3rem] overflow-hidden shadow-2xl border-white/10 divide-y divide-white/5">{commodities.map((item, idx) => <HighDensityCard key={idx} item={item} type="COMMODITY" />)}</div>
            </div>
        )}

        {activeTab === 'quant' && quantTab === 'simulation' && (
            <div className="space-y-16 animate-in fade-in slide-in-from-bottom-6 duration-700 text-left">
                <div className="flex flex-col md:flex-row md:items-baseline justify-between gap-8 border-b border-white/5 pb-8 font-outfit uppercase">
                   <div className="flex items-baseline gap-6 font-outfit"><h2 className="text-2xl md:text-3xl font-black text-white italic font-outfit leading-none uppercase tracking-tightest">Quant Strategies <span className="ml-4 text-[10px] bg-amber-500/10 text-amber-500 px-3 py-1 rounded-full border border-amber-500/20 tracking-widest">SIMULATION_MODE</span></h2><button onClick={() => setIsModalOpen(true)} className="h-10 w-10 rounded-full glass border-white/20 flex items-center justify-center text-lg font-black text-slate-400 hover:text-blue-400 transition-all shadow-xl">?</button></div>
                   <div className="flex items-center gap-4 font-outfit uppercase"><div className="flex flex-col text-right font-outfit"><span className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">IBKR_LINK_STATUS</span><span className={`text-xs font-bold font-mono ${ibStatus.web === 'Authenticated' ? 'text-emerald-400' : 'text-rose-400'}`}>{ibStatus.web}</span></div></div>
                </div>
                <StrategyMatrix matrix={quantMatrix} onDeploy={initiateDeploy} activeStrategies={quantStrategies.filter(s => s.params?.execution_mode === 'SIMULATION')} mode="simulation" onOpenBulk={() => setIsBulkOpen(true)} />
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
                    <div className="glass p-4 md:p-6 rounded-[1.5rem] md:rounded-[2rem] border-white/10 space-y-1 md:space-y-2"><span className="text-[7px] md:text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">Inventory Value</span><div className="text-lg md:text-2xl font-black text-white font-mono">{`$${velocitySummary.inventory_value?.toLocaleString() || '0.00'}`}</div><div className="text-[8px] md:text-[10px] text-slate-400 font-bold uppercase tracking-tighter">{velocitySummary.active_positions} Active</div></div>
                    <div className="glass p-4 md:p-6 rounded-[1.5rem] md:rounded-[2rem] border-white/10 space-y-1 md:space-y-2"><span className="text-[7px] md:text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">Today's P&L</span><div className={`text-lg md:text-2xl font-black font-mono ${velocitySummary.today_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{velocitySummary.today_pnl >= 0 ? '+' : ''}${velocitySummary.today_pnl?.toLocaleString() || '0.00'}</div><div className="text-[8px] md:text-[10px] text-slate-400 font-bold uppercase tracking-tighter">{velocitySummary.executions_today} Executions</div></div>
                    <div className="glass p-4 md:p-6 rounded-[1.5rem] md:rounded-[2rem] border-white/10 space-y-1 md:space-y-2 opacity-50"><span className="text-[7px] md:text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">IBKR Net Liq</span><div className="text-lg md:text-2xl font-black text-slate-400 font-mono">---</div></div>
                    <div className="glass p-4 md:p-6 rounded-[1.5rem] md:rounded-[2rem] border-white/10 space-y-1 md:space-y-2 opacity-50"><span className="text-[7px] md:text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">Real-Time P&L</span><div className="text-lg md:text-2xl font-black text-slate-400 font-mono">---</div></div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">{hft.map((h, i) => (<div key={i} className="glass rounded-3xl p-6 border-white/10 shadow-2xl flex flex-col gap-6 group hover:border-blue-500/30 transition-all relative overflow-hidden font-outfit uppercase"><div className="absolute top-0 right-0 p-4 opacity-[0.03] text-4xl font-black italic select-none font-outfit uppercase">{h.asset_class}</div><div className="space-y-1"><span className="text-2xl font-black text-white italic tracking-tighter group-hover:text-blue-400 transition-colors uppercase leading-none font-outfit">{h.ticker}</span><div className={`text-[9px] font-black uppercase tracking-widest flex items-center gap-2 ${h.fusion_signal?.includes('BUY') ? 'text-emerald-400' : 'text-rose-400'}`}>{h.fusion_signal || 'NEUTRAL'}</div></div><div className="grid grid-cols-4 gap-1 border-y border-white/5 py-3">{['1m', '5m', '30m', '1h'].map(t => (<div key={t} className="flex flex-col items-center"><span className="text-[7px] text-slate-600 uppercase font-black">{t}</span><span className={`text-[10px] font-bold font-mono ${h.velocity_estimates?.[t]?.includes('+') ? 'text-blue-400' : 'text-orange-400'}`}>{h.velocity_estimates?.[t] || '--'}</span></div>))}</div><div className="flex justify-between items-center text-[10px] font-black font-outfit"><span className="text-slate-500 uppercase">Pressure</span><span className="text-white font-mono">{(h.pressure_value || 0).toFixed(2)}</span></div></div>))}</div>
                <div className="space-y-6"><div className="flex justify-between items-center"><h3 className="text-sm md:text-xl font-black text-white uppercase tracking-widest font-outfit opacity-60 italic">Sim Execution Log (HKT)</h3><button className="px-3 md:px-4 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 text-[8px] md:text-[10px] font-black uppercase border border-white/10 transition-all font-outfit">Export</button></div><div className="glass rounded-[1.5rem] md:rounded-[2.5rem] overflow-hidden shadow-2xl border-white/10"><div className="overflow-x-auto max-h-[500px] overflow-y-auto custom-scrollbar"><table className="w-full text-left font-outfit uppercase relative min-w-[700px]"><thead className="bg-black/80 backdrop-blur-md text-slate-500 text-[10px] font-black tracking-[0.2em] sticky top-0 z-10 border-b border-white/10"><tr><th className="px-8 py-5">Time (HKT)</th><th className="px-8 py-5">Ticker</th><th className="px-8 py-5">Side</th><th className="px-8 py-5">Price</th><th className="px-8 py-5">Qty</th><th className="px-8 py-5">Value</th><th className="px-8 py-5 text-right">P&L</th></tr></thead><tbody className="divide-y divide-white/5">{velocityTrades.length > 0 ? velocityTrades.slice(0, 50).map((t, i) => (<tr key={i} className="hover:bg-white/[0.02] transition-colors group"><td className="px-8 py-5 text-[10px] font-bold text-slate-500 font-mono">{new Date(t.timestamp).toLocaleTimeString('en-HK', { timeZone: 'Asia/Hong_Kong', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}</td><td className="px-8 py-5 text-sm font-black text-white italic">{t.ticker}{t.strategy && t.strategy !== 'MANUAL_OVERRIDE' && (<span className="ml-2 px-1.5 py-0.5 rounded bg-blue-500/10 text-[8px] font-black text-blue-400 border border-blue-500/20 uppercase tracking-widest">SIM</span>)}</td><td className="px-8 py-5"><span className={`px-2 py-0.5 rounded text-[9px] font-black ${t.side === 'BUY' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>{t.side}</span></td><td className="px-8 py-5 text-sm font-bold text-slate-300 font-mono">${t.price?.toFixed(2)}</td><td className="px-8 py-5 text-sm font-bold text-slate-300 font-mono">{t.quantity}</td><td className="px-8 py-5 text-sm font-bold text-slate-300 font-mono">${t.total_value?.toLocaleString()}</td><td className={`px-8 py-5 text-sm font-black font-mono text-right ${t.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{t.pnl !== null ? `${t.pnl >= 0 ? '+' : ''}${t.pnl?.toLocaleString()}` : '---'}</td></tr>)) : (<tr><td colSpan="7" className="px-8 py-12 text-center text-slate-600 font-bold italic uppercase tracking-widest">No executions recorded in current cycle</td></tr>)}</tbody></table></div></div></div>
            </div>
        )}

        {activeTab === 'quant' && quantTab === 'live' && (
            <div className="space-y-16 animate-in fade-in slide-in-from-bottom-6 duration-700 text-left">
                <div className="flex flex-col md:flex-row md:items-baseline justify-between gap-8 border-b border-white/5 pb-8 font-outfit uppercase">
                   <div className="flex items-baseline gap-6 font-outfit"><h2 className="text-2xl md:text-3xl font-black text-white italic font-outfit leading-none uppercase tracking-tightest">Live Execution <span className="ml-4 text-[10px] bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded-full border border-emerald-500/20 tracking-widest">PAPER_TRADING</span></h2><button onClick={() => setIsBulkOpen(true)} className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-black uppercase border border-emerald-500/20 transition-all shadow-xl glow-emerald flex items-center gap-2"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3"><path d="M12 5v14M5 12h14"/></svg><span>Deploy Cluster</span></button></div>
                   <div className="flex items-center gap-4 font-outfit uppercase">{ibAccount && ibAccount.length > 0 ? (<select value={selectedAccountId} onChange={(e) => { const id = e.target.value; setSelectedAccountId(id); fetchIbData(id); }} className="bg-black/60 border border-blue-500/40 rounded-xl px-4 py-2 text-[10px] font-black text-white outline-none focus:border-blue-500 appearance-none pr-10 uppercase font-outfit shadow-[0_0_15px_rgba(59,130,246,0.1)]">{ibAccount.map(acc => (<option key={acc.id} value={acc.id}>{acc.id} ({acc.accountTitle || 'Active'})</option>))}</select>) : (ibStatus.web === 'Authenticated' && (<button onClick={fetchIbData} className="px-4 py-2 rounded-xl bg-amber-500/20 text-amber-400 text-[9px] font-black uppercase border border-amber-500/20 animate-pulse font-outfit leading-none">Link_Account_Data</button>))}<div className="flex flex-col text-right font-outfit"><span className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">IBKR_LINK_STATUS</span><span className={`text-xs font-bold font-mono ${ibStatus.web === 'Authenticated' ? 'text-emerald-400' : 'text-rose-400'}`}>{ibStatus.web}</span></div>{ibStatus.web !== 'Authenticated' ? (<div className="flex gap-2"><button onClick={() => { const width = 600; const height = 900; const left = (window.screen.width - width) / 2; const top = (window.screen.height - height) / 2; window.open('/sso/Login?forwardTo=22', 'ib_login_popup', `width=${width},height=${height},top=${top},left=${left},resizable=yes,scrollbars=yes,status=yes`); }} className="px-6 py-2 rounded-xl bg-blue-600 text-white text-[10px] font-black uppercase border border-blue-500 shadow-lg glow-blue font-outfit leading-none font-black">Authorize_Popup</button><button onClick={fetchIbData} className="px-4 py-2 rounded-xl bg-white/10 text-slate-400 text-[10px] font-black uppercase border border-white/10 hover:bg-white/20 transition-all font-outfit leading-none">Sync_Session</button></div>) : (<div className="flex gap-2"><button onClick={() => { fetchIbData(); fetchData(); }} className="px-6 py-2 rounded-xl bg-emerald-500/20 text-emerald-400 text-[10px] font-black uppercase border border-emerald-500/20 transition-all font-outfit leading-none font-black">Refresh_Session</button><button onClick={connectIb} className="px-6 py-2 rounded-xl bg-white/5 hover:bg-blue-600 text-slate-300 hover:text-white text-[10px] font-black uppercase border border-white/10 transition-all font-outfit shadow-lg leading-none font-black">Init_Socket</button></div>)}</div>
                </div>
                <div className="grid grid-cols-12 gap-8">
                    <div className="col-span-12 lg:col-span-8 space-y-8">
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-6">
                            <div className="glass p-4 md:p-6 rounded-[1.5rem] md:rounded-[2rem] border-white/10 space-y-1 md:space-y-2"><span className="text-[7px] md:text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">IBKR Net Liq</span><div className="text-lg md:text-2xl font-black text-emerald-400 font-mono">{activeAccount?.netLiquidation?.toLocaleString(undefined, {minimumFractionDigits: 2}) ? `$${activeAccount.netLiquidation.toLocaleString(undefined, {minimumFractionDigits: 2})}` : '---'}</div><div className="text-[8px] md:text-[10px] text-slate-400 font-bold uppercase tracking-tighter">BP: {activeAccount?.buyingPower ? `$${activeAccount.buyingPower.toLocaleString(undefined, {minimumFractionDigits: 2})}` : '---'}</div></div>
                            <div className="glass p-4 md:p-6 rounded-[1.5rem] md:rounded-[2rem] border-white/10 space-y-1 md:space-y-2"><span className="text-[7px] md:text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">Real-Time P&L</span><div className={`text-lg md:text-2xl font-black font-mono ${(Array.isArray(ibPositions) ? ibPositions : []).reduce((acc, p) => acc + (p.unrealizedPnl || 0), 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{(Array.isArray(ibPositions) ? ibPositions : []).reduce((acc, p) => acc + (p.unrealizedPnl || 0), 0) >= 0 ? '+' : ''}${(Array.isArray(ibPositions) ? ibPositions : []).reduce((acc, p) => acc + (p.unrealizedPnl || 0), 0).toLocaleString(undefined, {minimumFractionDigits: 2})}</div><div className="text-[8px] md:text-[10px] text-slate-400 font-bold uppercase tracking-tighter">Unrealized</div></div>
                            <div className="glass p-4 md:p-6 rounded-[1.5rem] md:rounded-[2rem] border-white/10 space-y-1 md:space-y-2 col-span-2 md:col-span-1"><span className="text-[7px] md:text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">Executions Today</span><div className="text-lg md:text-2xl font-black text-white font-mono">{velocityTrades.filter(t => !t.strategy || !t.strategy.includes('SIMULATION')).length}</div><div className="text-[8px] md:text-[10px] text-slate-400 font-bold uppercase tracking-tighter">Live Orders</div></div>
                        </div>
                        <StrategyMatrix matrix={quantMatrix} onDeploy={initiateDeploy} activeStrategies={quantStrategies.filter(s => s.params?.execution_mode !== 'SIMULATION')} mode="live" onOpenBulk={() => setIsBulkOpen(true)} />
                    </div>
                    <div className="col-span-12 lg:col-span-4"><InventoryCommandTable positions={ibPositions} onClosePosition={closePosition} /></div>
                </div>
                <div className="space-y-6"><div className="flex justify-between items-center"><h3 className="text-sm md:text-xl font-black text-white uppercase tracking-widest font-outfit opacity-60 italic">Live Execution Log (HKT)</h3><button className="px-3 md:px-4 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 text-[8px] md:text-[10px] font-black uppercase border border-white/10 transition-all font-outfit">Export</button></div><div className="glass rounded-[1.5rem] md:rounded-[2.5rem] overflow-hidden shadow-2xl border-white/10"><div className="overflow-x-auto max-h-[500px] overflow-y-auto custom-scrollbar"><table className="w-full text-left font-outfit uppercase relative min-w-[700px]"><thead className="bg-black/80 backdrop-blur-md text-slate-500 text-[10px] font-black tracking-[0.2em] sticky top-0 z-10 border-b border-white/10"><tr><th className="px-8 py-5">Time (HKT)</th><th className="px-8 py-5">Ticker</th><th className="px-8 py-5">Side</th><th className="px-8 py-5">Price</th><th className="px-8 py-5">Qty</th><th className="px-8 py-5">Value</th><th className="px-8 py-5 text-right">P&L</th></tr></thead><tbody className="divide-y divide-white/5">{velocityTrades.filter(t => !t.strategy || !t.strategy.includes('SIMULATION')).length > 0 ? velocityTrades.filter(t => !t.strategy || !t.strategy.includes('SIMULATION')).slice(0, 50).map((t, i) => (<tr key={i} className="hover:bg-white/[0.02] transition-colors group"><td className="px-8 py-5 text-[10px] font-bold text-slate-500 font-mono">{new Date(t.timestamp).toLocaleTimeString('en-HK', { timeZone: 'Asia/Hong_Kong', hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}</td><td className="px-8 py-5 text-sm font-black text-white italic">{t.ticker}<span className="ml-2 px-1.5 py-0.5 rounded bg-emerald-500/10 text-[8px] font-black text-emerald-400 border border-emerald-500/20 uppercase tracking-widest">LIVE</span></td><td className="px-8 py-5"><span className={`px-2 py-0.5 rounded text-[9px] font-black ${t.side === 'BUY' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>{t.side}</span></td><td className="px-8 py-5 text-sm font-bold text-slate-300 font-mono">${t.price?.toFixed(2)}</td><td className="px-8 py-5 text-sm font-bold text-slate-300 font-mono">{t.quantity}</td><td className="px-8 py-5 text-sm font-bold text-slate-300 font-mono">${t.total_value?.toLocaleString()}</td><td className={`px-8 py-5 text-sm font-black font-mono text-right ${t.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{t.pnl !== null ? `${t.pnl >= 0 ? '+' : ''}${t.pnl?.toLocaleString()}` : '---'}</td></tr>)) : (<tr><td colSpan="7" className="px-8 py-12 text-center text-slate-600 font-bold italic uppercase tracking-widest">No live executions recorded</td></tr>)}</tbody></table></div></div></div>
            </div>
        )}

        {activeTab === 'performance' && (
            <div className="space-y-16 text-left animate-in fade-in slide-in-from-bottom-6 duration-700">
                <div className="flex items-baseline gap-6 pb-4 border-b border-white/5"><h2 className="text-2xl md:text-3xl font-black text-white italic font-outfit leading-none uppercase tracking-tightest font-outfit leading-none uppercase">Core Stats</h2><span className="h-px flex-1 bg-white/5" /></div>
                <div className="grid lg:grid-cols-12 gap-12 items-start">
                    <div className="lg:col-span-8 glass p-8 md:p-12 rounded-[4rem] shadow-2xl space-y-12 relative overflow-hidden"><div className="absolute top-0 right-0 p-12 opacity-[0.03] text-7xl md:text-9xl font-black italic select-none font-outfit tracking-tighter leading-none font-outfit">EQUITY</div><div className="space-y-3 relative z-10 font-outfit"><h3 className="text-xl md:text-2xl font-black text-white uppercase tracking-widest font-outfit italic leading-none font-outfit uppercase">Simulated Equity Curve</h3><div className="flex items-center gap-8 pt-2"><div className="flex items-center gap-3 font-outfit"><span className="h-2.5 w-2.5 rounded-full bg-blue-500 shadow-[0_0_10px_#3b82f6]" /> <span className="text-[11px] font-bold uppercase text-slate-500 font-outfit tracking-widest">Adopted Strategy</span></div><div className="flex items-center gap-3 font-outfit"><span className="h-2.5 w-2.5 rounded-full bg-slate-700" /> <span className="text-[11px] font-bold uppercase text-slate-500 font-outfit tracking-widest font-outfit">S&P 500 Index</span></div></div></div><EquityCurve data={performance.curve} /></div>
                    <div className="lg:col-span-4 glass p-8 md:p-12 rounded-[4rem] shadow-2xl flex flex-col gap-12 font-outfit uppercase"><h3 className="text-xl md:text-2xl font-black text-white uppercase tracking-widest border-b border-white/5 pb-10 font-outfit italic leading-none text-left font-outfit uppercase">Yield Matrix</h3><div className="space-y-10">{performance.metrics.map((m, i) => (<div key={i} className="flex justify-between items-center group font-outfit"><div className="flex flex-col text-left font-outfit"><span className="text-[11px] font-black text-slate-600 uppercase tracking-[0.1em] md:tracking-[0.2em] font-outfit">Since {m.period}</span><span className="text-base md:text-lg font-bold text-white italic group-hover:text-blue-400 transition-colors font-outfit tracking-tight leading-none mt-2 font-black">{m.period === 'YEARLY' ? 'YTD Return' : m.period === 'QUARTERLY' ? 'Alpha' : 'ROI'}</span></div><div className="text-right font-outfit font-mono"><div className="flex items-center gap-3 font-outfit font-mono"><span className={`text-xl md:text-2xl font-black font-mono tracking-tighter ${m.strategy_return >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>{(m.strategy_return * 100).toFixed(1)}%</span></div></div></div>))}</div></div>
                </div>
            </div>
        )}

        {activeTab === 'config' && (
            <div className="space-y-16 text-left animate-in fade-in slide-in-from-bottom-6 duration-700">
                <div className="flex flex-col md:flex-row md:items-baseline justify-between gap-8 border-b border-white/5 pb-8 font-outfit uppercase">
                    <div className="flex items-baseline gap-6 font-outfit uppercase"><h2 className="text-2xl md:text-3xl font-black text-white italic tracking-tightest uppercase font-outfit leading-none font-outfit uppercase">System Node</h2><span className="px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-[10px] font-black border border-blue-500/20 tracking-widest">v2.9_STABLE</span></div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
                    {[{ id: 'indices', name: 'Macro_Sync', desc: 'Global Indices & Market Mood vectors.' }, { id: 'stocks', name: 'Alpha_Universe', desc: 'Predictive Neural Models for Equity.' }, { id: 'fx', name: 'Liquidity_Layer', desc: 'FX Liquidity & Interest Differentials.' }, { id: 'commodities', name: 'Hard_Assets', desc: 'Energy & Metals sync.' }, { id: 'crypto', name: 'Digital_Compute', desc: 'On-chain velocity audits.' }, { id: 'hft', name: 'Velocity_HFT', desc: 'High-Frequency Pressure Values.' }].map(comp => {
                        const schedule = syncSchedules.find(s => s.component === comp.id);
                        return (
                            <div key={comp.id} className={`glass rounded-[3rem] p-10 border-white/10 shadow-2xl flex flex-col gap-10 group hover:border-blue-500/40 transition-all font-outfit uppercase`}>
                                <div className="space-y-3 font-outfit font-black"><div className="flex justify-between items-start"><h3 className="text-2xl font-black text-white uppercase italic tracking-tighter font-outfit group-hover:text-blue-400 transition-colors leading-none font-outfit uppercase">{comp.name}</h3></div><p className="text-sm text-slate-500 leading-relaxed font-medium italic font-outfit lowercase">"{comp.desc}"</p></div>
                                <div className="space-y-3 pt-6 border-t border-white/5 font-outfit"><span className="text-[10px] font-black text-slate-500 uppercase tracking-widest leading-none block font-outfit">Auto-Sync Frequency</span><div className="flex gap-2 flex-wrap font-outfit">{['pause', '1min', '5min', '1hr', '1day'].map(freq => { const isActive = schedule?.frequency === freq; return (<button key={freq} className={`px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest border transition-all font-outfit ${isActive ? 'bg-blue-600 border-blue-600 text-white shadow-[0_0_10px_#3b82f6]' : 'border-white/5 text-slate-600 hover:text-slate-400 hover:border-white/10'}`}>{freq}</button>); })}</div></div>
                                <div className="flex items-center justify-between mt-auto pt-10 border-t border-white/5 font-outfit"><div className="flex flex-col text-left font-outfit font-mono"><span className="text-[10px] font-black text-slate-600 uppercase font-outfit leading-none font-outfit">Node_Status</span><span className={`text-base font-bold font-mono italic mt-1 ${maintenanceStatus[comp.id] === 'Live' ? 'text-emerald-400 text-glow' : 'text-blue-400'}`}>{maintenanceStatus[comp.id] || 'NODE_IDLE'}</span></div></div>
                            </div>
                        );
                    })}
                </div>
            </div>
        )}
      </main>

      <footer className="fixed bottom-0 left-0 w-full h-12 glass border-t border-white/5 backdrop-blur-3xl z-[110] flex items-center px-12 justify-between">
         <div className="flex items-center gap-8"><div className="flex items-center gap-2.5 font-outfit"><div className="h-2 w-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_#10b981]" /><span className="text-[10px] font-black text-slate-500 uppercase tracking-widest font-outfit leading-none">Node_0.129.4 // OK</span></div><div className="h-4 w-px bg-white/5" /><div className="hidden md:flex items-center gap-2.5 font-outfit"><span className="text-[10px] font-black text-slate-500 uppercase tracking-widest font-outfit leading-none">Neural Compute: 94.2 TFLOPS</span></div></div>
         <div className="hidden sm:flex items-center gap-6 text-[10px] font-black text-slate-600 uppercase tracking-widest font-outfit italic leading-none font-black">Institutional v2.9 ELITE // Global Portfolio Control</div>
      </footer>
    </div>
  );
};

export default App;
