import React, { useState, useEffect } from 'react';

const Sparkline = ({ data, color = "#3b82f6" }) => {
  if (!data || data.length === 0) return <div className="h-[15px] w-[40px] bg-white/5 rounded animate-pulse" />;
  const width = 60;
  const height = 20;
  const points = data.map((val, i) => `${(i / (data.length - 1)) * width},${height - (val / 100) * height}`).join(' ');
  return (
    <svg width={width} height={height} className="overflow-visible drop-shadow-[0_0_5px_rgba(59,130,246,0.3)]">
      <polyline fill="none" stroke={color} strokeWidth="2" points={points} strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
};

const MacroPill = ({ label, value, change, est }) => {
  const isDrop = change < 0;
  const indexNames = { 'US': 'DJI', 'HK': 'HSI', 'EU': 'STOXX50', 'CN': 'SSE', 'SG': 'STI' };
  const displayName = indexNames[label] || label;
  return (
    <div className="flex flex-col px-4 border-r border-white/5 last:border-0 min-w-[160px] md:min-w-[190px] group hover:bg-white/[0.02] transition-colors py-3">
      <div className="flex justify-between items-baseline mb-0.5">
          <span className="text-[8px] md:text-[9px] font-black text-slate-500 uppercase tracking-widest">{displayName}</span>
      </div>
      <div className="flex items-center gap-2 mb-2">
          <span className="text-base md:text-xl font-black text-white font-mono tracking-tighter">{value?.toLocaleString() || '---'}</span>
          <span className={`text-[9px] md:text-[11px] font-bold font-mono ${isDrop ? 'text-red-500' : 'text-green-500'}`}>
              {isDrop ? '▼' : '▲'}{Math.abs(change || 0).toFixed(2)}%
          </span>
      </div>
      <div className="flex justify-between border-t border-white/5 pt-2">
          {['1D', '1W', '1M'].map(p => (
              <div key={p} className="flex flex-col">
                  <span className="text-[5px] md:text-[6px] font-black text-slate-600 uppercase">{p}</span>
                  <span className={`text-[8px] md:text-[9px] font-black font-mono tracking-tight ${est?.[p.toLowerCase()]?.includes('+') ? 'text-blue-400' : 'text-orange-400'}`}>
                      {est?.[p.toLowerCase()] || '---'}
                  </span>
              </div>
          ))}
      </div>
    </div>
  );
};

const HighDensityCard = ({ item, type = "STOCK" }) => (
    <div className="p-5 md:p-6 hover:bg-white/[0.02] transition-all group duration-500">
        <div className="flex flex-col md:flex-row md:justify-between items-start gap-4 md:gap-8">
            <div className="flex-1 space-y-4 md:space-y-6 w-full text-left">
                <div className="flex items-center justify-between w-full">
                    <div className="flex items-center gap-4 md:gap-5">
                        <div className="flex flex-col text-left">
                            <div className="flex items-baseline gap-2 text-left">
                                <span className="text-xl md:text-2xl font-black text-white italic tracking-tighter group-hover:text-blue-400 transition-colors leading-none">{item.ticker || item.pair}</span>
                                <span className="text-sm font-bold text-slate-400 font-mono">${item.price}</span>
                                <span className={`text-[10px] font-bold font-mono ${item.change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                    {item.change >= 0 ? '▲' : '▼'}{Math.abs(item.change)}%
                                </span>
                            </div>
                            <span className={`mt-1 text-[8px] font-black uppercase tracking-widest px-2 py-0.5 rounded-md inline-block w-fit ${item.total_conf > 0.82 ? 'bg-green-500/10 text-green-400' : (item.action === 'SELL' ? 'bg-red-500/10 text-red-400' : 'bg-orange-500/10 text-orange-400')}`}>
                                {item.action || (item.total_conf > 0.82 ? 'STRONG BUY' : 'ACCUMULATE')}
                            </span>
                        </div>
                        <Sparkline data={item.sparkline} color={item.total_conf > 0.7 ? "#4ade80" : "#3b82f6"} />
                    </div>
                    <div className="text-[7px] text-slate-600 uppercase font-black">Sync: {new Date(item.timestamp).toLocaleTimeString('en-HK')}</div>
                </div>

                {/* --- Crypto Native Matrix --- */}
                {type === 'CRYPTO' && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div className="bg-blue-500/5 border border-blue-500/10 p-2 rounded-xl">
                            <span className="text-[7px] text-slate-600 uppercase font-black block">MVRV Z-Score</span>
                            <span className="text-xs font-bold text-blue-400">{item.mvrv_z_score?.toFixed(2)}</span>
                        </div>
                        <div className="bg-blue-500/5 border border-blue-500/10 p-2 rounded-xl">
                            <span className="text-[7px] text-slate-600 uppercase font-black block">Fear & Greed</span>
                            <span className="text-xs font-bold text-white">{item.fear_greed_index}</span>
                        </div>
                        <div className="bg-blue-500/5 border border-blue-500/10 p-2 rounded-xl">
                            <span className="text-[7px] text-slate-600 uppercase font-black block">Funding</span>
                            <span className="text-xs font-bold text-green-400">{item.funding_rate?.toFixed(3)}%</span>
                        </div>
                        <div className="bg-blue-500/5 border border-blue-500/10 p-2 rounded-xl">
                            <span className="text-[7px] text-slate-600 uppercase font-black block">{item.ticker === 'BTC-USD' ? 'HashRate' : 'Gas Price'}</span>
                            <span className="text-xs font-bold text-slate-300">{item.ticker === 'BTC-USD' ? `${item.hash_rate_th_s?.toFixed(0)}T` : `${item.gas_price_gwei?.toFixed(1)}g`}</span>
                        </div>
                    </div>
                )}

                <div className="grid grid-cols-3 gap-2 md:gap-4 border-y border-white/5 py-3 md:py-4 font-mono text-left">
                    {[{ label: '1D', val: item.estimates?.['1d'] }, { label: '7D', val: item.estimates?.['7d'] }, { label: '1M', val: item.estimates?.['1m'] }].map(est => (
                        <div key={est.label} className="flex flex-col">
                            <span className="text-[6px] md:text-[7px] font-black text-slate-500 uppercase tracking-widest mb-0.5">{est.label}</span>
                            <span className={`text-xs md:text-sm font-black ${est.val?.includes('+') ? 'text-blue-400' : 'text-orange-400'}`}>{est.val || '---'}</span>
                        </div>
                    ))}
                </div>
                <p className="text-[11px] md:text-[12px] text-slate-300 italic font-medium leading-snug text-left line-clamp-3">"{item.logic || item.reasoning}"</p>
            </div>
            <div className="w-full md:w-[100px] pt-0 md:pt-1 flex md:flex-col justify-between md:justify-start items-center gap-2">
                <div className="text-center">
                    <span className="text-[7px] md:text-[8px] font-black text-slate-500 uppercase tracking-widest block mb-0.5">Score</span>
                    <span className="text-3xl md:text-4xl font-black text-white italic drop-shadow-4xl">{(item.total_conf * 100).toFixed(0)}</span>
                </div>
                <div className="flex-1 md:w-full space-y-1.5">
                    <div className="h-1 bg-white/5 rounded-full overflow-hidden"><div className="h-full bg-blue-500" style={{ width: `${(item.trad_conf || 0.6) * 100}%` }} /></div>
                    <div className="h-1 bg-white/5 rounded-full overflow-hidden"><div className="h-full bg-green-500" style={{ width: `${(item.swarm_conf || 0.8) * 100}%` }} /></div>
                </div>
            </div>
        </div>
    </div>
);

const EquityCurve = ({ data }) => {
  if (!data || data.length < 2) return <div className="h-[300px] bg-white/5 rounded-3xl animate-pulse" />;
  const width = 800; const height = 300; const padding = 40;
  const maxVal = Math.max(...data.map(d => Math.max(d.strat, d.bench))) * 1.05;
  const minVal = Math.min(...data.map(d => Math.min(d.strat, d.bench))) * 0.95;
  const range = maxVal - minVal;
  
  const getX = (i) => padding + (i / (data.length - 1)) * (width - 2 * padding);
  const getY = (v) => height - padding - ((v - minVal) / range) * (height - 2 * padding);

  const stratPoints = data.map((d, i) => `${getX(i)},${getY(d.strat)}`).join(' ');
  const benchPoints = data.map((d, i) => `${getX(i)},${getY(d.bench)}`).join(' ');

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
      {/* Grid */}
      {[0, 0.25, 0.5, 0.75, 1].map(f => (
          <line key={f} x1={padding} y1={padding + f * (height-2*padding)} x2={width-padding} y2={padding + f * (height-2*padding)} stroke="white" strokeOpacity="0.05" strokeWidth="1" />
      ))}
      {/* Benchmark */}
      <polyline fill="none" stroke="#64748b" strokeWidth="2" strokeDasharray="4 4" points={benchPoints} opacity="0.5" />
      {/* Strategy */}
      <polyline fill="none" stroke="#3b82f6" strokeWidth="4" points={stratPoints} strokeLinejoin="round" strokeLinecap="round" className="drop-shadow-[0_0_12px_rgba(59,130,246,0.5)]" />
      {/* Points */}
      {data.filter((_,i) => i % 5 === 0 || i === data.length-1).map((d, i, arr) => (
          <text key={i} x={getX(data.indexOf(d))} y={height-10} fill="#475569" fontSize="8" textAnchor="middle">{d.ts}</text>
      ))}
    </svg>
  );
};

const App = () => {
  const [activeTab, setActiveTab] = useState('inventory');
  const [signals, setSignals] = useState([]);
  const [fx, setFx] = useState([]);
  const [commodities, setCommodities] = useState([]);
  const [crypto, setCrypto] = useState([]);
  const [hft, setHft] = useState([]);
  const [performance, setPerformance] = useState({ metrics: [], curve: [] });
  const [formulas, setFormulas] = useState([]);
  const [macro, setMacro] = useState({ indices: {}, system_risk: 'LOW', shock_text: 'System Nominal' });
  const [inventory, setInventory] = useState([]);
  const [outlook, setOutlook] = useState({ market_mood: '...', swarm_conclusion: '...', recommendations: [] });
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [maintenanceStatus, setMaintenanceStatus] = useState({});
  const [newAsset, setNewAsset] = useState({ ticker: '', asset_class: 'STOCK', quantity: 0, buy_price: 0 });

  const API_BASE = "http://47.129.86.69:8000/api";

  const fetchStatic = async () => {
    try {
      const [mRes, sRes, fRes, cRes, cryRes, hRes, iRes, oRes, formRes, perfRes] = await Promise.all([
        fetch(`${API_BASE}/macro/pulse`),
        fetch(`${API_BASE}/signals/1`),
        fetch(`${API_BASE}/fx/pairs`),
        fetch(`${API_BASE}/commodities/all`),
        fetch(`${API_BASE}/crypto/pairs`),
        fetch(`${API_BASE}/hft/matrix`),
        fetch(`${API_BASE}/inventory/evaluate`),
        fetch(`${API_BASE}/market/outlook`),
        fetch(`${API_BASE}/metadata/formulas`),
        fetch(`${API_BASE}/performance/strategy`)
      ]);
      if (mRes.ok) setMacro(await mRes.json());
      if (sRes.ok) setSignals(await sRes.json());
      if (fRes.ok) setFx(await fRes.json());
      if (cRes.ok) setCommodities(await cRes.json());
      if (cryRes.ok) setCrypto(await cryRes.json());
      if (hRes.ok) setHft(await hRes.json());
      if (iRes.ok) setInventory(await iRes.json());
      if (oRes.ok) setOutlook(await oRes.json());
      if (formRes.ok) setFormulas(await formRes.json());
      if (perfRes.ok) setPerformance(await perfRes.json());
    } catch (e) { console.error(e); }
  };

  const addAsset = async () => {
    if (!newAsset.ticker) return;
    try {
        await fetch(`${API_BASE}/inventory/add`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(newAsset)
        });
        setNewAsset({ ticker: '', asset_class: 'STOCK', quantity: 0, buy_price: 0 });
        fetchStatic();
    } catch (e) { console.error(e); }
  };

  const deleteAsset = async (ticker) => {
    try {
        await fetch(`${API_BASE}/inventory/delete/${ticker}`, { method: 'DELETE' });
        fetchStatic();
    } catch (e) { console.error(e); }
  };

  const triggerMaintenance = async (component) => {
    setMaintenanceStatus(prev => ({ ...prev, [component]: 'Syncing...' }));
    await fetch(`${API_BASE}/maintenance/refresh/${component}`, { method: 'POST' });
    setTimeout(() => { 
        setMaintenanceStatus(prev => ({ ...prev, [component]: 'Queued' }));
        fetchStatic();
    }, 2000);
  };

  useEffect(() => {
    fetchStatic();
    const fetchStatus = async () => {
        const components = ['indices', 'stocks', 'fx', 'commodities', 'crypto', 'hft'];
        for (const c of components) {
            try {
                const res = await fetch(`${API_BASE}/maintenance/status/${c}`);
                if (res.ok) {
                    const data = await res.json();
                    setMaintenanceStatus(prev => ({ ...prev, [c]: data.status }));
                }
            } catch {}
        }
    };
    fetchStatus();
    const interval = setInterval(() => { fetchStatic(); fetchStatus(); }, 30000);
    return () => clearInterval(interval);
  }, []);

  const getHKTNow = () => new Date(new Date().getTime() + 8 * 60 * 60 * 1000).toISOString().replace('T', ' ').substring(0, 19);

  return (
    <div className="min-h-screen bg-[#05070a] text-slate-300 flex flex-col font-sans overflow-x-hidden selection:bg-blue-500/30">
      
      {/* 1. Ticker Tape */}
      <div className="h-24 bg-black/90 border-b border-white/5 flex items-center px-4 md:px-6 sticky top-0 z-[100] backdrop-blur-xl w-full overflow-x-auto no-scrollbar shadow-xl">
        <div className="flex">
            {['US', 'HK', 'EU', 'CN', 'SG'].map(idx => (
                <MacroPill key={idx} label={macro.indices?.[idx]?.label || idx} 
                    value={macro.indices?.[idx]?.value} 
                    change={macro.indices?.[idx]?.change} 
                    est={macro.indices?.[idx]?.estimates} 
                />
            ))}
        </div>
      </div>

      {/* 2. Brand & Navigation */}
      <header className="px-4 md:px-12 py-5 md:py-8 bg-gradient-to-b from-white/[0.02] to-transparent sticky top-24 z-[90] backdrop-blur-xl border-b border-white/5">
        <div className="max-w-[1400px] mx-auto flex flex-col lg:flex-row lg:items-center justify-between gap-4 md:gap-8">
            <div className="flex flex-col md:flex-row md:items-center gap-4 md:gap-10 text-left">
                <div className="flex flex-col">
                    <h1 className="text-2xl md:text-4xl font-black text-white tracking-tightest uppercase italic flex items-baseline">
                        ORCHESTRA <span className="text-blue-500 text-[7px] md:text-[9px] not-italic ml-2 md:ml-3 font-black tracking-[0.5em] opacity-80">v2.7 ELITE</span>
                    </h1>
                    <div className="flex items-center gap-2 mt-1">
                        <span className="h-1.5 w-1.5 bg-blue-500 rounded-full animate-pulse" />
                        <span className="text-[7px] md:text-[9px] font-black text-slate-500 uppercase tracking-widest">Global Compute Cluster: Active</span>
                        <div className="h-3 w-px bg-white/10 mx-2" />
                        <span className="text-[7px] md:text-[9px] font-black text-blue-400 uppercase tracking-widest font-mono italic">HKT: {getHKTNow()}</span>
                    </div>
                </div>
            </div>
            <nav className="flex gap-1 p-0.5 bg-white/[0.03] rounded-xl border border-white/10 shadow-inner overflow-x-auto no-scrollbar scroll-smooth">
                {['inventory', 'market', 'signals', 'fx', 'commodities', 'crypto', 'hft', 'performance', 'config'].map(tab => (
                    <button key={tab} onClick={() => setActiveTab(tab)} className={`px-4 md:px-6 py-1.5 md:py-2.5 rounded-lg text-[8px] md:text-[9px] font-black uppercase tracking-widest transition-all whitespace-nowrap ${activeTab === tab ? 'bg-white text-black' : 'text-slate-500 hover:text-slate-300'}`}>{tab}</button>
                ))}
            </nav>
        </div>
      </header>

      {/* 3. Main Stage */}
      <main className="flex-1 p-4 md:p-10 max-w-[1400px] mx-auto w-full mb-32 space-y-6 md:space-y-10">
        
        {/* Universal Alert */}
        {activeTab !== 'config' && (
            <div className="bg-[#0d111c]/40 p-5 md:p-6 rounded-xl md:rounded-2xl border border-white/5 flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative overflow-hidden group shadow-lg">
                <div className={`absolute top-0 left-0 h-full w-1 ${macro.system_risk === 'CRITICAL' ? 'bg-red-500' : 'bg-blue-500'}`} />
                <div className="space-y-1 max-w-4xl text-left">
                    <span className="text-[7px] md:text-[8px] font-black text-slate-500 uppercase tracking-[0.4em]">Shock Radar Mode: {macro.system_risk}</span>
                    <p className="text-base md:text-lg text-white font-medium italic leading-relaxed">"{macro.shock_text || 'Monitoring Global Noise...'}"</p>
                </div>
                <div className="bg-white/5 px-4 md:px-5 py-2 md:py-3 rounded-lg md:rounded-xl text-center min-w-[120px] md:min-w-[160px]">
                    <span className="text-[6px] md:text-[7px] font-black text-slate-500 uppercase block mb-0.5">Stance</span>
                    <span className={`text-base md:text-lg font-black italic ${macro.system_risk === 'CRITICAL' ? 'text-red-500' : 'text-blue-400'}`}>
                        {macro.system_risk === 'CRITICAL' ? 'DEFENSIVE' : 'NOMINAL'}
                    </span>
                </div>
            </div>
        )}

        {activeTab === 'inventory' && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500 text-left">
                <div className="bg-[#0d111c]/60 p-5 md:p-8 rounded-xl md:rounded-[2rem] border border-white/10 shadow-2xl flex flex-wrap gap-4 md:gap-6 items-end relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-6 md:p-8 opacity-5 text-4xl md:text-5xl font-black italic select-none tracking-tighter">ADD_POSITION</div>
                    <div className="flex flex-col gap-1.5 min-w-[120px]">
                        <span className="text-[8px] font-black text-blue-500 uppercase tracking-widest">Ticker</span>
                        <input className="bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-white outline-none focus:border-blue-500 font-mono text-xs" placeholder="AAPL / BTC-USD" value={newAsset.ticker} onChange={e => setNewAsset({...newAsset, ticker: e.target.value.toUpperCase()})} />
                    </div>
                    <div className="flex flex-col gap-1.5">
                        <span className="text-[8px] font-black text-blue-500 uppercase tracking-widest">Class</span>
                        <select className="bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-white outline-none focus:border-blue-500 cursor-pointer appearance-none text-xs" value={newAsset.asset_class} onChange={e => setNewAsset({...newAsset, asset_class: e.target.value})}>
                            <option value="STOCK">STOCK</option>
                            <option value="FX">FX</option>
                            <option value="CRYPTO">CRYPTO</option>
                            <option value="COMMODITY">COMMODITY</option>
                        </select>
                    </div>
                    <div className="flex flex-col gap-1.5">
                        <span className="text-[8px] font-black text-blue-500 uppercase tracking-widest">Quantity</span>
                        <input type="number" className="bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-white outline-none focus:border-blue-500 font-mono text-xs w-24" value={newAsset.quantity} onChange={e => setNewAsset({...newAsset, quantity: parseFloat(e.target.value) || 0})} />
                    </div>
                    <div className="flex flex-col gap-1.5">
                        <span className="text-[8px] font-black text-blue-500 uppercase tracking-widest">Buy Price</span>
                        <input type="number" className="bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-white outline-none focus:border-blue-500 font-mono text-xs w-24" value={newAsset.buy_price} onChange={e => setNewAsset({...newAsset, buy_price: parseFloat(e.target.value) || 0})} />
                    </div>
                    <button onClick={addAsset} className="px-8 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest bg-blue-600 hover:bg-blue-500 text-white transition-all shadow-lg active:scale-95">Deploy Capital</button>
                </div>

                <div className="bg-[#0d111c]/60 rounded-xl md:rounded-2xl border border-white/10 overflow-hidden shadow-2xl">
                    <div className="p-5 md:p-8 border-b border-white/10 flex justify-between items-center bg-white/[0.01]">
                        <h3 className="text-xl md:text-2xl font-black text-white uppercase italic tracking-tighter">Global Inventory</h3>
                        <div className="text-[8px] text-slate-600 uppercase font-black tracking-widest">Sync: {new Date().toLocaleTimeString('en-HK')}</div>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left min-w-[1000px]">
                            <thead>
                                <tr className="border-b border-white/5 bg-white/[0.01]">
                                    <th className="p-5 md:p-6 text-[8px] font-black text-slate-500 uppercase tracking-widest">Asset</th>
                                    <th className="p-5 md:p-6 text-[8px] font-black text-slate-500 uppercase tracking-widest">Qty</th>
                                    <th className="p-5 md:p-6 text-[8px] font-black text-slate-500 uppercase tracking-widest">Buy Price</th>
                                    <th className="p-5 md:p-6 text-[8px] font-black text-slate-500 uppercase tracking-widest">Current</th>
                                    <th className="p-5 md:p-6 text-[8px] font-black text-slate-500 uppercase tracking-widest">Win/Loss</th>
                                    <th className="p-5 md:p-6 text-[8px] font-black text-slate-500 uppercase tracking-widest text-center">Estimates (1D / 1W / 1M)</th>
                                    <th className="p-5 md:p-6 text-[8px] font-black text-slate-500 uppercase tracking-widest text-center">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {inventory.map((i, idx) => (
                                    <tr key={idx} className="hover:bg-white/[0.01] transition-colors group">
                                        <td className="p-5 md:p-6">
                                            <div className="flex flex-col">
                                                <span className="text-lg md:text-xl font-black text-white italic leading-none group-hover:text-blue-400 transition-colors">{i.ticker}</span>
                                                <span className="text-[7px] text-slate-600 uppercase mt-1 font-bold">{i.asset_class}</span>
                                            </div>
                                        </td>
                                        <td className="p-5 md:p-6 font-mono text-sm text-slate-300">{i.quantity}</td>
                                        <td className="p-5 md:p-6 font-mono text-sm text-slate-300">${i.buy}</td>
                                        <td className="p-5 md:p-6 font-mono text-sm font-bold text-white">${i.current}</td>
                                        <td className="p-5 md:p-6"><span className={`px-2 py-0.5 rounded-md text-[8px] font-black uppercase ${i.win_loss.includes('+') ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>{i.win_loss}</span></td>
                                        <td className="p-5 md:p-6">
                                            <div className="flex justify-center gap-4 font-mono">
                                                <div className="flex flex-col items-center"><span className="text-[6px] text-slate-600 uppercase mb-0.5">1D</span><span className={`text-[10px] font-black ${i.est_1d?.includes('+') ? 'text-blue-400' : 'text-orange-400'}`}>{i.est_1d}</span></div>
                                                <div className="flex flex-col items-center"><span className="text-[6px] text-slate-600 uppercase mb-0.5">1W</span><span className={`text-[10px] font-black ${i.est_7d?.includes('+') ? 'text-blue-400' : 'text-orange-400'}`}>{i.est_7d}</span></div>
                                                <div className="flex flex-col items-center"><span className="text-[6px] text-slate-600 uppercase mb-0.5">1M</span><span className={`text-[10px] font-black ${i.est_1m?.includes('+') ? 'text-blue-400' : 'text-orange-400'}`}>{i.est_1m}</span></div>
                                            </div>
                                        </td>
                                        <td className="p-5 md:p-6 text-center">
                                            <button onClick={() => deleteAsset(i.ticker)} className="px-3 py-1 rounded-md text-[7px] font-black uppercase tracking-widest border border-red-500/30 text-red-400 hover:bg-red-500 hover:text-white transition-all">Liquidate</button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        )}

        {activeTab === 'market' && (
            <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500 text-left">
                <div className="grid lg:grid-cols-12 gap-8">
                    <div className="lg:col-span-8 bg-[#0d111c]/60 rounded-xl p-10 md:p-12 border border-white/10 flex flex-col justify-center shadow-xl">
                        <span className="text-[10px] font-black text-blue-500 uppercase tracking-[0.4em] mb-8">Global Regime Summary</span>
                        <div className="space-y-6 mb-12">
                            <span className="text-5xl md:text-7xl font-black text-white italic tracking-tighter drop-shadow-2xl">{outlook.market_mood || 'Analyzing'}</span>
                            <p className="text-xl md:text-2xl text-slate-300 italic leading-snug border-l-2 border-white/10 pl-6 md:pl-8">"{outlook.swarm_conclusion || 'Assembling Cross-Market Intelligence...'}"</p>
                        </div>
                        <div className="border-t border-white/10 pt-10">
                            <h4 className="text-[12px] md:text-[14px] font-black text-white uppercase tracking-[0.4em] mb-8">Global Economy Index Drivers</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-8">
                                {['US', 'HK', 'EU', 'CN', 'SG'].map(idx => {
                                    const labels = {'US':'DJI', 'HK':'HSI', 'EU':'STOXX50', 'CN':'SSE', 'SG':'STI'};
                                    const l = labels[idx];
                                    return (
                                    <div key={idx} className="bg-white/[0.03] p-8 md:p-10 rounded-2xl md:rounded-3xl border border-white/10 space-y-6 group hover:bg-white/[0.05] transition-all relative overflow-hidden shadow-md">
                                        <div className="flex justify-between items-center relative z-10">
                                            <span className="text-xl md:text-2xl font-black text-white italic tracking-tighter">{l} Narrative</span>
                                            <span className="text-[8px] md:text-[10px] font-black text-blue-400 uppercase tracking-widest bg-blue-500/10 px-2 md:px-3 py-1 rounded-full">AI Verified</span>
                                        </div>
                                        <p className="text-[13px] md:text-[15px] text-slate-300 font-medium italic leading-relaxed relative z-10">{macro.indices?.[idx]?.rationale || 'Syncing swarm narrative...'}</p>
                                    </div>
                                )})}
                            </div>
                        </div>
                    </div>
                    <div className="lg:col-span-4 space-y-8">
                        <div className="bg-gradient-to-br from-blue-900/20 to-transparent rounded-2xl md:rounded-3xl p-8 md:p-10 border border-white/10 flex flex-col justify-center text-center shadow-xl">
                            <span className="text-[8px] md:text-[9px] font-black text-slate-500 uppercase tracking-widest mb-4">Quant Strength</span>
                            <span className="text-6xl md:text-7xl font-black text-white italic">88<span className="text-2xl opacity-20">%</span></span>
                        </div>
                    </div>
                </div>
            </div>
        )}

        {activeTab === 'signals' && (
            <div className="space-y-12 md:space-y-20 animate-in fade-in slide-in-from-bottom-4 duration-500 text-left">
                {['US', 'HK', 'CN'].map(marketType => (
                    <div key={marketType} className="space-y-6 md:space-y-10">
                        <div className="flex items-baseline gap-4"><h2 className="text-3xl md:text-4xl font-black text-white italic tracking-tightest uppercase">{marketType} Alpha Matrix</h2><span className="h-px flex-1 bg-white/10" /></div>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 md:gap-10">
                            {['Short Term', 'Long Term'].map(horizon => (
                                <div key={horizon} className="bg-[#0d111c]/60 rounded-2xl md:rounded-3xl border border-white/10 overflow-hidden flex flex-col shadow-2xl">
                                    <div className="p-5 md:p-8 border-b border-white/10 bg-white/[0.02] flex justify-between items-center"><h3 className="text-base md:text-xl font-black text-white uppercase italic tracking-tighter">{horizon} Strategy</h3><span className={`text-[7px] md:text-[9px] font-black uppercase tracking-widest px-2 md:px-3 py-1 rounded-full ${horizon === 'Short Term' ? 'bg-blue-500/10 text-blue-400' : 'bg-indigo-500/10 text-indigo-400'}`}>{horizon === 'Short Term' ? 'Aggressive' : 'Growth'}</span></div>
                                    <div className="divide-y divide-white/5 flex-1">
                                        {signals.filter(s => s.market === marketType && s.horizon === horizon).map((s, idx) => (
                                            <HighDensityCard key={idx} item={s} type="STOCK" />
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        )}

        {activeTab === 'fx' && (
            <div className="bg-[#0d111c]/60 rounded-2xl md:rounded-[3rem] border border-white/10 overflow-hidden shadow-4xl backdrop-blur-3xl animate-in fade-in slide-in-from-bottom-4 duration-500 text-left">
                <div className="p-6 md:p-12 border-b border-white/10 flex justify-between items-center bg-white/[0.02]"><h3 className="text-2xl md:text-3xl font-black text-white uppercase italic tracking-tighter">Global FX Liquidity</h3></div>
                <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-white/5">
                    {fx.map((f, idx) => (
                        <HighDensityCard key={idx} item={f} type="FX" />
                    ))}
                </div>
            </div>
        )}

        {activeTab === 'commodities' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-10 animate-in fade-in slide-in-from-bottom-4 duration-500 text-left">
                {commodities.map((c, idx) => (
                    <HighDensityCard key={idx} item={c} type="COMMODITY" />
                ))}
            </div>
        )}

        {activeTab === 'crypto' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 md:gap-10 animate-in fade-in slide-in-from-bottom-4 duration-500 text-left">
                {crypto.map((c, idx) => (
                    <HighDensityCard key={idx} item={c} type="CRYPTO" />
                ))}
            </div>
        )}

        {activeTab === 'hft' && (
            <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500 text-left">
                <div className="flex items-baseline gap-4"><h2 className="text-3xl md:text-4xl font-black text-white italic tracking-tightest uppercase">High-Frequency Matrix</h2><div className="text-[9px] text-slate-600 uppercase font-black">Velocity Engine Active</div><span className="h-px flex-1 bg-white/10" /></div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {hft.map((h, i) => (
                        <div key={i} className="bg-[#0d111c]/60 rounded-2xl md:rounded-3xl p-8 md:p-10 border border-white/10 shadow-2xl flex flex-col gap-6 group hover:border-blue-500/30 transition-all relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-8 opacity-5 text-5xl md:text-6xl font-black italic select-none">{h.asset_class}</div>
                            <div className="flex justify-between items-start text-left">
                                <div className="space-y-1 text-left"><span className="text-3xl md:text-5xl font-black text-white italic tracking-tighter group-hover:text-blue-400 transition-colors leading-none text-left">{h.ticker}</span><div className="text-[8px] md:text-[9px] text-slate-500 uppercase font-bold tracking-widest mt-2 flex items-center gap-2"><span className="h-1.5 w-1.5 bg-blue-500 rounded-full animate-ping" />Liquidity: {h.liquidity_momentum}</div></div>
                                <span className={`px-2 md:px-3 py-1 rounded-lg text-[8px] md:text-[9px] font-black uppercase tracking-widest ${h.shock_warning === 'CRITICAL' ? 'bg-red-500 text-white' : 'bg-blue-500/10 text-blue-400'}`}>{h.shock_warning} SHOCK</span>
                            </div>
                            <div className="space-y-5">
                                <div className="flex justify-between items-center bg-black/40 p-4 rounded-xl md:rounded-2xl border border-white/5"><div className="flex flex-col text-left"><span className="text-[7px] md:text-[8px] text-slate-500 uppercase font-black">Fusion Signal</span><span className={`text-lg md:text-xl font-black italic ${h.fusion_signal?.includes('BUY') ? 'text-green-400' : 'text-orange-400'}`}>{h.fusion_signal}</span></div><div className="flex flex-col text-right"><span className="text-[7px] md:text-[8px] text-slate-500 uppercase font-black">Pressure Val</span><span className="text-lg md:text-xl font-black text-white font-mono">{(h.pressure_value || 0).toFixed(2)}</span></div></div>
                                <p className="text-[12px] md:text-[13px] text-slate-300 italic font-medium leading-relaxed text-left">"{h.reasoning}"</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        )}

        {activeTab === 'performance' && (
            <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500 text-left">
                <div className="flex items-baseline gap-4"><h2 className="text-4xl font-black text-white italic tracking-tightest uppercase">Strategy Backtest</h2><span className="h-px flex-1 bg-white/10" /></div>
                
                <div className="grid lg:grid-cols-3 gap-10">
                    <div className="lg:col-span-2 bg-[#0d111c]/60 p-10 rounded-[3rem] border border-white/10 shadow-2xl space-y-10 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-10 opacity-5 text-7xl font-black italic select-none">EQUITY_CURVE</div>
                        <div className="flex justify-between items-center relative z-10">
                            <div className="space-y-1">
                                <h3 className="text-xl font-black text-white uppercase tracking-widest">30-Day Simulated Growth</h3>
                                <div className="flex items-center gap-4">
                                    <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-blue-500" /> <span className="text-[10px] font-bold uppercase text-slate-500">Adopted Strategy</span></div>
                                    <div className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-slate-500 border border-dashed" /> <span className="text-[10px] font-bold uppercase text-slate-500">Benchmark (S&P 500)</span></div>
                                </div>
                            </div>
                            <span className="text-[10px] font-black text-blue-400 uppercase bg-blue-500/10 px-3 py-1 rounded-full">Validated by Swarm</span>
                        </div>
                        <EquityCurve data={performance.curve} />
                    </div>

                    <div className="bg-[#0d111c]/60 p-10 rounded-[3rem] border border-white/10 shadow-2xl flex flex-col gap-6">
                        <h3 className="text-xl font-black text-white uppercase tracking-widest border-b border-white/5 pb-6">Performance Matrix</h3>
                        <div className="space-y-6">
                            {performance.metrics.map((m, i) => (
                                <div key={i} className="flex justify-between items-center group">
                                    <div className="flex flex-col">
                                        <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Since {m.period}</span>
                                        <span className="text-sm font-bold text-white italic">{m.period === 'YEARLY' ? 'YTD Growth' : m.period === 'QUARTERLY' ? 'Quarterly Alpha' : 'Rolling Return'}</span>
                                    </div>
                                    <div className="text-right">
                                        <div className="flex items-center gap-2">
                                            <span className={`text-xl font-black font-mono ${m.strategy_return >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                                                {(m.strategy_return * 100).toFixed(2)}%
                                            </span>
                                            <span className="text-[8px] text-slate-600 font-bold">VS</span>
                                            <span className="text-xs font-bold text-slate-400 font-mono">{(m.benchmark_return * 100).toFixed(2)}%</span>
                                        </div>
                                        <span className={`text-[8px] font-black uppercase ${m.strategy_return > m.benchmark_return ? 'text-blue-400' : 'text-slate-500'}`}>
                                            {m.strategy_return > m.benchmark_return ? 'Outperforming' : 'Tracking'}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="mt-auto p-6 bg-blue-500/5 border border-blue-500/10 rounded-2xl italic text-[11px] text-slate-400 leading-relaxed">
                            "The adopted strategy leverages equal-weighted core market leaders (NVDA, AAPL, etc) and momentum-based Z-scoring. Backtest assumes rebalancing at each period start."
                        </div>
                    </div>
                </div>
            </div>
        )}
            <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500 text-left">
                <div className="flex items-baseline gap-4"><h2 className="text-3xl md:text-4xl font-black text-white italic tracking-tightest uppercase">System Maintenance</h2><span className="h-px flex-1 bg-white/10" /></div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 md:gap-10">
                    {[
                        { id: 'indices', name: 'Global Indices & Mood', desc: 'Syncs DJI, HSI, STOXX50, SSE, STI and recalibrates global sentiment.' },
                        { id: 'stocks', name: 'Stock Alpha Matrix', desc: 'Re-trains Prophet models for US, HK, CN stock universe.' },
                        { id: 'fx', name: 'Forex Liquidity Layer', desc: 'Updates 12 major currency pairs with live interest rate differentials.' },
                        { id: 'commodities', name: 'Hard Assets (Commodities)', desc: 'Syncs Gold, Oil, Silver, Natural Gas with macro-driver matrices.' },
                        { id: 'crypto', name: 'Digital Assets (Crypto)', desc: 'Syncs BTC, ETH, SOL with on-chain velocity and liquidity proxies.' },
                        { id: 'hft', name: 'High-Frequency Layer', desc: 'Recalibrates Liquidity Pressure and Geopolitical Shock vectors.' }
                    ].map(comp => (
                        <div key={comp.id} className="bg-[#0d111c]/60 rounded-xl md:rounded-[2.5rem] p-6 md:p-10 border border-white/10 shadow-xl flex flex-col gap-6 md:gap-8 group hover:border-blue-500/30 transition-all">
                            <div className="space-y-1.5 md:space-y-2 text-left"><h3 className="text-lg md:text-xl font-black text-white uppercase italic tracking-tighter text-left">{comp.name}</h3><p className="text-xs md:text-sm text-slate-400 leading-relaxed font-medium text-left">"{comp.desc}"</p></div>
                            <div className="flex items-center justify-between mt-auto pt-6 md:pt-8 border-t border-white/5"><div className="flex flex-col text-left"><span className="text-[8px] md:text-[9px] font-black text-slate-600 uppercase text-left">Current Status</span><span className="text-xs md:text-sm font-bold text-blue-400 font-mono italic text-left">{maintenanceStatus[comp.id] || 'Idle'}</span></div><button onClick={() => triggerMaintenance(comp.id)} className="px-5 md:px-10 py-2 md:py-3.5 rounded-xl text-[8px] md:text-[9px] font-black uppercase tracking-widest bg-white text-black hover:bg-blue-500 hover:text-white transition-all">Trigger Sync</button></div>
                        </div>
                    ))}
                </div>
            </div>
        )}

      </main>
    </div>
  );
};

export default App;
