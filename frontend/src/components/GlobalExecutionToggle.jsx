import React, { useState, useEffect, useRef } from 'react';

/**
 * Global Execution Mode Toggle
 * Platform-wide setting for SIMULATION / PAPER_TRADING / LIVE_TRADING
 */
export const GlobalExecutionToggle = () => {
  const [mode, setMode] = useState('SIMULATION');
  const [simCapital, setSimCapital] = useState(100000);
  const [simUsed, setSimUsed] = useState(0);
  const [simAvailable, setSimAvailable] = useState(100000);
  const [simPositions, setSimPositions] = useState(0);
  const [ibkrBalance, setIbkrBalance] = useState(null);
  const [ibkrCurrency, setIbkrCurrency] = useState('USD');
  const [ibkrBalanceUSD, setIbkrBalanceUSD] = useState(null);
  const [ibkrConnected, setIbkrConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [message, setMessage] = useState(null);
  const configRef = useRef(null);

  useEffect(() => {
    fetchGlobalMode();
    // Refresh every 60 seconds (reduced from 30 to minimize API calls)
    const interval = setInterval(fetchGlobalMode, 60000);
    return () => clearInterval(interval);
  }, []);

  // Handle click outside to close config panel
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (configRef.current && !configRef.current.contains(event.target)) {
        setShowConfig(false);
      }
    };
    
    if (showConfig) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showConfig]);

  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  const fetchGlobalMode = async () => {
    try {
      const res = await fetch('/api/execution/global-mode');
      if (res.ok) {
        const data = await res.json();
        setMode(data.execution_mode);
        setSimCapital(data.simulation_capital || 100000);
        // Track simulation balance
        setSimUsed(data.simulation_used || 0);
        setSimAvailable(data.simulation_available || (data.simulation_capital || 100000));
        setSimPositions(data.simulation_positions || 0);
        // Fix: Check for null/undefined, not falsy (0 is valid)
        if (data.account_balance !== null && data.account_balance !== undefined) {
          setIbkrBalance(data.account_balance);
        }
        // Store IBKR connection status
        setIbkrConnected(data.ibkr_connected || false);
        // Store currency info
        if (data.account_currency) {
          setIbkrCurrency(data.account_currency);
        }
        if (data.account_balance_usd !== null && data.account_balance_usd !== undefined) {
          setIbkrBalanceUSD(data.account_balance_usd);
        }
      }
    } catch (e) {
      console.error('Failed to fetch global mode:', e);
    }
  };

  const updateMode = async (newMode) => {
    if (newMode === mode || loading) return;
    
    setLoading(true);
    setMessage('Switching...');
    
    try {
      const res = await fetch('/api/execution/global-mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          execution_mode: newMode,
          simulation_capital: simCapital
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setMode(data.execution_mode);
        // Update simulation balance states when switching modes
        setSimUsed(data.simulation_used || 0);
        setSimAvailable(data.simulation_available || (data.simulation_capital || 100000));
        setSimPositions(data.simulation_positions || 0);
        // Fix: Check for null/undefined, not falsy (0 is valid)
        if (data.account_balance !== null && data.account_balance !== undefined) {
          setIbkrBalance(data.account_balance);
        }
        if (data.account_currency) {
          setIbkrCurrency(data.account_currency);
        }
        if (data.account_balance_usd !== null && data.account_balance_usd !== undefined) {
          setIbkrBalanceUSD(data.account_balance_usd);
        }
        setIbkrConnected(data.ibkr_connected || false);
        setMessage(`Switched to ${newMode.replace('_', ' ')}`);
        // Don't close config panel immediately so user sees the change
        setTimeout(() => setShowConfig(false), 800);
      } else {
        const err = await res.json();
        setMessage(err.detail || 'Failed to switch mode');
      }
    } catch (e) {
      console.error('Failed to update mode:', e);
      setMessage('Failed to switch mode');
    } finally {
      setLoading(false);
    }
  };

  const updateSimCapital = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/execution/global-mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          execution_mode: mode,
          simulation_capital: parseFloat(simCapital)
        })
      });
      
      if (res.ok) {
        setShowConfig(false);
      }
    } catch (e) {
      console.error('Failed to update capital:', e);
    } finally {
      setLoading(false);
    }
  };

  const getModeColor = (m) => {
    switch(m) {
      case 'SIMULATION': return 'bg-emerald-500';
      case 'PAPER_TRADING': return 'bg-amber-500';
      case 'LIVE_TRADING': return 'bg-rose-500';
      default: return 'bg-slate-500';
    }
  };

  const getModeBorder = (m) => {
    switch(m) {
      case 'SIMULATION': return 'border-emerald-500/50';
      case 'PAPER_TRADING': return 'border-amber-500/50';
      case 'LIVE_TRADING': return 'border-rose-500/50';
      default: return 'border-slate-500/50';
    }
  };

  return (
    <div className="relative">
      {/* Main Toggle Button */}
      <div 
        className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${getModeBorder(mode)} bg-slate-900/80 backdrop-blur cursor-pointer hover:bg-slate-800 transition-all ${loading ? 'opacity-75' : ''}`}
        onClick={() => !loading && setShowConfig(!showConfig)}
      >
        {/* Status Dot */}
        <div className={`w-2 h-2 rounded-full ${getModeColor(mode)} ${loading ? '' : 'animate-pulse'}`} />
        
        {loading && (
          <svg className="animate-spin h-3 w-3 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        )}
        
        {/* Mode Label */}
        <div className="flex flex-col">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">Mode</span>
          <span className={`text-xs font-bold ${
            mode === 'SIMULATION' ? 'text-emerald-400' :
            mode === 'PAPER_TRADING' ? 'text-amber-400' :
            'text-rose-400'
          }`}>
            {mode === 'SIMULATION' && '🧪 Sim'}
            {mode === 'PAPER_TRADING' && '📝 Paper'}
            {mode === 'LIVE_TRADING' && '💰 LIVE'}
          </span>
        </div>
        
        {/* Capital Indicator */}
        <div className="flex flex-col ml-2 pl-2 border-l border-white/10">
          <span className="text-[10px] text-slate-400">Capital</span>
          <span className="text-xs font-bold text-white">
            {mode === 'SIMULATION' 
              ? `$${(simAvailable / 1000).toFixed(0)}k` 
              : ibkrBalance 
                ? ibkrCurrency === 'HKD' 
                  ? `HK$${(ibkrBalance / 1000).toFixed(0)}k`
                  : `$${(ibkrBalance / 1000).toFixed(0)}k`
                : 'IBKR'
            }
          </span>
          {mode === 'SIMULATION' && simUsed > 0 && (
            <span className="text-[8px] text-slate-500">
              ${(simUsed / 1000).toFixed(0)}k used
            </span>
          )}
          {ibkrCurrency === 'HKD' && ibkrBalanceUSD && (
            <span className="text-[8px] text-slate-500">
              ~${(ibkrBalanceUSD / 1000).toFixed(0)}k USD
            </span>
          )}
        </div>
        
        {/* Dropdown Arrow */}
        <svg 
          className={`w-4 h-4 text-slate-400 ml-1 transition-transform ${showConfig ? 'rotate-180' : ''}`}
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </div>

      {/* Config Panel */}
      {showConfig && (
        <div 
          ref={configRef}
          className="absolute top-full right-0 mt-2 w-80 bg-slate-900 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden"
        >
          <div className="p-4 border-b border-white/10">
            <h3 className="text-sm font-bold text-white">Execution Mode</h3>
            <p className="text-xs text-slate-400 mt-1">Choose how trades are executed</p>
          </div>

          <div className="p-4 space-y-3">
            {/* Mode Selection */}
            {[
              { key: 'SIMULATION', label: 'Simulation', icon: '🧪', color: 'emerald', risk: 'Zero Risk' },
              { key: 'PAPER_TRADING', label: 'Paper Trading', icon: '📝', color: 'amber', risk: 'Fake Money' },
              { key: 'LIVE_TRADING', label: 'LIVE Trading', icon: '💰', color: 'rose', risk: 'REAL MONEY' }
            ].map((m) => (
                <button
                key={m.key}
                onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  if (mode !== m.key && !loading) {
                    updateMode(m.key);
                  }
                }}
                disabled={loading}
                className={`w-full p-3 rounded-lg border text-left transition-all ${
                  mode === m.key
                    ? `bg-${m.color}-500/20 border-${m.color}-500 ring-1 ring-${m.color}-500`
                    : 'bg-slate-800 border-white/5 hover:border-white/20'
                } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">{m.icon}</span>
                  <div className="flex-1">
                    <div className={`text-sm font-bold ${mode === m.key ? `text-${m.color}-400` : 'text-white'}`}>
                      {m.label}
                    </div>
                    <div className="text-[10px] text-slate-400">{m.risk}</div>
                  </div>
                  {mode === m.key && (
                    <div className={`w-2 h-2 rounded-full bg-${m.color}-500`} />
                  )}
                </div>
              </button>
            ))}

            {/* Simulation Capital Config */}
            {mode === 'SIMULATION' && (
              <div className="mt-4 p-3 bg-slate-800/50 rounded-lg">
                <label className="text-xs text-slate-400 block mb-2">Simulation Capital</label>
                
                {/* Balance Breakdown */}
                <div className="grid grid-cols-3 gap-2 mb-3">
                  <div className="text-center p-2 bg-slate-900/50 rounded">
                    <span className="text-[10px] text-slate-500 block">Total</span>
                    <span className="text-sm font-bold text-white">${(simCapital/1000).toFixed(0)}k</span>
                  </div>
                  <div className="text-center p-2 bg-slate-900/50 rounded">
                    <span className="text-[10px] text-slate-500 block">Used</span>
                    <span className="text-sm font-bold text-amber-400">${(simUsed/1000).toFixed(0)}k</span>
                  </div>
                  <div className="text-center p-2 bg-slate-900/50 rounded">
                    <span className="text-[10px] text-slate-500 block">Available</span>
                    <span className="text-sm font-bold text-emerald-400">${(simAvailable/1000).toFixed(0)}k</span>
                  </div>
                </div>
                
                {simPositions > 0 && (
                  <p className="text-[10px] text-slate-400 mb-2">
                    {simPositions} active position{simPositions !== 1 ? 's' : ''} using ${simUsed.toLocaleString()}
                  </p>
                )}
                
                <div className="flex gap-2">
                  <input
                    type="number"
                    value={simCapital}
                    onChange={(e) => setSimCapital(e.target.value)}
                    className="flex-1 bg-slate-900 border border-white/10 rounded px-3 py-2 text-sm text-white"
                    min="0"
                    step="1000"
                  />
                  <button
                    onClick={updateSimCapital}
                    disabled={loading}
                    className="px-3 py-2 bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 text-white text-xs font-bold rounded"
                  >
                    Save
                  </button>
                </div>
                <p className="text-[10px] text-slate-500 mt-2">Total simulation account balance</p>
              </div>
            )}

            {/* IBKR Info for Paper/Live */}
            {mode !== 'SIMULATION' && (
              <div className="mt-4 p-3 bg-slate-800/50 rounded-lg">
                <label className="text-xs text-slate-400 block mb-1">IBKR Account Balance</label>
                <div className="text-lg font-bold text-white">
                  {!ibkrConnected
                    ? 'Not Connected'
                    : ibkrBalance !== null
                      ? ibkrCurrency === 'HKD'
                        ? `HK$${ibkrBalance.toLocaleString()}`
                        : `$${ibkrBalance.toLocaleString()}`
                      : 'Checking...'
                  }
                </div>
                {ibkrCurrency === 'HKD' && ibkrBalanceUSD && ibkrConnected && (
                  <div className="text-sm text-slate-400">
                    ~ ${ibkrBalanceUSD.toLocaleString()} USD
                  </div>
                )}
                <p className="text-[10px] text-slate-500 mt-1">
                  {mode === 'PAPER_TRADING'
                    ? `Fetches from IBKR Paper Account (${ibkrCurrency || 'USD'})`
                    : `Fetches from IBKR Live Account (${ibkrCurrency || 'USD'})`
                  }
                </p>
                {!ibkrConnected && (
                  <p className="text-[10px] text-amber-400 mt-1">
                    ⚠️ TWS/IB Gateway not connected. Start TWS to fetch balance.
                  </p>
                )}
              </div>
            )}

            {/* Live Trading Warning */}
            {mode === 'LIVE_TRADING' && (
              <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-lg">
                <div className="flex items-start gap-2">
                  <span className="text-rose-400">⚠️</span>
                  <div className="text-[10px] text-rose-400">
                    WARNING: All trades will execute with <strong>REAL MONEY</strong> in your live IBKR account.
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Message Toast */}
      {message && (
        <div className="absolute top-full right-0 mt-2 px-4 py-2 bg-blue-500 text-white text-xs font-bold rounded-lg shadow-lg z-50 animate-fade-in">
          {message}
        </div>
      )}
    </div>
  );
};

export default GlobalExecutionToggle;
