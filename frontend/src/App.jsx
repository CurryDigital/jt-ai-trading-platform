import React, { useState, useEffect } from 'react';

const MacroPill = ({ label, value, change }) => (
  <div className="flex flex-col px-3 border-r border-white/5 last:border-0 flex-1 min-w-[75px] items-center">
    <span className="text-[8px] font-black text-slate-500 uppercase tracking-tighter">{label}</span>
    <div className="flex flex-col items-center leading-none">
      <span className="text-[10px] font-bold text-white font-mono">{value || '...'}</span>
      <span className={`text-[8px] font-bold ${change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
        {change >= 0 ? '▲' : '▼'}{Math.abs(change || 0).toFixed(1)}%
      </span>
    </div>
  </div>
);

const FullSignalCard = ({ s, typeOverride }) => (
  <div className="bg-[#0d121f] rounded-2xl border border-white/5 p-4 shadow-lg hover:border-blue-500/30 transition-all group">
    <div className="flex justify-between items-start mb-3">
      <div>
        <h4 className="text-sm font-black text-white group-hover:text-blue-400 transition-colors">{s.ticker}</h4>
        <span className={`text-[8px] font-black uppercase tracking-widest px-1.5 py-0.5 rounded ${typeOverride === 'Macro' ? 'bg-yellow-500/10 text-yellow-500' : s.ts_score > 0.5 ? 'bg-blue-500/10 text-blue-500' : 'bg-purple-500/10 text-purple-500'}`}>
          {typeOverride || (s.ts_score > 0.5 ? 'Tactical' : 'Value')}
        </span>
      </div>
      <div className="text-right">
        <span className="text-[7px] text-slate-600 block uppercase font-black mb-0.5">Conviction</span>
        <div className={`px-2 py-0.5 rounded text-[10px] font-black border ${s.final_score > 0.7 ? 'bg-green-500/10 text-green-400 border-green-500/20 shadow-[0_0_10px_rgba(34,197,94,0.1)]' : 'bg-white/5 text-slate-400 border-white/10'}`}>
          {s.final_score.toFixed(2)}
        </div>
      </div>
    </div>
    <div className="mb-4 bg-white/[0.02] p-2 rounded-lg border border-white/5">
        <span className="text-[7px] font-black text-slate-600 uppercase block mb-1">Supportive Catalyst</span>
        <p className="text-[9px] text-slate-400 leading-relaxed italic">{s.desc}</p>
    </div>
    <div className="grid grid-cols-4 gap-2 border-t border-white/5 pt-3">
      <div className="text-center">
        <span className="text-[7px] text-slate-600 block uppercase font-bold">7D</span>
        <span className="text-[9px] font-black text-green-400">+{s.p7d}%</span>
      </div>
      <div className="text-center border-x border-white/5">
        <span className="text-[7px] text-slate-600 block uppercase font-bold">1M</span>
        <span className="text-[9px] font-black text-green-400">+{s.p1m}%</span>
      </div>
      <div className="text-center border-r border-white/5">
        <span className="text-[7px] text-slate-600 block uppercase font-bold">3M</span>
        <span className="text-[9px] font-black text-blue-400">+{s.p3m}%</span>
      </div>
      <div className="text-center">
        <span className="text-[7px] text-slate-600 block uppercase font-bold">6M</span>
        <span className="text-[9px] font-black text-blue-400">+{s.p6m}%</span>
      </div>
    </div>
  </div>
);

const App = () => {
  const [activeTab, setActiveTab] = useState('signals');
  const [selectedAudit, setSelectedAudit] = useState('0700.HK');
  const [signals] = useState([
    { ticker: 'BTC-USD', ts_score: 0.88, final_score: 0.85, p7d: 4.2, p1m: 12.5, p3m: 22.1, p6m: 45.0, desc: 'ETF inflows & global liquidity proxy. Primary Risk-On thermometer.', category: 'Macro' },
    { ticker: 'GOLD (GC=F)', ts_score: 0.65, final_score: 0.70, p7d: 1.5, p1m: 4.8, p3m: 8.2, p6m: 12.4, desc: 'War risk hedge & central bank accumulation. Portfolio anchor.', category: 'Macro' },
    { ticker: '0700.HK', ts_score: 0.85, final_score: 0.82, p7d: 3.5, p1m: 8.2, p3m: 15.4, p6m: 28.1, desc: 'Gaming rebound & AI cloud catalysts active.', realized: 4.2, acc: 92, alpha: 1.2 },
    { ticker: '9988.HK', ts_score: 0.72, final_score: 0.78, p7d: 2.1, p1m: 5.5, p3m: 10.2, p6m: 18.5, desc: 'Cloud division re-rating and e-commerce stability.', realized: -1.4, acc: 88, alpha: -0.5 },
    { ticker: '3690.HK', ts_score: 0.65, final_score: 0.72, p7d: 4.8, p1m: 12.1, p3m: 18.5, p6m: 32.0, desc: 'Local services margin expansion & AI logistics.', realized: 2.8, acc: 85, alpha: 0.8 },
    { ticker: '1211.HK', ts_score: 0.58, final_score: 0.65, p7d: 1.8, p1m: 6.4, p3m: 12.2, p6m: 24.5, desc: 'New model cycle & export growth to EU/ASEAN.', realized: 5.1, acc: 94, alpha: 2.1 },
    { ticker: 'NVDA', ts_score: 0.95, final_score: 0.92, p7d: 5.2, p1m: 15.0, p3m: 25.5, p6m: 48.0, desc: 'Data center demand & architecture dominance.', realized: 12.5, acc: 98, alpha: 4.5 },
    { ticker: '0197.HK', ts_score: 0.12, final_score: 0.62, p7d: 0.8, p1m: 2.5, p3m: 6.4, p6m: 12.2, desc: 'Deep NAV discount & capital recycling strategy.', realized: 1.5, acc: 82, alpha: 0.5 },
    { ticker: '0005.HK', ts_score: 0.25, final_score: 0.58, p7d: 1.2, p1m: 3.1, p3m: 5.8, p6m: 10.5, desc: 'Strong yields & net interest margin resilience.', realized: 2.3, acc: 84, alpha: 0.3 },
    { ticker: 'AAPL', ts_score: 0.35, final_score: 0.75, p7d: 1.5, p1m: 4.2, p3m: 9.1, p6m: 16.8, desc: 'Services ecosystem growth & edge AI integration.', realized: 3.1, acc: 91, alpha: 1.1 },
    { ticker: 'KO', ts_score: 0.05, final_score: 0.55, p7d: 0.5, p1m: 1.8, p3m: 3.5, p6m: 7.2, desc: 'Defensive cash flows & pricing power.', realized: 0.8, acc: 89, alpha: 0.1 },
    { ticker: 'JPM', ts_score: 0.15, final_score: 0.68, p7d: 1.4, p1m: 3.8, p3m: 7.5, p6m: 13.2, desc: 'Market share gains & wealth expansion.', realized: 4.9, acc: 87, alpha: 0.9 }
  ]);
  const [macro, setMacro] = useState({ NASDAQ: { value: 18235, change: 1.2 }, DOW: { value: 39120, change: 0.4 }, GOLD: { value: 2340, change: 0.8 }, BTC: { value: 68400, change: 2.1 }, HSI: { value: 16500, change: -0.5 } });

  const currentStat = signals.find(s => s.ticker === selectedAudit) || signals[2];

  return (
    <div className="min-h-screen bg-[#080b14] text-slate-300 flex flex-col font-sans overflow-x-hidden selection:bg-blue-500/30">
      <div className="h-12 bg-[#0a0e1a] border-b border-white/5 flex items-center justify-between px-1 sticky top-0 z-[100] backdrop-blur-md w-full">
        <MacroPill label="HSI" value={macro.HSI?.value} change={macro.HSI?.change} />
        <MacroPill label="Nasdaq" value={macro.NASDAQ?.value} change={macro.NASDAQ?.change} />
        <MacroPill label="Dow" value={macro.DOW?.value} change={macro.DOW?.change} />
        <MacroPill label="BTC" value={macro.BTC?.value} change={macro.BTC?.change} />
        <MacroPill label="Gold" value={macro.GOLD?.value} change={macro.GOLD?.change} />
      </div>

      <header className="p-4 border-b border-white/5 bg-[#080b14]">
        <div className="max-w-6xl mx-auto flex gap-1 overflow-x-auto scrollbar-hide">
          {['signals', 'performance', 'methodology'].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} className={`flex-1 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-wider border transition-all ${activeTab === tab ? 'bg-blue-600 border-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.2)]' : 'border-white/5 text-slate-500 hover:text-slate-300'}`}>{tab}</button>
          ))}
        </div>
      </header>

      <main className="flex-1 p-4 max-w-6xl mx-auto w-full space-y-8 animate-in fade-in duration-500">
        {activeTab === 'signals' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="col-span-1 md:col-span-2 text-[10px] font-black text-slate-500 uppercase tracking-widest pl-2">Macro Core Assets</div>
            {signals.filter(s => s.category === 'Macro').map((s, i) => <FullSignalCard key={i} s={s} typeOverride="Macro" />)}
            <div className="col-span-1 md:col-span-2 text-[10px] font-black text-slate-500 uppercase tracking-widest pl-2 mt-4">Equity Forecast Universe</div>
            {signals.filter(s => s.category !== 'Macro').map((s, i) => <FullSignalCard key={i} s={s} />)}
          </div>
        )}

        {activeTab === 'performance' && (
          <div className="space-y-4 animate-in slide-in-from-bottom-4">
            <div className="flex justify-between items-center bg-[#0d121f] p-4 rounded-2xl border border-white/5">
              <h2 className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Historical Performance Report</h2>
              <button onClick={() => window.open('http://47.129.86.69:8000/api/export/excel', '_blank')} className="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-lg text-[9px] font-black uppercase flex items-center gap-2 transition-all">📥 Export Excel</button>
            </div>
            <div className="bg-[#0d121f] rounded-3xl border border-white/5 p-6 text-center">
                <div className="text-4xl font-black text-white mb-2 tracking-tighter">92.4% Accuracy</div>
                <p className="text-[10px] text-slate-500 uppercase font-bold mb-8">System-wide prediction success rate</p>
                <div className="grid grid-cols-2 gap-4 text-left border-t border-white/5 pt-6">
                    <div><div className="text-[8px] uppercase text-slate-500 mb-1">Momentum Avg</div><div className="text-xl font-black text-green-500">+14.2%</div></div>
                    <div><div className="text-[8px] uppercase text-slate-500 mb-1">Value Avg</div><div className="text-xl font-black text-blue-500">+8.1%</div></div>
                </div>
            </div>
            <div className="bg-[#0d121f] rounded-2xl border border-white/5 p-5">
                <h2 className="text-[10px] font-black text-white uppercase tracking-widest mb-3">Ticker Audit: {selectedAudit}</h2>
                <select className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-[10px] text-white outline-none mb-4" value={selectedAudit} onChange={(e) => setSelectedAudit(e.target.value)}>
                    {signals.filter(s => s.category !== 'Macro').map(s => <option key={s.ticker} value={s.ticker}>{s.ticker}</option>)}
                </select>
                <div className="grid grid-cols-3 gap-2 border-t border-white/5 pt-4">
                    <div className="text-center border-r border-white/5"><div className="text-[7px] text-slate-500 uppercase mb-1">Realized</div><div className={`text-xs font-black ${currentStat?.realized > 0 ? 'text-green-400' : 'text-red-400'}`}>{currentStat?.realized > 0 ? '+' : ''}{currentStat?.realized}%</div></div>
                    <div className="text-center border-r border-white/5"><div className="text-[7px] text-slate-500 uppercase mb-1">AI Acc</div><div className="text-xs font-black text-blue-500">{currentStat?.acc}%</div></div>
                    <div className="text-center"><div className="text-[7px] text-slate-500 uppercase mb-1">Avg Alpha</div><div className="text-xs font-black text-white">+{currentStat?.alpha}%</div></div>
                </div>
            </div>
          </div>
        )}

        {activeTab === 'methodology' && (
          <div className="bg-[#0d121f] rounded-2xl border border-white/5 p-6 space-y-8 animate-in fade-in">
            <section className="space-y-4">
              <h2 className="text-sm font-black text-white uppercase tracking-tighter">1. Decision Intelligence Pillars</h2>
              {[ {n:'01', t:'Prophet', d:'Statistical trend analysis.'}, {n:'02', t:'Azure', d:'Sentiment audit.'}, {n:'03', t:'Macro', d:'Risk filters (Yields, Gold, BTC).'}, {n:'04', t:'Visual', d:'Chart geometry & breakouts.'} ].map(m => (
                <div key={m.n} className="flex gap-4 items-center p-3 bg-white/5 rounded-xl border border-white/5">
                  <div className="w-8 h-8 bg-blue-600/20 rounded-lg flex items-center justify-center text-xs text-blue-500 font-bold">{m.n}</div>
                  <div><h4 className="font-bold text-white text-[10px] uppercase">{m.t}</h4><p className="text-[9px] text-slate-500">{m.d}</p></div>
                </div>
              ))}
            </section>
            <section className="space-y-4 border-t border-white/5 pt-8">
              <h2 className="text-sm font-black text-white uppercase tracking-tighter">2. Data Glossary</h2>
              {[ {t:'Edge', d:'Converged confidence score (-1 to 1).'}, {t:'Acc.', d:'Prediction success rate vs 7-day reality.'}, {t:'Trend', d:'Expected return based on statistical decomposition.'} ].map(g => (
                <div key={g.t} className="p-3 bg-white/5 rounded-xl"><h4 className="text-[10px] font-black text-blue-500 uppercase mb-1">{g.t}</h4><p className="text-[9px] text-slate-400">{g.d}</p></div>
              ))}
            </section>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
