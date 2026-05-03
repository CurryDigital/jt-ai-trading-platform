import React, { useState, useEffect } from 'react';
import { IbkrGatewayTester } from './IbkrGatewayTester';
import { AuditLog } from './AuditLog';

// Enhanced Settings Tab with Configuration Management
export const SettingsTab = () => {
  const [activeSection, setActiveSection] = useState('ibkr'); // ibkr, trading, sync, display, data
  const [syncStatus, setSyncStatus] = useState({});
  const [platformSettings, setPlatformSettings] = useState({
    defaultCapital: 100000,
    maxPositionsPerStrategy: 4,
    tradeSizePercent: 25,
    autoRefreshInterval: 30,
    priceAlerts: true,
    emailNotifications: false
  });
  const [executionMode, setExecutionMode] = useState('SIMULATION');
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [resetConfirm, setResetConfirm] = useState(false);
  const [dataSources, setDataSources] = useState(null);
  const [dataSourcesLoading, setDataSourcesLoading] = useState(false);

  useEffect(() => {
    fetchSettings();
    fetchSyncStatus();
    fetchExecutionMode();
    fetchDataSources();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await fetch('/api/settings');
      if (res.ok) {
        const data = await res.json();
        setPlatformSettings(prev => ({ ...prev, ...data }));
      }
    } catch (e) { console.error('Failed to fetch settings:', e); }
  };

  const fetchSyncStatus = async () => {
    try {
      const res = await fetch('/api/sync/status');
      if (res.ok) {
        const data = await res.json();
        setSyncStatus(data);
      }
    } catch (e) { console.error('Failed to fetch sync status:', e); }
  };

  const fetchExecutionMode = async () => {
    try {
      const res = await fetch('/api/execution/global-mode');
      if (res.ok) {
        const data = await res.json();
        setExecutionMode(data.execution_mode);
      }
    } catch (e) { console.error('Failed to fetch execution mode:', e); }
  };

  const fetchDataSources = async () => {
    setDataSourcesLoading(true);
    try {
      const res = await fetch('/api/settings/data-sources');
      if (res.ok) {
        const data = await res.json();
        setDataSources(data);
      }
    } catch (e) { console.error('Failed to fetch data sources:', e); }
    finally { setDataSourcesLoading(false); }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(platformSettings)
      });
    } catch (e) { console.error('Failed to save settings:', e); }
    finally { setSaving(false); }
  };

  const resetSimulation = async () => {
    setResetting(true);
    try {
      // Call API to reset all paper strategies and trades
      const res = await fetch('/api/simulation/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (res.ok) {
        const data = await res.json();
        alert(`✅ Simulation reset complete!\n\n${data.message || 'All positions and trades cleared.'}`);
        setResetConfirm(false);
        // Refresh the page to show updated state
        window.location.reload();
      } else {
        const error = await res.json();
        alert(`❌ Reset failed: ${error.detail || 'Unknown error'}`);
      }
    } catch (e) { 
      console.error('Failed to reset simulation:', e);
      alert('❌ Network error during reset');
    }
    finally { setResetting(false); }
  };

  const sections = [
    { id: 'ibkr', label: '🔗 IBKR Connection', icon: '🔗' },
    { id: 'trading', label: '💰 Trading Config', icon: '💰' },
    { id: 'sync', label: '🔄 Data Sync', icon: '🔄' },
    { id: 'data', label: '📊 Data Sources', icon: '📊' },
    { id: 'audit', label: '🛡️ Audit Log', icon: '🛡️' },
    { id: 'display', label: '🎨 Display', icon: '🎨' },
  ];

  const syncComponents = [
    { id: 'stocks', label: 'Stocks', icon: '📈' },
    { id: 'fx', label: 'FX', icon: '💱' },
    { id: 'crypto', label: 'Crypto', icon: '₿' },
    { id: 'commodities', label: 'Commodities', icon: '🥇' },
    { id: 'earnings', label: 'Earnings', icon: '📊' },
    { id: 'consensus', label: 'Analyst Ratings', icon: '⭐' },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-500 max-w-5xl">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-black text-white">Platform Settings</h2>
        <button
          onClick={saveSettings}
          disabled={saving}
          className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 text-white text-sm font-bold rounded-lg"
        >
          {saving ? 'Saving...' : '💾 Save Changes'}
        </button>
      </div>

      {/* Section Tabs */}
      <div className="flex items-center gap-2 p-1 rounded-xl bg-slate-900/50 border border-white/5">
        {sections.map(section => (
          <button
            key={section.id}
            onClick={() => setActiveSection(section.id)}
            className={`flex-1 px-4 py-2.5 rounded-lg text-xs font-bold transition-all ${
              activeSection === section.id
                ? 'bg-blue-500 text-white shadow-lg'
                : 'text-slate-400 hover:text-white hover:bg-white/5'
            }`}
          >
            {section.label}
          </button>
        ))}
      </div>

      {/* IBKR CONNECTION */}
      {activeSection === 'ibkr' && (
        <div className="space-y-4">
          <IbkrGatewayTester />
        </div>
      )}

      {/* TRADING CONFIGURATION */}
      {activeSection === 'trading' && (
        <div className="space-y-4">
          {/* Execution Mode Warning */}
          <div className={`p-4 rounded-xl border ${
            executionMode === 'LIVE_TRADING' 
              ? 'bg-rose-500/10 border-rose-500/30' :
            executionMode === 'PAPER_TRADING'
              ? 'bg-amber-500/10 border-amber-500/30'
              : 'bg-emerald-500/10 border-emerald-500/30'
          }`}>
            <div className="flex items-center gap-3">
              <span className="text-2xl">
                {executionMode === 'LIVE_TRADING' ? '💰' : 
                 executionMode === 'PAPER_TRADING' ? '📝' : '🧪'}
              </span>
              <div>
                <h3 className="text-sm font-bold text-white">
                  Current Mode: {executionMode.replaceAll('_', ' ')}
                </h3>
                <p className="text-xs text-slate-400">
                  {executionMode === 'LIVE_TRADING' 
                    ? '⚠️ WARNING: Real money at risk! All trades will execute on live IBKR account.' :
                   executionMode === 'PAPER_TRADING'
                    ? 'Trades execute on IBKR paper account for testing.'
                    : 'Trades are simulated only - no real orders placed.'}
                </p>
              </div>
            </div>
          </div>

          {/* Capital Settings */}
          <div className="p-6 rounded-xl bg-slate-900/50 border border-white/10">
            <h3 className="text-sm font-black text-white uppercase tracking-wider mb-4">Capital Allocation</h3>
            
            <div className="space-y-4">
              <div>
                <label className="text-xs text-slate-400 block mb-2">Default Capital Pool per Strategy</label>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="10000"
                    max="2000000"
                    step="10000"
                    value={platformSettings.defaultCapital}
                    onChange={(e) => setPlatformSettings({...platformSettings, defaultCapital: Number(e.target.value)})}
                    className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                  />
                  <span className="text-sm font-bold text-white w-24 text-right">
                    ${platformSettings.defaultCapital.toLocaleString()}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1">Default pool size when deploying new strategies</p>
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-2">Trade Size (% of Pool)</label>
                <div className="flex items-center gap-3">
                  <input
                    type="range"
                    min="10"
                    max="50"
                    step="5"
                    value={platformSettings.tradeSizePercent}
                    onChange={(e) => setPlatformSettings({...platformSettings, tradeSizePercent: Number(e.target.value)})}
                    className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                  />
                  <span className="text-sm font-bold text-white w-16 text-right">
                    {platformSettings.tradeSizePercent}%
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Each position uses {platformSettings.tradeSizePercent}% of the strategy's capital pool
                </p>
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-2">Max Positions per Strategy</label>
                <div className="flex items-center gap-2">
                  {[2, 3, 4, 5, 6].map(num => (
                    <button
                      key={num}
                      onClick={() => setPlatformSettings({...platformSettings, maxPositionsPerStrategy: num})}
                      className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                        platformSettings.maxPositionsPerStrategy === num
                          ? 'bg-blue-500 text-white'
                          : 'bg-slate-800 text-slate-400 hover:text-white'
                      }`}
                    >
                      {num}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Risk Settings */}
          <div className="p-6 rounded-xl bg-slate-900/50 border border-white/10">
            <h3 className="text-sm font-black text-white uppercase tracking-wider mb-4">Risk Management</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                <div>
                  <span className="text-sm font-medium text-white">Price Alerts</span>
                  <p className="text-xs text-slate-500">Notify on significant price moves</p>
                </div>
                <button
                  onClick={() => setPlatformSettings({...platformSettings, priceAlerts: !platformSettings.priceAlerts})}
                  className={`w-12 h-6 rounded-full transition-all ${
                    platformSettings.priceAlerts ? 'bg-emerald-500' : 'bg-slate-700'
                  }`}
                >
                    <div className={`w-5 h-5 rounded-full bg-white transition-all ${
                      platformSettings.priceAlerts ? 'translate-x-6' : 'translate-x-0.5'
                    }`} />
                </button>
              </div>

              <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                <div>
                  <span className="text-sm font-medium text-white">Email Notifications</span>
                  <p className="text-xs text-slate-500">Send trade alerts via email</p>
                </div>
                <button
                  onClick={() => setPlatformSettings({...platformSettings, emailNotifications: !platformSettings.emailNotifications})}
                  className={`w-12 h-6 rounded-full transition-all ${
                    platformSettings.emailNotifications ? 'bg-emerald-500' : 'bg-slate-700'
                  }`}
                >
                    <div className={`w-5 h-5 rounded-full bg-white transition-all ${
                      platformSettings.emailNotifications ? 'translate-x-6' : 'translate-x-0.5'
                    }`} />
                </button>
              </div>
            </div>
          </div>

          {/* SIMULATION RESET - Only show in SIMULATION mode */}
          {executionMode === 'SIMULATION' && (
            <div className="p-6 rounded-xl bg-rose-900/20 border border-rose-500/30">
              <h3 className="text-sm font-black text-rose-400 uppercase tracking-wider mb-4">⚠️ Simulation Reset</h3>
              
              <p className="text-xs text-slate-400 mb-4">
                Reset all simulation data. This will:
              </p>
              <ul className="text-xs text-slate-400 mb-4 space-y-1 list-disc list-inside">
                <li>Delete all paper trading positions</li>
                <li>Clear all trade history</li>
                <li>Reset simulation capital to default ($100,000)</li>
                <li>Remove all P&L data</li>
              </ul>
              
              {!resetConfirm ? (
                <button
                  onClick={() => setResetConfirm(true)}
                  className="px-4 py-2 bg-rose-500/20 text-rose-400 hover:bg-rose-500/30 border border-rose-500/50 rounded-lg text-sm font-bold transition-all"
                >
                  🗑️ Reset Simulation Data
                </button>
              ) : (
                <div className="flex items-center gap-3">
                  <span className="text-xs text-rose-400 font-bold">Are you sure? This cannot be undone.</span>
                  <button
                    onClick={resetSimulation}
                    disabled={resetting}
                    className="px-4 py-2 bg-rose-500 hover:bg-rose-400 disabled:bg-slate-700 text-white text-sm font-bold rounded-lg transition-all"
                  >
                    {resetting ? 'Resetting...' : '✅ Yes, Reset Everything'}
                  </button>
                  <button
                    onClick={() => setResetConfirm(false)}
                    disabled={resetting}
                    className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm font-bold rounded-lg transition-all"
                  >
                    Cancel
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* DATA SYNC */}
      {activeSection === 'sync' && (
        <div className="space-y-4">
          <div className="p-6 rounded-xl bg-slate-900/50 border border-white/10">
            <h3 className="text-sm font-black text-white uppercase tracking-wider mb-4">Data Synchronization Status</h3>
            
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {syncComponents.map(comp => {
                const status = syncStatus[comp.id] || { last_sync: null, status: 'unknown' };
                const isRecent = status.last_sync && (new Date() - new Date(status.last_sync)) < 3600000; // 1 hour
                
                return (
                  <div key={comp.id} className="p-4 rounded-lg bg-slate-800/50 border border-white/5">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg">{comp.icon}</span>
                      <span className="text-sm font-bold text-white">{comp.label}</span>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        isRecent ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
                      }`} />
                      <span className="text-xs text-slate-400">
                        {status.last_sync 
                          ? new Date(status.last_sync).toLocaleTimeString()
                          : 'Never synced'
                        }
                      </span>
                    </div>
                    
                    <button
                      onClick={() => fetch('/api/sync/' + comp.id, { method: 'POST' })}
                      className="mt-3 w-full py-1.5 text-xs bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 rounded"
                    >
                      🔄 Sync Now
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="p-6 rounded-xl bg-slate-900/50 border border-white/10">
            <h3 className="text-sm font-black text-white uppercase tracking-wider mb-4">Auto Refresh Settings</h3>
            
            <div>
              <label className="text-xs text-slate-400 block mb-2">Dashboard Refresh Interval (seconds)</label>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="10"
                  max="300"
                  step="10"
                  value={platformSettings.autoRefreshInterval}
                  onChange={(e) => setPlatformSettings({...platformSettings, autoRefreshInterval: Number(e.target.value)})}
                  className="flex-1 h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
                <span className="text-sm font-bold text-white w-16 text-right">
                  {platformSettings.autoRefreshInterval}s
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* DATA SOURCES */}
      {activeSection === 'data' && (
        <div className="space-y-4">
          {/* IBKR Connection Status */}
          <div className={`p-6 rounded-xl border ${
            dataSources?.ibkr_connected 
              ? 'bg-emerald-900/20 border-emerald-500/30' 
              : 'bg-amber-900/20 border-amber-500/30'
          }`}>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-black text-white uppercase tracking-wider">
                  IBKR Gateway Status
                </h3>
                <p className="text-xs text-slate-400 mt-1">
                  {dataSources?.ibkr_connected 
                    ? `Connected to ${dataSources?.ibkr_host}:${dataSources?.ibkr_port} (${dataSources?.ibkr_mode})`
                    : 'Disconnected - Using Yahoo Finance fallback'
                  }
                </p>
              </div>
              <div className={`px-3 py-1.5 rounded-lg text-xs font-bold ${
                dataSources?.ibkr_connected 
                  ? 'bg-emerald-500/20 text-emerald-400' 
                  : 'bg-amber-500/20 text-amber-400'
              }`}>
                {dataSources?.ibkr_connected ? '🟢 Connected' : '🟡 Disconnected'}
              </div>
            </div>
          </div>

          {/* Summary Stats */}
          {dataSources?.summary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 bg-slate-900/50 border border-white/10 rounded-xl text-center">
                <span className="text-2xl font-bold text-white">{dataSources.summary.total_feeds}</span>
                <span className="text-xs text-slate-500 block">Total Feeds</span>
              </div>
              <div className="p-4 bg-slate-900/50 border border-white/10 rounded-xl text-center">
                <span className="text-2xl font-bold text-blue-400">{dataSources.summary.ibkr_primary}</span>
                <span className="text-xs text-slate-500 block">IBKR Primary</span>
              </div>
              <div className="p-4 bg-slate-900/50 border border-white/10 rounded-xl text-center">
                <span className="text-2xl font-bold text-purple-400">{dataSources.summary.yahoo_primary}</span>
                <span className="text-xs text-slate-500 block">Yahoo Primary</span>
              </div>
              <div className="p-4 bg-slate-900/50 border border-white/10 rounded-xl text-center">
                <span className="text-2xl font-bold text-emerald-400">{dataSources.summary.database_primary}</span>
                <span className="text-xs text-slate-500 block">Database</span>
              </div>
            </div>
          )}

          {/* Data Sources Table */}
          <div className="p-6 rounded-xl bg-slate-900/50 border border-white/10">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-black text-white uppercase tracking-wider">
                Data Source Breakdown
              </h3>
              <button 
                onClick={fetchDataSources}
                disabled={dataSourcesLoading}
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                {dataSourcesLoading ? 'Refreshing...' : '🔄 Refresh'}
              </button>
            </div>
            
            {dataSourcesLoading ? (
              <div className="h-32 flex items-center justify-center text-slate-500">
                Loading data sources...
              </div>
            ) : dataSources?.data_sources ? (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-[10px] text-slate-500 uppercase border-b border-white/10">
                      <th className="text-left py-2">Category</th>
                      <th className="text-left py-2">Data Type</th>
                      <th className="text-left py-2">Primary Source</th>
                      <th className="text-left py-2">Frequency</th>
                      <th className="text-center py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {dataSources.data_sources.map((ds, idx) => (
                      <tr key={idx} className="text-xs">
                        <td className="py-3 text-slate-400">{ds.category}</td>
                        <td className="py-3 text-white font-medium">{ds.data_type}</td>
                        <td className="py-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            ds.primary_source === 'IBKR' ? 'bg-blue-500/20 text-blue-400' :
                            ds.primary_source === 'Yahoo Finance' ? 'bg-purple-500/20 text-purple-400' :
                            ds.primary_source === 'Database (calculated)' ? 'bg-emerald-500/20 text-emerald-400' :
                            'bg-slate-500/20 text-slate-400'
                          }`}>
                            {ds.primary_source}
                          </span>
                        </td>
                        <td className="py-3 text-slate-400">{ds.frequency}</td>
                        <td className="py-3 text-center">
                          <span className={`text-[10px] ${
                            ds.status?.includes('✅') ? 'text-emerald-400' :
                            ds.status?.includes('⚠️') ? 'text-amber-400' :
                            ds.status?.includes('❌') ? 'text-rose-400' :
                            'text-slate-400'
                          }`}>
                            {ds.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center text-slate-500">
                No data source information available
              </div>
            )}
          </div>

          {/* Data Source Legend */}
          <div className="p-4 bg-slate-900/50 border border-white/10 rounded-xl">
            <h4 className="text-xs font-bold text-slate-500 uppercase mb-3">Source Legend</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                <span className="text-slate-400">IBKR - Real-time market data</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                <span className="text-slate-400">Yahoo - Delayed/backup data</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span className="text-slate-400">Database - Calculated analytics</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                <span className="text-slate-400">FMP - Fundamental data</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AUDIT LOG */}
      {activeSection === 'audit' && (
        <div className="space-y-4">
          <AuditLog />
        </div>
      )}

      {/* DISPLAY SETTINGS */}
      {activeSection === 'display' && (
        <div className="space-y-4">
          <div className="p-6 rounded-xl bg-slate-900/50 border border-white/10">
            <h3 className="text-sm font-black text-white uppercase tracking-wider mb-4">Display Preferences</h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                <div>
                  <span className="text-sm font-medium text-white">Compact Mode</span>
                  <p className="text-xs text-slate-500">Show more data in less space</p>
                </div>
                <button className="w-12 h-6 rounded-full bg-slate-700">
                  <div className="w-5 h-5 rounded-full bg-white translate-x-0.5" />
                </button>
              </div>

              <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                <div>
                  <span className="text-sm font-medium text-white">Show P&L in Header</span>
                  <p className="text-xs text-slate-500">Always display total P&L in top bar</p>
                </div>
                <button className="w-12 h-6 rounded-full bg-emerald-500">
                  <div className="w-5 h-5 rounded-full bg-white translate-x-6" />
                </button>
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-2">Number Format</label>
                <div className="flex gap-2">
                  {['1,000.00', '1 000,00', '1000.00'].map(format => (
                    <button
                      key={format}
                      className="px-4 py-2 bg-slate-800 text-slate-400 rounded-lg text-sm hover:text-white"
                    >
                      {format}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-400 block mb-2">Timezone</label>
                <select className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-white">
                  <option>UTC</option>
                  <option>Hong Kong (HKT)</option>
                  <option>New York (EST)</option>
                  <option>London (GMT)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Platform Info */}
          <div className="p-6 rounded-xl bg-slate-900/50 border border-white/10">
            <h3 className="text-sm font-black text-white uppercase tracking-wider mb-4">Platform Information</h3>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-slate-500 block">Version</span>
                <span className="text-white">v3.0 Quant Edition</span>
              </div>
              <div>
                <span className="text-slate-500 block">Build Date</span>
                <span className="text-white">2026-02-19</span>
              </div>
              <div>
                <span className="text-slate-500 block">Total Strategies</span>
                <span className="text-white">22 JT-Ready</span>
              </div>
              <div>
                <span className="text-slate-500 block">Database</span>
                <span className="text-white">PostgreSQL (Gold Schema)</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SettingsTab;
