import React, { useState, useEffect, useMemo } from 'react';

// --- UTILS & HELPERS ---
const parseRationale = (raw) => {
  if (!raw) return { mood: 'Neutral', highlights: [], body: '', industries: { short_term: [], long_term: [] } };
  try {
    const data = JSON.parse(raw);
    return {
      mood: data.market_mood || 'Neutral',
      highlights: [data.conclusion],
      body: data.rationale || '',
      industries: data.recommended_industries || { short_term: [], long_term: [] }
    };
  } catch {
    return { mood: 'Neutral', highlights: [], body: raw.slice(0, 160) + '...', industries: { short_term: [], long_term: [] } };
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

const HighDensityCard = ({ item, type = "STOCK" }) => {
  const isUp = item.change >= 0;
  const metrics = type === 'STOCK' ? [
    { label: 'P/E', value: item.metrics?.pe || '---', color: 'text-orange-400' },
    { label: 'FCF', value: item.metrics?.fcf || '---', color: 'text-emerald-400' },
    { label: 'Sharpe', value: item.metrics?.sharpe || '---', color: 'text-blue-400' },
    { label: 'MDD', value: item.metrics?.mdd || '---', color: 'text-rose-400' },
    { label: 'Corr', value: item.metrics?.corr || '0.5', color: 'text-slate-400' }
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

const StrategyDeployModal = ({ isOpen, onClose, template, ticker, onConfirm }) => {
  if (!isOpen || !template) return null;
  
  return (
    <div className="fixed inset-0 z-[250] flex items-center justify-center p-4 md:p-6 bg-black/90 backdrop-blur-xl animate-in fade-in duration-300 font-outfit">
      <div className="glass max-w-2xl w-full rounded-[2.5rem] p-8 md:p-12 shadow-3xl border-white/10 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-[0.03] text-9xl font-black italic select-none uppercase">DEPLOY</div>
        
        <button onClick={onClose} className="absolute top-8 right-8 p-2 rounded-full hover:bg-white/5 transition-colors text-slate-500">
          <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M18 6L6 18M6 6l12 12" /></svg>
        </button>

        <div className="space-y-8 relative z-10">
           <div>
             <span className="text-[10px] font-black text-blue-500 uppercase tracking-[0.3em]">Strategy Configuration</span>
             <h2 className="text-3xl md:text-4xl font-black text-white italic tracking-tight uppercase mt-1">{template.name}</h2>
             <div className="flex items-center gap-3 mt-3">
                <span className="px-3 py-1 rounded-lg bg-white/5 text-[10px] font-bold text-slate-300 uppercase tracking-widest border border-white/10">{ticker}</span>
                <span className="px-3 py-1 rounded-lg bg-emerald-500/10 text-[10px] font-bold text-emerald-400 uppercase tracking-widest border border-emerald-500/20">Ready to Deploy</span>
             </div>
           </div>

           <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
               <div className="space-y-4">
                   <div className="space-y-1">
                       <span className="text-[9px] text-slate-500 font-black uppercase tracking-widest">Logic Core</span>
                       <p className="text-sm text-slate-200 font-medium leading-relaxed">"{template.description}"</p>
                   </div>
                   <div className="space-y-1">
                       <span className="text-[9px] text-slate-500 font-black uppercase tracking-widest">Execution Frequency</span>
                       <p className="text-sm text-white font-mono font-bold">{template.frequency}</p>
                   </div>
                   <div className="space-y-1">
                       <span className="text-[9px] text-slate-500 font-black uppercase tracking-widest">Risk Rules</span>
                       <p className="text-xs text-slate-300 font-mono border-l-2 border-blue-500/30 pl-3">{template.risk_management}</p>
                   </div>
               </div>

               <div className="glass bg-white/[0.02] p-6 rounded-3xl border-white/5 space-y-5">
                   <span className="text-[10px] font-black text-amber-500 uppercase tracking-[0.2em] border-b border-white/5 pb-2 block">Backtest Audit (30D)</span>
                   <div className="space-y-3">
                       <div className="flex justify-between items-center">
                           <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Accuracy (1D)</span>
                           <span className="text-base font-black text-white font-mono">{template.backtest_metrics["1d_accuracy"]}</span>
                       </div>
                       <div className="flex justify-between items-center">
                           <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Accuracy (7D)</span>
                           <span className="text-base font-black text-white font-mono">{template.backtest_metrics["7d_accuracy"]}</span>
                       </div>
                       <div className="flex justify-between items-center">
                           <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Net Return</span>
                           <span className="text-base font-black text-emerald-400 font-mono">{template.backtest_metrics["30d_return"]}</span>
                       </div>
                       <div className="flex justify-between items-center">
                           <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Sharpe Ratio</span>
                           <span className="text-base font-black text-blue-400 font-mono">{template.backtest_metrics["sharpe_ratio"]}</span>
                       </div>
                   </div>
               </div>
           </div>

           <button onClick={() => onConfirm(ticker, template.id)} className="w-full py-5 rounded-2xl bg-blue-600 text-white text-xs font-black uppercase tracking-[0.25em] hover:bg-blue-500 transition-all shadow-2xl glow-blue mt-4">
               Confirm & Activate Strategy
           </button>
        </div>
      </div>
    </div>
  );
};

const StrategyMatrix = ({ matrix, onDeploy, onToggle, onDelete }) => {
  const [selectedStrat, setSelectedStrat] = useState(null);

  // Safely derive keys
  const keys = useMemo(() => (matrix ? Object.keys(matrix) : []), [matrix]);

  // Update selection if matrix loads later
  useEffect(() => {
      if (keys.length > 0 && !selectedStrat) {
          setSelectedStrat(keys[0]);
      }
  }, [keys]); 

  // If we have nothing to render, just return null, don't crash
  if (!matrix || keys.length === 0) return null;

  const activeData = selectedStrat ? matrix[selectedStrat] : null;
  
  // Extra safety: if selectedStrat points to non-existent key (race condition), fallback
  if (!activeData && keys.length > 0) return null;
  if (!activeData) return null;
  
  const commonPairs = ["EURUSD=X", "USDJPY=X", "GBPUSD=X", "AUDUSD=X", "BTC-USD"];

  return (
    <div className="space-y-6">
        <div className="flex gap-4 overflow-x-auto pb-2">
            {Object.entries(matrix).map(([key, data]) => (
                <button 
                    key={key}
                    onClick={() => setSelectedStrat(key)}
                    className={`flex-1 min-w-[200px] glass p-4 rounded-2xl border text-left transition-all ${selectedStrat === key ? 'border-blue-500 bg-blue-500/10' : 'border-white/10 hover:bg-white/5'}`}
                >
                    <div className="flex justify-between items-start mb-2">
                        <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">{data.name}</span>
                        <span className={`text-xs font-black font-mono ${data.total_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {data.total_pnl >= 0 ? '+' : ''}${data.total_pnl.toLocaleString()}
                        </span>
                    </div>
                    <div className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">{data.total_trades} Trades // {data.win_rate.toFixed(1)}% WR</div>
                </button>
            ))}
        </div>

        <div className="glass p-6 md:p-8 rounded-[2.5rem] border-white/10 relative overflow-hidden">
             <div className="absolute top-0 right-0 p-8 opacity-[0.02] text-8xl font-black italic select-none uppercase">MATRIX</div>
             <div className="relative z-10 space-y-6">
                 <div>
                     <h3 className="text-2xl font-black text-white italic tracking-tighter uppercase font-outfit">{activeData.name} // Performance</h3>
                     <p className="text-sm text-slate-400 font-medium max-w-2xl mt-2">"{activeData.description}"</p>
                 </div>

                 <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                     {commonPairs.map(pair => {
                         const pairData = activeData.pairs[pair];
                         return (
                             <div key={pair} className={`p-4 rounded-2xl border transition-all ${pairData ? 'bg-white/[0.02] border-white/10' : 'border-dashed border-white/5 opacity-60'}`}>
                                 <div className="flex justify-between items-center mb-3">
                                     <span className="text-sm font-black text-white font-outfit tracking-tight">{pair}</span>
                                     {pairData ? (
                                         <div className="flex gap-2">
                                             <button onClick={() => onToggle(pairData.id)} className={`w-2 h-2 rounded-full ${pairData.is_active ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : 'bg-slate-600'}`} title="Toggle Status" />
                                             <button onClick={() => onDelete(pairData.id)} className="text-[10px] text-rose-500 hover:text-white transition-colors">×</button>
                                         </div>
                                     ) : (
                                         <button onClick={() => onDeploy(pair, selectedStrat)} className="text-[9px] font-black uppercase tracking-widest text-blue-400 hover:text-white transition-colors">+ Deploy</button>
                                     )}
                                 </div>
                                 {pairData ? (
                                     <div className="space-y-1">
                                         <div className="flex justify-between text-[10px] uppercase font-bold text-slate-500">
                                             <span>P&L</span>
                                             <span className={`font-mono ${pairData.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>${pairData.pnl.toLocaleString()}</span>
                                         </div>
                                         <div className="flex justify-between text-[10px] uppercase font-bold text-slate-500">
                                             <span>Trades</span>
                                             <span className="text-white font-mono">{pairData.trades}</span>
                                         </div>
                                     </div>
                                 ) : (
                                     <div className="h-8 flex items-center justify-center text-[9px] font-bold text-slate-600 uppercase tracking-widest">
                                         Inactive
                                     </div>
                                 )}
                             </div>
                         );
                     })}
                 </div>
             </div>
        </div>
    </div>
  );
};

const MiniEquityCurve = ({ data, color = "#10b981", height = 40 }) => {
  if (!data || data.length < 2) return <div style={{height}} className="w-full bg-white/5 animate-pulse rounded-lg" />;
  const vals = data.map(d => d.val);
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const range = max - min || 1;
  const width = 200;
  const points = data.map((d, i) => 
    `${(i / (data.length - 1)) * width},${height - ((d.val - min) / range) * height}`
  ).join(' ');
  
  return (
    <div className="w-full h-10 mt-2">
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className="overflow-visible">
        <polyline fill="none" stroke={color} strokeWidth="3" points={points} strokeLinejoin="round" strokeLinecap="round" className="drop-shadow-[0_0_8px_rgba(16,185,129,0.3)]" />
      </svg>
    </div>
  );
};

const QuantStrategyCard = ({ strat, onToggle }) => {
    const isWin = strat.current_pnl >= 0;
    const deleteStrategy = async (id) => {
        if (window.confirm("Terminate and Liquidate this strategy?")) {
            await fetch(`${API_BASE}/quant/strategies/delete/${id}`, { method: 'DELETE' });
            await fetchQuantStrategies();
        }
    };

    return (
        <div className={`glass p-6 rounded-[2.5rem] border-white/10 space-y-6 transition-all group hover:border-blue-500/30 relative overflow-hidden ${!strat.is_active ? 'opacity-50 grayscale' : ''}`}>
            <div className="absolute top-0 right-0 p-6 opacity-[0.03] text-4xl font-black italic select-none font-outfit">QUANT</div>
            <div className="flex justify-between items-start">
                <div className="flex flex-col">
                    <span className="text-xl font-black text-white italic font-outfit uppercase tracking-tighter">{strat.name}</span>
                    <span className="text-[10px] font-black text-blue-500 uppercase tracking-widest mt-1">{strat.target_ticker} // MR CORE</span>
                </div>
                <div className="flex gap-2">
                    <button onClick={() => onToggle(strat.id)} className={`px-4 py-1.5 rounded-full text-[9px] font-black uppercase tracking-widest border transition-all ${strat.is_active ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-white/5 text-slate-500 border-white/10'}`}>
                        {strat.is_active ? 'Active' : 'Paused'}
                    </button>
                    <button onClick={() => deleteStrategy(strat.id)} className="h-7 w-7 rounded-full bg-rose-500/10 text-rose-500 border border-rose-500/20 flex items-center justify-center text-xs hover:bg-rose-500 hover:text-white transition-all">×</button>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 py-4 border-y border-white/5">
                <div className="flex flex-col">
                    <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest">Total P&L</span>
                    <span className={`text-xl font-black font-mono ${isWin ? 'text-emerald-400' : 'text-rose-400'}`}>
                        {isWin ? '+' : ''}${strat.current_pnl?.toLocaleString()}
                    </span>
                </div>
                <div className="flex flex-col text-right">
                    <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest">Win Rate</span>
                    <span className="text-xl font-black text-white font-mono italic">{(strat.winning_trades / (strat.total_trades || 1) * 100).toFixed(1)}%</span>
                </div>
            </div>

            <div className="space-y-2">
                <span className="text-[8px] font-black text-slate-600 uppercase tracking-widest">Live Alpha Drift</span>
                <MiniEquityCurve data={strat.equity_curve} color={isWin ? "#10b981" : "#f43f5e"} />
            </div>

            <div className="flex justify-between items-center pt-4 text-[9px] font-black uppercase font-outfit">
                <div className="flex gap-3">
                    <span className="text-slate-500">TP: <span className="text-white">{(strat.take_profit_pct * 100).toFixed(1)}%</span></span>
                    <span className="text-slate-500">SL: <span className="text-white">{(strat.stop_loss_pct * 100).toFixed(1)}%</span></span>
                </div>
                <span className="text-blue-400 italic">Target: {(strat.win_rate_target * 100).toFixed(0)}%</span>
            </div>
        </div>
    );
};

// --- MAIN APPLICATION ---
const App = () => {
  const [activeTab, setActiveTab] = useState('inventory');
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

  const fetchQuantStrategies = async () => {
    try {
        const resp = await fetch(`${API_BASE}/quant/strategies`);
        if (resp.ok) setQuantStrategies(await resp.json());
        
        const matrixResp = await fetch(`${API_BASE}/quant/performance/matrix`);
        if (matrixResp.ok) setQuantMatrix(await matrixResp.json());
    } catch (e) { console.error(e); }
  };

  const fetchStrategyTemplates = async () => {
    try {
        const resp = await fetch(`${API_BASE}/quant/templates`);
        if (resp.ok) setStrategyTemplates(await resp.json());
    } catch (e) { console.error(e); }
  };

  const initiateDeploy = (ticker, templateId) => {
      setDeployModalData({ isOpen: true, templateId, ticker });
  };

  const confirmDeploy = async (pair, templateId) => {
    setDeployModalData({ isOpen: false, templateId: null, ticker: null });
    setIsDeploying(true);
    try {
        await fetch(`${API_BASE}/quant/strategies/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pair, lot_size: 1000, template_id: templateId })
        });
        await fetchQuantStrategies();
    } catch (e) { console.error(e); } 
    finally { setIsDeploying(false); }
  };

  const toggleStrategy = async (id) => {
    await fetch(`${API_BASE}/quant/strategies/toggle/${id}`, { method: 'POST' });
    await fetchQuantStrategies();
  };

  const API_BASE = "/api";

  const [selectedAccountId, setSelectedAccountId] = useState(null);

  const fetchIbData = async () => {
    try {
      console.log("IBKR: Starting session sync check...");
      
      const statusCheck = async () => {
          // 1. Initial linkage call to "wake up" the session
          await fetch('/v1/api/iserver/accounts', { credentials: 'include' });
          
          const authResp = await fetch('/v1/api/iserver/auth/status', { credentials: 'include' });
          if (authResp.ok) {
              const authData = await authResp.json();
              return authData;
          }
          return null;
      };

      const authData = await statusCheck();
      if (authData && authData.authenticated) {
          setIbStatus(prev => ({ ...prev, web: 'Authenticated', status: 'Connected' }));
          
          // 2. Sync to backend
          await fetch(`${API_BASE}/velocity/ib/sync-session`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              credentials: 'include'
          });

          // 3. Fetch account summary
          const accResp = await fetch('/v1/api/portfolio/accounts', { credentials: 'include' });
          if (accResp.ok) {
            const accData = await accResp.json();
            console.log("IBKR: Raw Portfolio Accounts:", accData);
            
            if (accData && accData.length > 0) {
              const targetId = selectedAccountId || (accData.find(a => a.id.startsWith('DU')) || accData[0]).id;
              if (!selectedAccountId) setSelectedAccountId(targetId);

              // 4. Fetch specific account summary for high-fidelity balance data
              const summaryResp = await fetch(`/v1/api/portfolio/${targetId}/summary`, { credentials: 'include' });
              let summaryData = {};
              if (summaryResp.ok) {
                  summaryData = await summaryResp.json();
                  console.log("IBKR: Account Summary:", summaryData);
              }

              const processedAccounts = accData.map(a => {
                  const isTarget = a.id === targetId;
                  return {
                    ...a,
                    // Use summary data if available for the target account, fallback to portfolio list keys
                    netLiquidation: (isTarget ? (summaryData.netliquidation?.amount || summaryData.netLiquidation?.amount) : null) || 
                                    a.netLiquidationValue || a.netLiquidation || a.totalCashValue || a.amount || a.equity || 0,
                    buyingPower: (isTarget ? (summaryData.buyingpower?.amount || summaryData.buyingPower?.amount) : null) || 
                                 a.buyingPower || a.availableFunds || a.cash || 0
                  };
              });
              
              setIbAccount(processedAccounts);
              
              const posResp = await fetch(`/v1/api/portfolio/${targetId}/positions/0`, { credentials: 'include' });
              if (posResp.ok) {
                  const posData = await posResp.json();
                  setIbPositions(Array.isArray(posData) ? posData : []);
              }
            } else {
                console.warn("IBKR: Portfolio accounts empty. Triggering iserver/accounts handshake...");
                await fetch('/v1/api/iserver/accounts', { credentials: 'include' });
            }
          }
      } else {
          setIbStatus(prev => ({ ...prev, web: 'Unauthorized' }));
      }
    } catch (e) { console.error("IBKR: Critical Fetch Error:", e); }
  };

  const activeAccount = useMemo(() => {
    if (!ibAccount || !selectedAccountId) return null;
    return ibAccount.find(a => a.id === selectedAccountId) || ibAccount[0];
  }, [ibAccount, selectedAccountId]);

  const fetchData = async () => {
    try {
      const endpoints = [
        'macro/pulse', 'signals/1', 'fx/pairs', 'crypto/pairs', 'commodities/all',
        'hft/matrix', 'inventory/evaluate', 'market/outlook', 'performance/strategy',
        'metadata/strategy_configs', 'metadata/sync_schedules', 'velocity/ib/status',
        'velocity/summary', 'velocity/trades'
      ];
      const responses = await Promise.all(endpoints.map(e => fetch(`${API_BASE}/${e}`)));
      const data = await Promise.all(responses.map(r => r.ok ? r.json() : null));
      if (data[0]) setMacro(data[0]);
      if (data[1]) setSignals(data[1]);
      if (data[2]) setFx(data[2]);
      if (data[3]) setCrypto(data[3]);
      if (data[4]) setCommodities(data[4]);
      if (data[5]) setHft(data[5]);
      if (data[6]) setInventory(data[6]);
      if (data[7]) setOutlook(data[7]);
      if (data[8]) setPerformance(data[8]);
      if (data[9]) setStrategyConfigs(data[9]);
      if (data[10]) setSyncSchedules(data[10]);
      if (data[11]) setIbStatus(data[11]);
      if (data[12]) setVelocitySummary(data[12]);
      if (data[13]) setVelocityTrades(data[13]);
    } catch (e) { console.error(e); }
  };

  const applySystemChanges = async () => {
    setIsApplying(true);
    try {
        await Promise.all(Object.entries(pendingConfigs).map(([ac, wr]) => 
            fetch(`${API_BASE}/metadata/strategy_configs/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ asset_class: ac, win_rate_target: parseFloat(wr) })
            })
        ));
        await Promise.all(Object.entries(pendingSchedules).map(([comp, freq]) => 
            fetch(`${API_BASE}/metadata/sync_schedules/update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ component: comp, frequency: freq })
            })
        ));
        setPendingConfigs({});
        setPendingSchedules({});
        await fetchData();
        alert("System configurations applied successfully.");
    } catch (e) {
        console.error(e);
        alert("Failed to apply some changes.");
    } finally {
        setIsApplying(false);
    }
  };

  const updateConfig = (asset_class, wr) => {
    setPendingConfigs(prev => ({ ...prev, [asset_class]: wr }));
    setStrategyConfigs(prev => prev.map(c => c.asset_class === asset_class ? { ...c, win_rate_target: wr } : c));
  };

  const updateSchedule = (component, frequency) => {
    setPendingSchedules(prev => ({ ...prev, [component]: frequency }));
    setSyncSchedules(prev => prev.map(s => s.component === component ? { ...s, frequency } : s));
  };

  const triggerSellAnalysis = async (ticker) => {
    setAnalysisStatus(prev => ({ ...prev, [ticker]: 'Analyzing...' }));
    try {
        await fetch(`${API_BASE}/inventory/analyze/${ticker}`, { method: 'POST' });
        setTimeout(() => {
            setAnalysisStatus(prev => ({ ...prev, [ticker]: 'Syncing' }));
            fetchData();
        }, 5000);
    } catch (e) { console.error(e); }
  };

  const triggerMaintenance = async (component) => {
    setMaintenanceStatus(prev => ({ ...prev, [component]: 'Syncing...' }));
    await fetch(`${API_BASE}/maintenance/refresh/${component}`, { method: 'POST' });
    setTimeout(fetchData, 3000);
  };

  const connectIb = async () => {
    setIbStatus(prev => ({...prev, status: 'Connecting...'}));
    await fetch(`${API_BASE}/velocity/ib/connect`, { method: 'POST' });
  };

  const executeManualTrade = async (ticker, action, quantity) => {
    if (!ibAccount || ibAccount.length === 0) {
        alert("IBKR Account not synchronized.");
        return;
    }
    try {
        const resp = await fetch(`${API_BASE}/velocity/trade/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ticker, action, quantity,
                account_id: ibAccount[0].id
            })
        });
        if (resp.ok) {
            alert(`Execution ${action} ${ticker} successful.`);
            fetchData();
        } else {
            const err = await resp.json();
            alert(`Execution failed: ${err.detail}`);
        }
    } catch (e) { console.error(e); }
  };

  const fetchNodeStatus = async () => {
    try {
      const components = ['indices', 'stocks', 'fx', 'commodities', 'crypto', 'hft'];
      const responses = await Promise.all(components.map(c => fetch(`${API_BASE}/maintenance/status/${c}`)));
      const data = await Promise.all(responses.map(r => r.ok ? r.json() : null));
      const newStatus = {};
      components.forEach((c, i) => {
        if (data[i]) newStatus[c] = data[i].status;
      });
      setMaintenanceStatus(newStatus);
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    fetchData();
    fetchNodeStatus();
    fetchIbData();
    fetchQuantStrategies();
    fetchStrategyTemplates();
    const interval = setInterval(() => {
        fetchData();
        fetchNodeStatus();
        fetchIbData();
        fetchQuantStrategies();
    }, 15000); // 15s for more reactive quant updates
    return () => clearInterval(interval);
  }, []);

  const getHKTTime = () => {
    return new Date().toLocaleTimeString('en-HK', { 
        timeZone: 'Asia/Hong_Kong', 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-[#05070a] text-slate-300 flex flex-col font-sans selection:bg-blue-500/30 overflow-x-hidden">
      
      <StrategyInfoModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} tab={activeTab} />
      <StrategyDeployModal 
        isOpen={deployModalData.isOpen} 
        onClose={() => setDeployModalData({ isOpen: false, templateId: null, ticker: null })} 
        template={strategyTemplates[deployModalData.templateId]}
        ticker={deployModalData.ticker}
        onConfirm={confirmDeploy}
      />
      
      <div className="md:h-24 glass border-b border-white/5 flex flex-wrap items-center px-4 md:px-8 sticky top-0 z-[100] backdrop-blur-2xl shadow-2xl">
        <div className="flex flex-wrap divide-x divide-white/5 shrink-0">
            {['US', 'HK', 'EU', 'CN', 'SG'].map(idx => (
                <MacroPill key={idx} label={idx} 
                    value={macro.indices?.[idx]?.value} 
                    change={macro.indices?.[idx]?.change} 
                    est={macro.indices?.[idx]?.estimates} 
                />
            ))}
        </div>
        <div className="ml-auto hidden lg:flex items-center gap-8 pl-10 pr-4 shrink-0">
           <div className="flex flex-col text-right">
              <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit mb-1 leading-none">Cluster State</span>
              <div className="flex items-center gap-2 justify-end">
                 <div className="h-1.5 w-1.5 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_#10b981]" />
                 <span className="text-xs font-bold text-white font-mono uppercase leading-none">Sync_OK</span>
              </div>
           </div>
           <div className="flex flex-col text-right min-w-[80px]">
              <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit leading-none mb-1">Local HKT</span>
              <span className="text-xs font-bold text-blue-400 font-mono italic leading-none">{getHKTTime()}</span>
           </div>
        </div>
      </div>

      <header className="px-6 md:px-12 py-8 md:py-10 bg-gradient-to-b from-blue-500/[0.02] to-transparent sticky top-20 md:top-24 z-[90] backdrop-blur-xl border-b border-white/5">
        <div className="max-w-[1600px] mx-auto flex flex-col lg:flex-row lg:items-center justify-between gap-8 md:gap-10">
            <div className="flex items-center gap-6">
                <div className="h-12 w-12 glass rounded-xl flex items-center justify-center border-blue-500/20 group cursor-pointer hover:scale-105 transition-all">
                   <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg"><span className="text-lg font-black text-white italic">O</span></div>
                </div>
                <div className="flex flex-col text-left">
                    <h1 className="text-2xl md:text-3xl font-black text-white tracking-tight uppercase italic font-outfit leading-none font-outfit uppercase font-black">ORCHESTRA <span className="text-blue-500 text-[10px] md:text-[12px] font-mono ml-3 not-italic tracking-widest">v2.9 ELITE</span></h1>
                    <div className="flex items-center gap-2 mt-2">
                        <span className="text-[9px] md:text-[11px] font-black text-slate-500 uppercase tracking-[0.2em] font-outfit">Institutional Command</span>
                    </div>
                </div>
            </div>
            <nav className="flex flex-wrap gap-1.5 p-1 glass rounded-2xl shadow-inner">
                {[
                  {id: 'inventory', label: 'Command'}, {id: 'research', label: 'Intelligence'}, {id: 'signals', label: 'Alpha'}, 
                  {id: 'fx', label: 'Forex'}, {id: 'crypto', label: 'Digital'}, {id: 'commodities', label: 'Assets'},
                  {id: 'hft', label: 'Velocity'}, {id: 'performance', label: 'Performance'}, {id: 'config', label: 'System'}
                ].map(tab => (
                    <button key={tab.id} onClick={() => setActiveTab(tab.id)} 
                      className={`px-4 md:px-6 py-2 md:py-3 rounded-lg md:rounded-xl text-[10px] md:text-[11px] font-black uppercase tracking-widest transition-all whitespace-nowrap font-outfit
                        ${activeTab === tab.id ? 'bg-white text-black shadow-2xl font-black' : 'text-slate-500 hover:text-slate-200 hover:bg-white/5'}`}>
                      {tab.label}
                    </button>
                ))}
            </nav>
        </div>
      </header>

      <main className="flex-1 p-6 md:p-12 max-w-[1600px] mx-auto w-full mb-32 space-y-10 md:space-y-16">
        
        {activeTab === 'inventory' && (
            <div className="glass p-4 md:p-6 rounded-[2rem] flex flex-col lg:flex-row lg:items-center justify-between gap-6 md:gap-10 relative overflow-hidden group shadow-2xl">
                <div className={`absolute top-0 left-0 h-full w-1.5 md:w-2 ${macro.system_risk === 'CRITICAL' ? 'bg-rose-500 shadow-[0_0_15px_#f43f5e]' : 'bg-blue-500 shadow-[0_0_15px_#3b82f6]'}`} />
                <div className="space-y-2 max-w-5xl text-left relative z-10">
                    <div className="flex items-center gap-3">
                        <span className={`text-[9px] font-black uppercase tracking-[0.3em] font-outfit ${macro.system_risk === 'CRITICAL' ? 'text-rose-500' : 'text-blue-500'}`}>Risk Radar: {macro.system_risk}</span>
                        <div className={`h-1.5 w-1.5 rounded-full animate-ping ${macro.system_risk === 'CRITICAL' ? 'bg-rose-500' : 'bg-blue-500'}`} />
                    </div>
                    <p className="text-sm md:text-lg text-white font-medium italic leading-relaxed text-left font-outfit tracking-tight uppercase">"{macro.shock_text || 'Synthesizing market noise...'}"</p>
                </div>
                <div className="glass bg-white/5 px-6 py-4 rounded-[1.5rem] text-center min-w-[150px] border-white/10 flex flex-col justify-center"><span className="text-[7px] font-black text-slate-500 uppercase block mb-1 font-outfit tracking-widest">Market Bias</span><span className={`text-base md:text-lg font-black italic font-outfit ${macro.system_risk === 'CRITICAL' ? 'text-rose-500' : 'text-blue-400'}`}>{macro.system_risk === 'CRITICAL' ? 'DEFENSIVE' : 'BULLISH'}</span></div>
            </div>
        )}

        {activeTab === 'inventory' && (
            <div className="space-y-12 text-left animate-in fade-in slide-in-from-bottom-6 duration-700">
                <div className="glass p-8 md:p-12 rounded-[2.5rem] shadow-2xl flex flex-wrap gap-6 md:gap-10 items-end relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-12 opacity-[0.03] text-7xl md:text-9xl font-black italic select-none font-outfit uppercase">DEPLOY</div>
                    <div className="flex flex-col gap-2 min-w-[160px] md:min-w-[200px] w-full md:w-auto font-outfit uppercase"><span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">Ticker</span><input className="bg-black/60 border border-white/10 rounded-2xl px-5 py-3.5 text-white outline-none focus:border-blue-500 font-mono text-sm uppercase" placeholder="NVDA / BTC-USD" value={newAsset.ticker} onChange={e => setNewAsset({...newAsset, ticker: e.target.value.toUpperCase()})} /></div>
                    <div className="flex flex-col gap-2 flex-1 md:flex-none font-outfit uppercase"><span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">Class</span><select className="bg-black/60 border border-white/10 rounded-2xl px-5 py-3.5 text-white outline-none focus:border-blue-500 appearance-none font-outfit font-bold pr-12 uppercase" value={newAsset.asset_class} onChange={e => setNewAsset({...newAsset, asset_class: e.target.value})}><option value="STOCK">STOCK</option><option value="FX">FX</option><option value="CRYPTO">CRYPTO</option><option value="COMMODITY">COMMODITY</option></select></div>
                    <div className="flex flex-col gap-2 font-outfit uppercase"><span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">Qty</span><input type="number" className="bg-black/60 border border-white/10 rounded-2xl px-5 py-3.5 text-white outline-none focus:border-blue-500 font-mono text-sm w-full md:w-32" value={newAsset.quantity} onChange={e => setNewAsset({...newAsset, quantity: parseFloat(e.target.value) || 0})} /></div>
                    <button onClick={() => executeManualTrade(newAsset.ticker, 'BUY', newAsset.quantity)} className="w-full md:w-auto px-12 py-4 rounded-2xl text-[12px] font-black uppercase tracking-[0.2em] bg-blue-600 hover:bg-blue-500 text-white shadow-xl glow-blue font-outfit">Execute</button>
                </div>
                <div className="glass rounded-[3rem] overflow-hidden shadow-2xl">
                    <div className="p-8 md:p-12 border-b border-white/10 flex flex-col md:flex-row justify-between items-center gap-6 bg-white/[0.02]">
                        <div className="flex items-center gap-4">
                           <h3 className="text-xl md:text-3xl font-black text-white uppercase italic tracking-tightest font-outfit leading-none">Portfolio</h3>
                           <button onClick={() => setIsModalOpen(true)} className="h-8 w-8 rounded-full glass border-white/20 flex items-center justify-center text-[12px] font-black text-slate-400 hover:text-blue-400 transition-all shadow-xl">?</button>
                           <span className="px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-[10px] font-black border border-blue-500/20 uppercase tracking-widest">{inventory.length} POSITIONS</span>
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 divide-y md:divide-y-0 md:gap-px bg-white/5">
                        {inventory.map((i, idx) => (
                            <div key={idx} className="bg-[#05070a] p-8 space-y-6 hover:bg-white/[0.02] transition-colors group">
                                <div className="flex justify-between items-start"><div className="flex flex-col"><span className="text-3xl font-black text-white italic font-outfit tracking-tighter uppercase leading-none font-outfit font-black">{i.ticker}</span><span className="text-[9px] text-slate-600 font-bold uppercase tracking-[0.2em] mt-2 font-outfit">{i.asset_class} SECURITY</span></div><span className={`px-3 py-1 rounded-lg text-xs font-black font-mono border ${getStatusColor(i.win_loss, 'text')} ${getStatusColor(i.win_loss, 'bg')} ${getStatusColor(i.win_loss, 'border')}`}>{i.win_loss}</span></div>
                                <div className="grid grid-cols-2 gap-6 py-5 border-y border-white/5"><div className="space-y-1"><span className="text-[8px] text-slate-500 uppercase font-black tracking-widest font-outfit">Volume</span><span className="text-base font-bold text-white font-mono">{i.quantity}</span></div><div className="space-y-1 text-right font-outfit"><span className="text-[8px] text-slate-500 uppercase font-black tracking-widest">Mark_Price</span><span className="text-base font-bold text-white font-mono">${i.current?.toLocaleString()}</span></div></div>
                                <div className="flex justify-between items-center">
                                    <div className="flex gap-5 font-mono">
                                        {[{l: '1D', v: i.est_1d}, {l: '1W', v: i.est_7d}].map(e => (
                                            <div key={e.l} className="flex flex-col">
                                                <span className="text-[8px] text-slate-600 uppercase font-black mb-1 leading-none font-outfit">{e.l}</span>
                                                <span className={`text-[13px] font-black leading-none ${e.v?.includes('+') ? 'text-blue-400' : 'text-orange-400'}`}>{e.v || '---'}</span>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="flex gap-2 font-outfit">
                                        <button onClick={() => triggerSellAnalysis(i.ticker)} className="px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest bg-blue-600 text-white hover:bg-blue-500 transition-all font-outfit shadow-lg leading-none">
                                            {analysisStatus[i.ticker] || 'Sell Analysis'}
                                        </button>
                                        <button className="px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest border border-rose-500/20 text-rose-500/70 hover:bg-rose-500 hover:text-white transition-all font-outfit leading-none">Liquidate</button>
                                    </div>
                                </div>
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
                            <div className="flex justify-between items-start mb-10 font-outfit"><span className="text-[11px] font-black text-blue-500 uppercase tracking-[0.5em] font-outfit uppercase">Neural Consensus Outlook</span><button onClick={() => setIsModalOpen(true)} className="h-10 w-10 rounded-full glass border-white/20 flex items-center justify-center text-lg font-black text-slate-400 hover:text-blue-400 transition-all shadow-xl">?</button></div>
                            <div className="space-y-6 md:space-y-8 relative z-10 font-outfit">
                                <span className="text-3xl md:text-5xl font-black text-white italic tracking-tighter drop-shadow-4xl font-outfit leading-none uppercase">{outlook.market_mood || 'Analyzing...'}</span>
                                <div className="space-y-3 md:space-y-4">
                                   <div className="flex items-center gap-2 md:gap-3"><span className="h-px w-6 md:w-10 bg-blue-500/30" /><span className="text-[8px] md:text-[10px] font-black text-slate-500 uppercase tracking-widest font-outfit italic leading-none">Institutional Grade Conclusion</span></div>
                                   <p className="text-lg md:text-2xl text-slate-100 italic leading-snug font-outfit tracking-tight border-l-4 border-blue-600/20 pl-6 md:pl-10 text-left font-medium max-w-4xl">"{outlook.swarm_conclusion || 'Assembling cross-market intelligence...'}"</p>
                                </div>
                            </div>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            {['US', 'HK', 'EU', 'CN', 'SG'].map(idx => {
                                const data = macro.indices?.[idx];
                                return data ? <NarrativeCard key={idx} title={data.label} data={data} /> : null;
                            })}
                        </div>
                    </div>
                    <div className="lg:col-span-4 space-y-10">
                        <div className="glass rounded-[3rem] p-10 border-white/10 shadow-2xl space-y-8 sticky top-[24rem]">
                            <span className="text-[11px] font-black text-amber-500 uppercase tracking-[0.3em] font-outfit border-b border-white/5 pb-6 block uppercase font-black">Top Alpha Picks</span>
                            <div className="space-y-4 font-outfit">
                                {signals.slice(0, 6).map((s, idx) => (<AlphaPill key={idx} item={s} />))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        )}

        {activeTab === 'signals' && (
            <div className="space-y-20 text-left animate-in fade-in slide-in-from-bottom-6 duration-700">
                {['US', 'HK', 'CN'].map(marketType => (
                    <div key={marketType} className="space-y-12">
                        <div className="flex items-baseline gap-6 border-b border-white/5 pb-8 font-outfit"><h2 className="text-2xl md:text-3xl font-black text-white italic tracking-tightest uppercase font-outfit leading-none font-outfit uppercase">{marketType} Alpha</h2><button onClick={() => setIsModalOpen(true)} className="h-10 w-10 rounded-full glass border-white/20 flex items-center justify-center text-lg font-black text-slate-400 hover:text-blue-400 transition-all shadow-xl">?</button><span className="h-px flex-1 bg-white/5" /><span className="text-[11px] font-black text-slate-600 uppercase tracking-[0.5em] font-outfit uppercase">Predictive signals</span></div>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 font-outfit">
                            {['Short Term', 'Long Term'].map(horizon => (
                                <div key={horizon} className="glass rounded-[3rem] overflow-hidden flex flex-col shadow-2xl border-white/10 glass-hover">
                                    <div className="p-10 border-b border-white/5 bg-white/[0.02] flex justify-between items-center"><h3 className="text-xl md:text-2xl font-black text-white uppercase italic tracking-tighter font-outfit leading-none uppercase">{horizon} Strat</h3><span className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase font-outfit border ${horizon === 'Short Term' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'}`}>{horizon === 'Short Term' ? 'MOMENTUM' : 'GROWTH'}</span></div>
                                    <div className="divide-y divide-white/5 flex-1">{signals.filter(s => s.market === marketType && s.horizon === horizon).map((s, idx) => (<HighDensityCard key={idx} item={s} type="STOCK" />))}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        )}

        {activeTab === 'fx' && (
            <div className="space-y-12 text-left animate-in fade-in slide-in-from-bottom-6 duration-700">
                <div className="flex items-baseline gap-6 pb-8 border-b border-white/5 font-outfit uppercase"><h2 className="text-2xl md:text-3xl font-black text-white italic font-outfit leading-none uppercase tracking-tightest">Forex Liquidity</h2><button onClick={() => setIsModalOpen(true)} className="h-10 w-10 rounded-full glass border-white/20 flex items-center justify-center text-lg font-black text-slate-400 hover:text-blue-400 transition-all shadow-xl">?</button><span className="h-px flex-1 bg-white/5" /></div>
                <div className="glass rounded-[3rem] overflow-hidden shadow-2xl border-white/10 divide-y divide-white/5">
                    {fx.map((item, idx) => (
                        <div key={idx} className="flex flex-col">
                            <HighDensityCard item={item} type="FX" />
                            {item.drivers && (
                                <div className="bg-blue-600/[0.02] border-t border-white/5 p-8 grid grid-cols-1 md:grid-cols-3 gap-6">
                                    {Object.entries(item.drivers).map(([key, strat]) => (
                                        <div key={key} className="glass p-6 rounded-[2rem] border-white/5 hover:border-blue-500/20 transition-all group font-outfit uppercase">
                                            <div className="flex justify-between items-start mb-4"><div><h5 className="text-lg font-black text-white italic font-outfit uppercase font-black">{strat.name}</h5><span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">{strat.margin} Margin</span></div><div className="text-right font-mono"><span className="text-[8px] font-black text-slate-500 uppercase block mb-1">Win_Rate</span><span className="text-xl font-bold text-white font-mono">{(strat.results.win_rate * 100).toFixed(0)}%</span></div></div>
                                            <p className="text-xs text-slate-400 italic mb-4">"{strat.logic}"</p>
                                            <div className="flex justify-between items-center pt-4 border-t border-white/5 font-outfit"><span className="text-[9px] font-black text-slate-600 uppercase tracking-widest font-outfit">Est_Alpha</span><span className={`text-base font-black font-mono ${strat.results.alpha.includes('+') ? 'text-emerald-400' : 'text-rose-400'}`}>{strat.results.alpha}</span></div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        )}

        {activeTab === 'crypto' && (
            <div className="space-y-12 text-left animate-in fade-in slide-in-from-bottom-6 duration-700">
                <div className="flex items-baseline gap-6 pb-8 border-b border-white/5 font-outfit uppercase"><h2 className="text-2xl md:text-3xl font-black text-white italic font-outfit leading-none uppercase tracking-tightest font-outfit">Digital Assets</h2><span className="h-px flex-1 bg-white/5" /></div>
                <div className="glass rounded-[3rem] overflow-hidden shadow-2xl border-white/10 divide-y divide-white/5">
                    {crypto.map((item, idx) => <HighDensityCard key={idx} item={item} type="CRYPTO" />)}
                </div>
            </div>
        )}

        {activeTab === 'commodities' && (
            <div className="space-y-12 text-left animate-in fade-in slide-in-from-bottom-6 duration-700">
                <div className="flex items-baseline gap-6 pb-8 border-b border-white/5 font-outfit uppercase"><h2 className="text-2xl md:text-3xl font-black text-white italic font-outfit leading-none uppercase tracking-tightest font-outfit">Hard Assets</h2><span className="h-px flex-1 bg-white/5" /></div>
                <div className="glass rounded-[3rem] overflow-hidden shadow-2xl border-white/10 divide-y divide-white/5">
                    {commodities.map((item, idx) => <HighDensityCard key={idx} item={item} type="COMMODITY" />)}
                </div>
            </div>
        )}

        {activeTab === 'hft' && (
            <div className="space-y-16 animate-in fade-in slide-in-from-bottom-6 duration-700 text-left">
                <div className="flex flex-col md:flex-row md:items-baseline justify-between gap-8 border-b border-white/5 pb-8 font-outfit uppercase">
                   <div className="flex items-baseline gap-6 font-outfit">
                      <h2 className="text-2xl md:text-3xl font-black text-white italic font-outfit leading-none uppercase tracking-tightest font-outfit">Velocity Control</h2>
                      <button onClick={() => setIsModalOpen(true)} className="h-10 w-10 rounded-full glass border-white/20 flex items-center justify-center text-lg font-black text-slate-400 hover:text-blue-400 transition-all shadow-xl">?</button>
                   </div>
                   <div className="flex items-center gap-4 font-outfit uppercase">
                      {ibAccount && ibAccount.length > 0 ? (
                          <select 
                            value={selectedAccountId} 
                            onChange={(e) => {
                                setSelectedAccountId(e.target.value);
                                fetchIbData();
                            }}
                            className="bg-black/60 border border-blue-500/40 rounded-xl px-4 py-2 text-[10px] font-black text-white outline-none focus:border-blue-500 appearance-none pr-10 uppercase font-outfit shadow-[0_0_15px_rgba(59,130,246,0.1)]"
                          >
                            {ibAccount.map(acc => (
                                <option key={acc.id} value={acc.id}>{acc.id} ({acc.accountTitle || 'Active'})</option>
                            ))}
                          </select>
                      ) : (
                          ibStatus.web === 'Authenticated' && (
                            <button onClick={fetchIbData} className="px-4 py-2 rounded-xl bg-amber-500/20 text-amber-400 text-[9px] font-black uppercase border border-amber-500/20 animate-pulse font-outfit leading-none">
                                Link_Account_Data
                            </button>
                          )
                      )}
                      <div className="flex flex-col text-right font-outfit">
                         <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">IBKR_LINK_STATUS</span>
                         <span className={`text-xs font-bold font-mono ${ibStatus.web === 'Authenticated' ? 'text-emerald-400' : 'text-rose-400'}`}>{ibStatus.web}</span>
                      </div>
                      {ibStatus.web !== 'Authenticated' ? (
                          <div className="flex gap-2">
                            <button 
                                onClick={() => {
                                    // Open popup for easier login flow
                                    const width = 600;
                                    const height = 900;
                                    const left = (window.screen.width - width) / 2;
                                    const top = (window.screen.height - height) / 2;
                                    window.open(
                                        '/sso/Login?forwardTo=22', 
                                        'ib_login_popup', 
                                        `width=${width},height=${height},top=${top},left=${left},resizable=yes,scrollbars=yes,status=yes`
                                    );
                                }}
                                className="px-6 py-2 rounded-xl bg-blue-600 text-white text-[10px] font-black uppercase border border-blue-500 shadow-lg glow-blue font-outfit leading-none font-black"
                            >
                                Authorize_Popup
                            </button>
                            <button onClick={fetchIbData} className="px-4 py-2 rounded-xl bg-white/10 text-slate-400 text-[10px] font-black uppercase border border-white/10 hover:bg-white/20 transition-all font-outfit leading-none">
                                Sync_Session
                            </button>
                          </div>
                      ) : (
                          <div className="flex gap-2">
                             <button onClick={fetchIbData} className="px-6 py-2 rounded-xl bg-emerald-500/20 text-emerald-400 text-[10px] font-black uppercase border border-emerald-500/20 transition-all font-outfit leading-none font-black">Refresh_Session</button>
                             <button onClick={connectIb} className="px-6 py-2 rounded-xl bg-white/5 hover:bg-blue-600 text-slate-300 hover:text-white text-[10px] font-black uppercase border border-white/10 transition-all font-outfit shadow-lg leading-none font-black">Init_Socket</button>
                          </div>
                      )}
                   </div>
                </div>

                {/* QUANT STRATEGY UNIT */}
                <div className="space-y-10">
                    <div className="flex justify-between items-end">
                        <div className="space-y-2">
                            <span className="text-[11px] font-black text-blue-500 uppercase tracking-[0.3em]">Institutional Quant Intelligence</span>
                            <h3 className="text-3xl font-black text-white italic tracking-tighter uppercase font-outfit">Active Quant Models</h3>
                        </div>
                    </div>
                    
                    {/* Iteration 5: Matrix View for Performance Comparison */}
                    <StrategyMatrix 
                        matrix={quantMatrix} 
                        onDeploy={initiateDeploy} 
                        onToggle={toggleStrategy}
                        onDelete={deleteStrategy}
                    />
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                        {quantStrategies.length > 0 ? quantStrategies.map((strat, i) => (
                            <QuantStrategyCard key={i} strat={strat} onToggle={toggleStrategy} onDelete={deleteStrategy} />
                        )) : (
                            <div className="lg:col-span-4 glass p-16 rounded-[4rem] flex flex-col items-center justify-center border-dashed border-white/10 space-y-6">
                                <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center"><span className="text-3xl opacity-20">🤖</span></div>
                                <p className="text-slate-500 font-bold uppercase tracking-[0.3em] text-sm">Waiting for Model Deployment</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* QUANT PERFORMANCE SUMMARY */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="glass p-6 rounded-[2rem] border-white/10 space-y-2">
                        <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">Inventory Value</span>
                        <div className="text-2xl font-black text-white font-mono">
                            {ibPositions.length > 0 ? 
                                `$${ibPositions.reduce((acc, pos) => acc + (pos.mktValue || 0), 0).toLocaleString()}` : 
                                `$${velocitySummary.inventory_value?.toLocaleString() || '0.00'}`}
                        </div>
                        <div className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">
                            {ibPositions.length || velocitySummary.active_positions} Active Positions
                        </div>
                    </div>
                    <div className="glass p-6 rounded-[2rem] border-white/10 space-y-2">
                        <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">Today's P&L</span>
                        <div className={`text-2xl font-black font-mono ${velocitySummary.today_pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                            {velocitySummary.today_pnl >= 0 ? '+' : ''}${velocitySummary.today_pnl?.toLocaleString() || '0.00'}
                        </div>
                        <div className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">{velocitySummary.executions_today} Executions Today</div>
                    </div>
                    {activeAccount && (
                        <>
                            <div className="glass p-6 rounded-[2rem] border-white/10 space-y-2">
                                <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">IBKR Net Liq</span>
                                <div className="text-2xl font-black text-emerald-400 font-mono">
                                    ${activeAccount.netLiquidation?.toLocaleString(undefined, {minimumFractionDigits: 2}) || '---'}
                                </div>
                                <div className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">
                                    Buying Power: ${activeAccount.buyingPower?.toLocaleString(undefined, {minimumFractionDigits: 2})}
                                </div>
                            </div>
                            <div className="glass p-6 rounded-[2rem] border-white/10 space-y-2">
                                <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">Real-Time P&L</span>
                                <div className={`text-2xl font-black font-mono ${ibPositions.reduce((acc, p) => acc + (p.unrealizedPnl || 0), 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                    {ibPositions.reduce((acc, p) => acc + (p.unrealizedPnl || 0), 0) >= 0 ? '+' : ''}
                                    ${ibPositions.reduce((acc, p) => acc + (p.unrealizedPnl || 0), 0).toLocaleString(undefined, {minimumFractionDigits: 2})}
                                </div>
                                <div className="text-[10px] text-slate-400 font-bold uppercase tracking-tighter">Unrealized Across Cluster</div>
                            </div>
                        </>
                    )}
                </div>

                {/* REAL-TIME LIQUIDITY MATRIX */}
                <div className="space-y-6">
                   <div className="flex justify-between items-center">
                      <h3 className="text-xl font-black text-white uppercase tracking-widest font-outfit opacity-60 italic">Liquidity Velocity Matrix</h3>
                      <span className="px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-[9px] font-black border border-blue-500/20 tracking-widest">REAL-TIME FEEDS</span>
                   </div>
                   <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
                       {hft.map((h, i) => (
                           <div key={i} className="glass rounded-3xl p-6 border-white/10 shadow-2xl flex flex-col gap-6 group hover:border-blue-500/30 transition-all relative overflow-hidden font-outfit uppercase">
                               <div className="absolute top-0 right-0 p-4 opacity-[0.03] text-4xl font-black italic select-none font-outfit uppercase">{h.asset_class}</div>
                               <div className="space-y-1">
                                   <span className="text-2xl font-black text-white italic tracking-tighter group-hover:text-blue-400 transition-colors uppercase leading-none font-outfit">{h.ticker}</span>
                                   <div className={`text-[9px] font-black uppercase tracking-widest flex items-center gap-2 ${h.fusion_signal?.includes('BUY') ? 'text-emerald-400' : 'text-rose-400'}`}>
                                       {h.fusion_signal || 'NEUTRAL'}
                                   </div>
                               </div>
                               
                               <div className="grid grid-cols-4 gap-1 border-y border-white/5 py-3">
                                   {['1m', '5m', '30m', '1h'].map(t => (
                                       <div key={t} className="flex flex-col items-center">
                                           <span className="text-[7px] text-slate-600 uppercase font-black">{t}</span>
                                           <span className={`text-[10px] font-bold font-mono ${h.velocity_estimates?.[t]?.includes('+') ? 'text-blue-400' : 'text-orange-400'}`}>
                                               {h.velocity_estimates?.[t] || '--'}
                                           </span>
                                       </div>
                                   ))}
                               </div>

                               <div className="flex justify-between items-center text-[10px] font-black font-outfit">
                                   <span className="text-slate-500 uppercase">Pressure</span>
                                   <span className="text-white font-mono">{(h.pressure_value || 0).toFixed(2)}</span>
                               </div>
                           </div>
                       ))}
                   </div>
                </div>

                <div className="grid lg:grid-cols-12 gap-10">
                    {/* EXECUTION LOG */}
                    <div className="lg:col-span-8 space-y-6">
                        <div className="flex justify-between items-center">
                            <h3 className="text-xl font-black text-white uppercase tracking-widest font-outfit opacity-60 italic">Execution Log</h3>
                            <button className="px-4 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 text-[10px] font-black uppercase border border-white/10 transition-all font-outfit">Export_Audit</button>
                        </div>
                        <div className="glass rounded-[2.5rem] overflow-hidden shadow-2xl border-white/10">
                            <div className="overflow-x-auto">
                                <table className="w-full text-left font-outfit uppercase">
                                    <thead className="bg-white/[0.03] text-slate-500 text-[10px] font-black tracking-[0.2em]">
                                        <tr>
                                            <th className="px-8 py-5">Time</th>
                                            <th className="px-8 py-5">Ticker</th>
                                            <th className="px-8 py-5">Side</th>
                                            <th className="px-8 py-5">Price</th>
                                            <th className="px-8 py-5">Qty</th>
                                            <th className="px-8 py-5">Value</th>
                                            <th className="px-8 py-5 text-right">P&L</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/5">
                                        {velocityTrades.length > 0 ? velocityTrades.map((t, i) => (
                                            <tr key={i} className="hover:bg-white/[0.02] transition-colors group">
                                                <td className="px-8 py-5 text-[10px] font-bold text-slate-500 font-mono">{new Date(t.timestamp).toLocaleTimeString()}</td>
                                                <td className="px-8 py-5 text-sm font-black text-white italic">{t.ticker}</td>
                                                <td className="px-8 py-5">
                                                    <span className={`px-2 py-0.5 rounded text-[9px] font-black ${t.side === 'BUY' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                                                        {t.side}
                                                    </span>
                                                </td>
                                                <td className="px-8 py-5 text-sm font-bold text-slate-300 font-mono">${t.price?.toFixed(2)}</td>
                                                <td className="px-8 py-5 text-sm font-bold text-slate-300 font-mono">{t.quantity}</td>
                                                <td className="px-8 py-5 text-sm font-bold text-slate-300 font-mono">${t.total_value?.toLocaleString()}</td>
                                                <td className={`px-8 py-5 text-sm font-black font-mono text-right ${t.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                                    {t.pnl !== null ? `${t.pnl >= 0 ? '+' : ''}${t.pnl?.toLocaleString()}` : '---'}
                                                </td>
                                            </tr>
                                        )) : (
                                            <tr>
                                                <td colSpan="7" className="px-8 py-12 text-center text-slate-600 font-bold italic uppercase tracking-widest">No executions recorded in current cycle</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    {/* ACTIVE POSITIONS QUICK-VIEW */}
                    <div className="lg:col-span-4 space-y-6">
                        <h3 className="text-xl font-black text-white uppercase tracking-widest font-outfit opacity-60 italic">Live Positions</h3>
                        <div className="space-y-4">
                            {ibPositions.map((pos, i) => (
                                <div key={i} className="glass p-6 rounded-[2rem] border-white/10 hover:border-blue-500/30 transition-all group relative overflow-hidden">
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="flex flex-col">
                                            <span className="text-xl font-black text-white italic font-outfit group-hover:text-blue-400 transition-colors">{pos.contractDesc || pos.symbol}</span>
                                            <span className="text-[9px] text-slate-500 font-bold uppercase tracking-widest">{pos.position} Units @ ${pos.avgPrice?.toFixed(2)}</span>
                                        </div>
                                        <div className={`text-right ${pos.unrealizedPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                            <div className="text-lg font-black font-mono">
                                                {pos.unrealizedPnl >= 0 ? '+' : ''}{pos.unrealizedPnl?.toLocaleString()}
                                            </div>
                                            <span className="text-[8px] font-black uppercase">Unrealized P&L</span>
                                        </div>
                                    </div>
                                    <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                                        <div className={`h-full ${pos.unrealizedPnl >= 0 ? 'bg-emerald-500' : 'bg-rose-500'}`} style={{ width: '40%' }} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
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
                    <div className="flex items-baseline gap-6 font-outfit uppercase">
                        <h2 className="text-2xl md:text-3xl font-black text-white italic tracking-tightest uppercase font-outfit leading-none font-outfit uppercase">System Node</h2>
                        <span className="px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-[10px] font-black border border-blue-500/20 tracking-widest">v2.9_STABLE</span>
                    </div>
                    {(Object.keys(pendingConfigs).length > 0 || Object.keys(pendingSchedules).length > 0) && (
                        <button 
                            onClick={applySystemChanges}
                            disabled={isApplying}
                            className="px-10 py-4 rounded-2xl bg-blue-600 text-white text-xs font-black uppercase tracking-[0.2em] shadow-2xl glow-blue hover:bg-blue-500 transition-all active:scale-95 disabled:opacity-50"
                        >
                            {isApplying ? 'Applying...' : 'Apply_All_Changes'}
                        </button>
                    )}
                </div>
                
                <div className="space-y-10 font-outfit uppercase">
                    <div className="flex justify-between items-end">
                        <h3 className="text-xl md:text-2xl font-black text-white uppercase italic tracking-tighter font-outfit font-black">Target Win Rates</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                        {strategyConfigs.map(cfg => (
                            <div key={cfg.asset_class} className={`glass p-8 rounded-[2.5rem] border-white/10 space-y-6 font-outfit uppercase transition-all ${pendingConfigs[cfg.asset_class] ? 'border-blue-500/40 bg-blue-500/[0.02]' : ''}`}>
                                <div className="flex justify-between items-center font-outfit font-black">
                                    <span className="text-xl font-black text-white italic font-outfit">{cfg.asset_class}</span>
                                    {pendingConfigs[cfg.asset_class] && <span className="text-[8px] text-blue-400 font-black animate-pulse">PENDING</span>}
                                </div>
                                <div className="space-y-2 font-outfit">
                                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest font-outfit">Success Threshold</span>
                                    <div className="flex items-center gap-4 font-outfit">
                                        <input type="range" min="0.3" max="0.9" step="0.05" value={cfg.win_rate_target} onChange={e => updateConfig(cfg.asset_class, e.target.value)} className="flex-1 accent-blue-500 cursor-pointer" />
                                        <span className="text-lg font-bold text-white font-mono font-mono font-bold">{(cfg.win_rate_target * 100).toFixed(0)}%</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
                    {[
                        { id: 'indices', name: 'Macro_Sync', desc: 'Global Indices & Market Mood vectors.' },
                        { id: 'stocks', name: 'Alpha_Universe', desc: 'Predictive Neural Models for Equity.' },
                        { id: 'fx', name: 'Liquidity_Layer', desc: 'FX Liquidity & Interest Differentials.' },
                        { id: 'commodities', name: 'Hard_Assets', desc: 'Energy & Metals sync.' },
                        { id: 'crypto', name: 'Digital_Compute', desc: 'On-chain velocity audits.' },
                        { id: 'hft', name: 'Velocity_HFT', desc: 'High-Frequency Pressure Values.' }
                    ].map(comp => {
                        const schedule = syncSchedules.find(s => s.component === comp.id);
                        return (
                            <div key={comp.id} className={`glass rounded-[3rem] p-10 border-white/10 shadow-2xl flex flex-col gap-10 group hover:border-blue-500/40 transition-all font-outfit uppercase ${pendingSchedules[comp.id] ? 'border-blue-500/40 bg-blue-500/[0.02]' : ''}`}>
                                <div className="space-y-3 font-outfit font-black">
                                    <div className="flex justify-between items-start">
                                        <h3 className="text-2xl font-black text-white uppercase italic tracking-tighter font-outfit group-hover:text-blue-400 transition-colors leading-none font-outfit uppercase">{comp.name}</h3>
                                        {pendingSchedules[comp.id] && <span className="text-[8px] text-blue-400 font-black animate-pulse">PENDING</span>}
                                    </div>
                                    <p className="text-sm text-slate-500 leading-relaxed font-medium italic font-outfit lowercase">"{comp.desc}"</p>
                                </div>
                                <div className="space-y-3 pt-6 border-t border-white/5 font-outfit">
                                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest leading-none block font-outfit">Auto-Sync Frequency</span>
                                    <div className="flex gap-2 flex-wrap font-outfit">
                                        {['pause', '1min', '5min', '1hr', '1day'].map(freq => { 
                                            const isActive = schedule?.frequency === freq; 
                                            return (
                                                <button 
                                                    key={freq} 
                                                    onClick={() => updateSchedule(comp.id, freq)} 
                                                    className={`px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest border transition-all font-outfit ${isActive ? 'bg-blue-600 border-blue-600 text-white shadow-[0_0_10px_#3b82f6]' : 'border-white/5 text-slate-600 hover:text-slate-400 hover:border-white/10'}`}
                                                >
                                                    {freq}
                                                </button>
                                            ); 
                                        })}
                                    </div>
                                </div>
                                <div className="flex items-center justify-between mt-auto pt-10 border-t border-white/5 font-outfit">
                                    <div className="flex flex-col text-left font-outfit font-mono">
                                        <span className="text-[10px] font-black text-slate-600 uppercase font-outfit leading-none font-outfit">Node_Status</span>
                                        <span className={`text-base font-bold font-mono italic mt-1 ${maintenanceStatus[comp.id] === 'Live' ? 'text-emerald-400 text-glow' : 'text-blue-400'}`}>{maintenanceStatus[comp.id] || 'NODE_IDLE'}</span>
                                    </div>
                                    <button onClick={() => triggerMaintenance(comp.id)} className="px-8 py-3.5 rounded-2xl text-[10px] font-black uppercase tracking-widest bg-white text-black hover:bg-blue-600 hover:text-white transition-all font-outfit shadow-xl active:scale-95 leading-none font-black">Sync_Node</button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        )}

      </main>

      <footer className="fixed bottom-0 left-0 w-full h-12 glass border-t border-white/5 backdrop-blur-3xl z-[110] flex items-center px-12 justify-between">
         <div className="flex items-center gap-8">
            <div className="flex items-center gap-2.5 font-outfit">
               <div className="h-2 w-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_10px_#10b981]" />
               <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest font-outfit leading-none">Node_0.129.4 // OK</span>
            </div>
            <div className="h-4 w-px bg-white/5" />
            <div className="hidden md:flex items-center gap-2.5 font-outfit">
               <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest font-outfit leading-none">Neural Compute: 94.2 TFLOPS</span>
            </div>
         </div>
         <div className="hidden sm:flex items-center gap-6 text-[10px] font-black text-slate-600 uppercase tracking-widest font-outfit italic leading-none font-black">Institutional v2.9 ELITE // Global Portfolio Control</div>
      </footer>
    </div>
  );
};

export default App;
