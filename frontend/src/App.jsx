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

const App = () => {
  const [activeTab, setActiveTab] = useState('signals');
  const [signals, setSignals] = useState([]);
  const [fxVol, setFxVol] = useState([]);
  const [macro, setMacro] = useState({});
  const API_BASE = "http://47.129.86.69:8000/api";

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [mRes, sRes, fRes] = await Promise.all([
          fetch(`${API_BASE}/macro/pulse`),
          fetch(`${API_BASE}/signals/1`),
          fetch(`${API_BASE}/quants/volatility`)
        ]);
        if (mRes.ok) setMacro(await mRes.json());
        if (sRes.ok) setSignals(await sRes.json());
        if (fRes.ok) setFxVol(await fRes.json());
      } catch (e) {}
    };
    fetchAll();
    const interval = setInterval(fetchAll, 10000); // 10s update for Quants
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#080b14] text-slate-300 flex flex-col font-sans overflow-x-hidden">
      <div className="h-12 bg-[#0a0e1a] border-b border-white/5 flex items-center justify-between px-1 sticky top-0 z-[100] backdrop-blur-md w-full">
        <MacroPill label="HSI" value={macro.HSI?.value} change={macro.HSI?.change} />
        <MacroPill label="Nasdaq" value={macro.NASDAQ?.value} change={macro.NASDAQ?.change} />
        <MacroPill label="BTC" value={macro.BTC?.value} change={macro.BTC?.change} />
        <MacroPill label="Gold" value={macro.GOLD?.value} change={macro.GOLD?.change} />
      </div>

      <header className="p-4 border-b border-white/5 bg-[#080b14]">
        <div className="max-w-6xl mx-auto flex gap-1 overflow-x-auto scrollbar-hide">
          {['signals', 'quants', 'performance', 'methodology'].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} className={`flex-1 px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest border transition-all ${activeTab === tab ? 'bg-blue-600 border-blue-500 text-white' : 'border-white/5 text-slate-500'}`}>{tab}</button>
          ))}
        </div>
      </header>

      <main className="flex-1 p-4 max-w-6xl mx-auto w-full">
        {activeTab === 'quants' && (
          <div className="space-y-6 animate-in fade-in">
            <div className="bg-[#0d121f] rounded-3xl border border-white/5 overflow-hidden shadow-2xl">
              <div className="p-6 border-b border-white/5 flex justify-between items-center">
                <h3 className="font-bold text-white uppercase tracking-widest text-sm">FX Volatility Radar (1m)</h3>
                <span className="text-[10px] font-black text-green-500 animate-pulse">LIVE STREAMING</span>
              </div>
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-white/5 text-[10px] text-slate-500 uppercase font-black tracking-widest">
                    <th className="p-4 pl-8">Pair</th>
                    <th className="p-4">Price</th>
                    <th className="p-4 text-center">Z-Score</th>
                    <th className="p-4 text-right pr-8">Edge Signal</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 font-mono">
                  {fxVol.map((f, i) => (
                    <tr key={i} className="hover:bg-blue-600/5 transition-colors">
                      <td className="p-4 pl-8 font-black text-slate-200">{f.pair}</td>
                      <td className="p-4">{f.price}</td>
                      <td className={`p-4 text-center ${Math.abs(f.z_score) > 2 ? 'text-orange-400 font-black' : 'text-slate-500'}`}>{f.z_score}σ</td>
                      <td className="p-4 text-right pr-8">
                        <span className={`px-3 py-1 rounded-lg text-[9px] font-black uppercase ${f.signal.includes('BUY') ? 'bg-green-500/20 text-green-400' : f.signal.includes('SELL') ? 'bg-red-500/20 text-red-400' : 'bg-white/5 text-slate-500'}`}>
                          {f.signal}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="p-6 bg-blue-600/10 border border-blue-500/20 rounded-2xl">
                <h4 className="text-[10px] font-black text-blue-500 uppercase tracking-widest mb-2">Quant Logic: Mean-Reversion</h4>
                <p className="text-[10px] text-slate-400 leading-relaxed italic">Our Quant engine monitors price distance from the 20-period mean. Signals are generated when standard deviation (z-score) exceeds 2.0, targeting a volatility "snap-back" within 5-15 minutes.</p>
            </div>
          </div>
        )}

        {activeTab === 'signals' && (
           <div className="text-center p-20 text-slate-600 italic">Equity Signals Active. Switch to Quants for FX.</div>
        )}
      </main>
    </div>
  );
};

export default App;
