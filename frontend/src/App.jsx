import React, { useState, useEffect } from 'react';

const StatCard = ({ label, value, color, trend }) => (
  <div className="bg-slate-800/40 p-5 rounded-2xl border border-slate-700/50 hover:border-blue-500/30 transition-all group">
    <div className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-2 group-hover:text-slate-400 transition-colors">{label}</div>
    <div className={`text-2xl font-mono font-bold ${color}`}>{value}</div>
    {trend && <div className="text-[10px] mt-2 text-green-500 font-bold">{trend}</div>}
  </div>
);

const App = () => {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTicker, setSearchTicker] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [searching, setSearching] = useState(false);
  const [projects, setProjects] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');

  const API_BASE = "http://47.129.86.69:8000/api";

  const fetchData = async () => {
    try {
      const pRes = await fetch(`${API_BASE}/projects`);
      const pData = await pRes.json();
      setProjects(pData);
      
      const sRes = await fetch(`${API_BASE}/signals/1`);
      const sData = await sRes.json();
      setSignals(Array.isArray(sData) ? sData : []);
    } catch (err) { console.error("Fetch error:", err); }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, []);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!searchTicker || searching) return;
    setSearching(true);
    setAnalysisResult(null);
    try {
      const res = await fetch(`${API_BASE}/analyze/${searchTicker}`);
      const task = await res.json();
      
      // Poll for result
      const poll = setInterval(async () => {
        const check = await fetch(`${API_BASE}/analyze/result/${task.task_id}`);
        const status = await check.json();
        if (status.status === 'complete') {
          setAnalysisResult(status.data);
          setSearching(false);
          clearInterval(poll);
          fetchData(); // Refresh history
        } else if (status.status === 'error') {
          alert("AI Analysis Error: " + status.message);
          setSearching(false);
          clearInterval(poll);
        }
      }, 2000);
    } catch (err) { setSearching(false); }
  };

  const launchRun = () => {
    setSearchTicker("0700.HK");
    handleSearch();
  };

  return (
    <div className="min-h-screen bg-[#080b14] text-slate-300 flex font-sans selection:bg-blue-500/30">
      <aside className="w-80 border-r border-white/5 p-8 bg-[#0a0e1a] flex flex-col">
        <div className="flex items-center gap-3 mb-12">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl flex items-center justify-center font-black text-white shadow-lg">JT</div>
          <div className="flex flex-col">
            <span className="font-black text-lg text-white leading-none">ORCHESTRA</span>
            <span className="text-[10px] text-blue-500 font-bold tracking-widest">TRADING OS</span>
          </div>
        </div>
        
        <div className="flex-1">
          <div className="text-slate-500 text-[10px] uppercase font-black mb-6">Active Portfolios</div>
          <div className="space-y-4">
            {projects.map(p => (
              <div key={p.id} className="p-4 rounded-2xl bg-slate-800/40 border border-white/5 hover:border-blue-500/40 cursor-pointer group">
                <div className="flex justify-between items-center mb-3">
                  <span className="font-bold text-sm group-hover:text-white">{p.name}</span>
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                </div>
                <div className="w-full bg-white/5 h-1.5 rounded-full"><div className="bg-blue-600 h-full w-2/3"></div></div>
              </div>
            ))}
          </div>
        </div>
      </aside>

      <main className="flex-1 flex flex-col min-w-0">
        <header className="h-24 border-b border-white/5 flex items-center justify-between px-12 bg-[#0a0e1a]/80 backdrop-blur-xl sticky top-0 z-50">
          <form onSubmit={handleSearch} className="flex-1 max-w-xl relative group">
            <input 
              type="text" 
              placeholder="Search Ticker (e.g. 0700.HK)" 
              className={`w-full bg-white/5 border rounded-2xl py-3.5 px-6 text-sm focus:outline-none ${searching ? 'animate-pulse border-blue-500' : 'border-white/5'}`}
              value={searchTicker}
              onChange={(e) => setSearchTicker(e.target.value)}
              disabled={searching}
            />
          </form>
          <div className="flex items-center gap-6 ml-10">
            <button onClick={launchRun} disabled={searching} className="bg-white text-black px-6 py-3 rounded-xl text-xs font-black uppercase tracking-widest hover:bg-blue-500 hover:text-white transition-all">
              {searching ? "PROCESSING..." : "LAUNCH RUN"}
            </button>
          </div>
        </header>

        <div className="p-12 overflow-y-auto">
          {analysisResult && (
            <div className="mb-12 bg-gradient-to-br from-blue-600/20 to-indigo-600/5 border border-blue-500/20 rounded-[2.5rem] p-10 relative group animate-in slide-in-from-top-4">
              <div className="absolute top-0 right-0 p-8">
                <div className={`text-4xl font-black px-8 py-3 rounded-2xl border-4 ${analysisResult.recommendation === 'BUY' ? 'border-green-500/30 text-green-400 bg-green-500/10' : 'border-red-500/30 text-red-400 bg-red-500/10'}`}>
                  {analysisResult.recommendation}
                </div>
              </div>
              <h2 className="text-5xl font-black text-white tracking-tighter mb-2">{analysisResult.ticker}</h2>
              <div className="grid grid-cols-4 gap-6 mt-10">
                <div className="bg-white/5 p-6 rounded-3xl border border-white/5">
                  <span className="text-[10px] font-black text-blue-500 uppercase block mb-4">7D Forecast</span>
                  <div className="text-2xl font-black text-white">{analysisResult.forecasts['7d']}</div>
                </div>
                <div className="col-span-3 bg-white/5 p-6 rounded-3xl border border-white/5 grid grid-cols-3">
                  <div><span className="text-[10px] uppercase block text-slate-500 mb-2">Trend</span><div className="text-xl font-bold">{analysisResult.metrics.ts_score.toFixed(2)}</div></div>
                  <div><span className="text-[10px] uppercase block text-slate-500 mb-2">Sentiment</span><div className="text-xl font-bold">{analysisResult.metrics.sent_score.toFixed(2)}</div></div>
                  <div><span className="text-[10px] uppercase block text-slate-500 mb-2">Alpha</span><div className="text-xl font-bold">{analysisResult.metrics.alpha_score.toFixed(2)}</div></div>
                </div>
              </div>
            </div>
          )}

          <div className="grid grid-cols-4 gap-6 mb-12">
            <StatCard label="Analysed Assets" value="48" color="text-white" trend="+2 New" />
            <StatCard label="Avg Edge" value="0.42" color="text-blue-500" />
            <StatCard label="Active Signals" value={signals.length} color="text-green-500" />
            <StatCard label="Token Burn" value="$0.14" color="text-slate-600" />
          </div>

          <div className="bg-[#0e1321] rounded-[2rem] border border-white/5 shadow-2xl">
            <div className="p-8 border-b border-white/5 flex justify-between items-center text-lg"><h3 className="font-bold text-white">Signal Audit Log</h3></div>
            <table className="w-full text-left">
              <thead>
                <tr className="bg-white/[0.02] text-[10px] uppercase text-slate-500 font-black border-b border-white/5">
                  <th className="p-6 pl-10">Ticker</th>
                  <th className="p-6 text-center">Trend</th>
                  <th className="p-6 text-center">Sentiment</th>
                  <th className="p-6 text-center">Alpha</th>
                  <th className="p-6 text-right pr-10">Edge</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 font-mono text-xs">
                {signals.map((s) => (
                  <tr key={s.id} className="hover:bg-blue-600/[0.03]">
                    <td className="p-6 pl-10 font-black text-slate-300">{s.ticker}</td>
                    <td className={`p-6 text-center ${s.ts_score > 0 ? 'text-green-500' : 'text-red-500'}`}>{s.ts_score > 0 ? '▲' : '▼'} {Math.abs(s.ts_score).toFixed(2)}</td>
                    <td className="p-6 text-center text-blue-400">{s.sent_score.toFixed(2)}</td>
                    <td className="p-6 text-center text-slate-500">{s.alpha_score.toFixed(2)}</td>
                    <td className="p-6 text-right pr-10"><span className="px-4 py-1.5 rounded-full font-black text-[10px] border bg-green-500/10 text-green-500 border-green-500/20">{s.final_score.toFixed(2)}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
