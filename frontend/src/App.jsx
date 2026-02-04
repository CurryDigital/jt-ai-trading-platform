import React, { useState, useEffect } from 'react';

const StatCard = ({ label, value, color }) => (
  <div className="bg-slate-800/50 p-4 rounded-lg border border-slate-700/50">
    <div className="text-slate-500 text-xs uppercase tracking-wider mb-1">{label}</div>
    <div className={`text-xl font-mono font-bold ${color}`}>{value}</div>
  </div>
);

const ProjectItem = ({ name, status, count, active }) => (
  <div className={`p-4 rounded-xl border transition-all cursor-pointer mb-3 ${
    active ? 'bg-blue-600/20 border-blue-500/50' : 'bg-slate-800/30 border-slate-700/50 hover:border-slate-500'
  }`}>
    <div className="flex justify-between items-start">
      <h3 className="font-bold text-slate-200">{name}</h3>
      <span className={`text-[10px] px-2 py-0.5 rounded-full uppercase ${
        status === 'Active' ? 'bg-green-500/20 text-green-400' : 'bg-slate-700 text-slate-400'
      }`}>{status}</span>
    </div>
    <div className="mt-3 text-xs text-slate-500 flex items-center">
      <div className="w-full bg-slate-700 h-1 rounded-full mr-2">
        <div className="bg-blue-500 h-1 rounded-full" style={{width: `${count * 10}%`}}></div>
      </div>
      {count} Tasks
    </div>
  </div>
);

const App = () => {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSignals = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/signals');
        const data = await response.json();
        setSignals(data);
        setLoading(false);
      } catch (error) {
        console.error("Error fetching signals:", error);
        setLoading(false);
      }
    };
    fetchSignals();
  }, []);

  return (
    <div className="min-h-screen bg-[#0b0f1a] text-slate-300 flex">
      {/* Sidebar */}
      <aside className="w-72 border-r border-slate-800/60 p-6 bg-[#0d121f]">
        <div className="flex items-center gap-3 mb-10">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-white">JT</div>
          <span className="font-bold text-xl tracking-tight text-white">ORCHESTRA</span>
        </div>
        
        <nav className="mb-10">
          <div className="text-slate-500 text-[10px] uppercase font-bold tracking-widest mb-4">Trading Projects</div>
          <ProjectItem name="HK Tech Momentum" status="Active" count={12} active />
          <ProjectItem name="Sentiment Arbitrage" status="Paused" count={4} />
          <ProjectItem name="Prophet Alpha" status="Idle" count={0} />
          <button className="w-full mt-4 py-2 border border-dashed border-slate-700 rounded-xl text-slate-500 text-sm hover:text-blue-400 hover:border-blue-500/50 transition-all">
            + New Workspace
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <header className="h-20 border-b border-slate-800/60 flex items-center justify-between px-10 bg-[#0d121f]/50 backdrop-blur-md sticky top-0 z-10">
          <div>
            <h2 className="text-lg font-bold text-white">HK Tech Momentum</h2>
            <p className="text-xs text-slate-500">Last updated: Just now</p>
          </div>
          <div className="flex gap-4">
            <button className="bg-blue-600 hover:bg-blue-500 text-white px-5 py-2 rounded-lg text-sm font-bold transition-all shadow-lg shadow-blue-900/20">
              Run Orchestrator
            </button>
          </div>
        </header>

        <div className="p-10 max-w-6xl mx-auto">
          {/* Stats Grid */}
          <div className="grid grid-cols-4 gap-4 mb-10">
            <StatCard label="Total Universe" value="48 Stocks" color="text-white" />
            <StatCard label="Avg Confidence" value="0.42" color="text-blue-400" />
            <StatCard label="Buy Signals" value="8" color="text-green-400" />
            <StatCard label="Azure Cost (Est)" value="$0.14" color="text-slate-400" />
          </div>

          {/* Table Area */}
          <div className="bg-[#121826] rounded-2xl border border-slate-800/60 shadow-2xl overflow-hidden">
            <div className="p-6 border-b border-slate-800/60 flex justify-between items-center">
              <h3 className="font-bold text-white">Real-time Signals</h3>
              <div className="flex gap-2">
                <span className="px-2 py-1 bg-slate-800 rounded text-[10px] font-bold">CSV EXPORT</span>
              </div>
            </div>
            <table className="w-full text-left">
              <thead>
                <tr className="bg-slate-900/50 text-[10px] uppercase tracking-widest text-slate-500 font-bold border-b border-slate-800/60">
                  <th className="p-4 pl-6">Ticker</th>
                  <th className="p-4 text-center">Prophet</th>
                  <th className="p-4 text-center">Sentiment</th>
                  <th className="p-4 text-center">Alpha</th>
                  <th className="p-4 text-right pr-6">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-sm">
                {loading ? (
                  <tr><td colSpan="5" className="p-10 text-center text-slate-500 animate-pulse">Running Model Orchestrator...</td></tr>
                ) : signals.map((s) => (
                  <tr key={s.ticker} className="hover:bg-blue-600/5 transition-colors">
                    <td className="p-4 pl-6 font-bold text-slate-200">{s.ticker}</td>
                    <td className={`p-4 text-center ${s.ts_signal > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {s.ts_signal > 0 ? '+' : ''}{s.ts_signal?.toFixed(2)}
                    </td>
                    <td className={`p-4 text-center ${s.sent_signal > 0 ? 'text-blue-400' : 'text-slate-500'}`}>
                      {s.sent_signal > 0 ? '+' : ''}{s.sent_signal?.toFixed(2)}
                    </td>
                    <td className={`p-4 text-center ${s.alpha_signal > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {s.alpha_signal > 0 ? '+' : ''}{s.alpha_signal?.toFixed(2)}
                    </td>
                    <td className="p-4 text-right pr-6">
                      <span className={`px-3 py-1 rounded-lg font-bold ${
                        s.final_score > 0.3 ? 'bg-green-500/20 text-green-400 border border-green-500/20' : 
                        'bg-slate-800 text-slate-400'
                      }`}>
                        {s.final_score?.toFixed(2)}
                      </span>
                    </td>
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
