import React, { useState, useEffect } from 'react';
import { IbkrGatewayTester } from './IbkrGatewayTester';
import { AuditLog } from './AuditLog';
import { marketClock, marketStatus, fetchWithTimeout } from '../utils';
import { useBarQuality, barQualityView } from '../freshness';

// Enhanced Settings Tab with Configuration Management + System Health
export const SettingsTab = ({ healthData, latencyMs, wsConnected }) => {
  const [activeSection, setActiveSection] = useState('ibkr'); // ibkr, trading, sync, display, data, health
  const [syncStatus, setSyncStatus] = useState({});
  const [platformSettings, setPlatformSettings] = useState({
    defaultCapital: 100000,
    maxPositionsPerStrategy: 4,
    tradeSizePercent: 25,
    autoRefreshInterval: 30,
    priceAlerts: true,
    emailNotifications: false
  });
  const [riskConfig, setRiskConfig] = useState({ max_drawdown: '15', min_sharpe_oos: '0.8', high_turnover: '500', low_trade_count: '20' });
  const [notifConfig, setNotifConfig] = useState({ telegram_token: '', telegram_chat_id: '', fills: true, demotes: true, stalls: true, promotions: false });
  const [saving, setSaving] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [resetConfirm, setResetConfirm] = useState(false);
  const [dataSources, setDataSources] = useState(null);
  const [dataSourcesLoading, setDataSourcesLoading] = useState(false);
  const [clocks, setClocks] = useState(marketClock());
  const [statuses, setStatuses] = useState(marketStatus());
  // Yahoo suspect-bar guard — /api/system/freshness bar_quality section
  // (gold.v_us_equity_bar_quality, qr_etl). Polled alongside data sources.
  const barQ = useBarQuality();
  const bqView = barQualityView(barQ.loaded, barQ.bq);

  useEffect(() => {
    fetchSettings();
    fetchSyncStatus();
    fetchDataSources();
    const id = setInterval(() => {
      setClocks(marketClock());
      setStatuses(marketStatus());
    }, 1000);
    return () => clearInterval(id);
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await fetchWithTimeout('/api/settings');
      if (res.ok) {
        const data = await res.json();
        setPlatformSettings(prev => ({ ...prev, ...(data.trading_config || {}) }));
        setRiskConfig(prev => ({ ...prev, ...(data.risk_config || {}) }));
        setNotifConfig(prev => ({ ...prev, ...(data.notifications || {}) }));
      }
    } catch (e) { console.error('Failed to fetch settings:', e); }
  };

  const putSettingsSection = async (section, payload) => {
    try {
      await fetchWithTimeout(`/api/settings/${section}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }, 15000);
    } catch (e) { console.error(`Failed to save ${section}:`, e); }
  };

  const fetchSyncStatus = async () => {
    try {
      const res = await fetchWithTimeout('/api/sync/status');
      if (res.ok) {
        const data = await res.json();
        setSyncStatus(data);
      }
    } catch (e) { console.error('Failed to fetch sync status:', e); }
  };

  const fetchDataSources = async () => {
    setDataSourcesLoading(true);
    try {
      const res = await fetchWithTimeout('/api/settings/data-sources');
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
      if (activeSection === 'risk') await putSettingsSection('risk_config', riskConfig);
      else if (activeSection === 'notif') await putSettingsSection('notifications', notifConfig);
      else await putSettingsSection('trading_config', platformSettings);
    } catch (e) { console.error('Failed to save settings:', e); }
    finally { setSaving(false); }
  };

  const resetSimulation = async () => {
    setResetting(true);
    try {
      // Call API to reset all paper strategies and trades
      const res = await fetchWithTimeout('/api/simulation/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      }, 30000);
      
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
    { id: 'risk', label: '⚠️ Risk Config', icon: '⚠️' },
    { id: 'notif', label: '🔔 Notifications', icon: '🔔' },
    { id: 'sync', label: '🔄 Data Sync', icon: '🔄' },
    { id: 'data', label: '📊 Data Sources', icon: '📊' },
    { id: 'health', label: '🩺 System Health', icon: '🩺' },
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
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-white">Settings</h2>
          <p className="text-[10px] text-slate-500">System &amp; broker configuration</p>
        </div>
        <button
          onClick={saveSettings}
          disabled={saving}
          className="qr-btn-primary disabled:opacity-40"
        >
          {saving ? 'Saving…' : 'Save Changes'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-[230px_1fr] gap-3 items-start">
        {/* Section nav */}
        <div className="qr-surface-strong overflow-hidden">
          {sections.map(section => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`w-full text-left px-3.5 py-2.5 border-b border-white/[0.04] border-l-2 transition-colors ${
                activeSection === section.id
                  ? 'border-l-blue-500 bg-blue-500/[0.08]'
                  : 'border-l-transparent hover:bg-white/[0.03]'
              }`}
            >
              <div className={`text-[12px] font-semibold ${activeSection === section.id ? 'text-white' : 'text-slate-300'}`}>{section.label}</div>
            </button>
          ))}
        </div>

        {/* Detail panel */}
        <div className="qr-surface-strong overflow-hidden">

      {/* IBKR CONNECTION */}
      {activeSection === 'ibkr' && (
        <div className="space-y-4">
          <IbkrGatewayTester />
        </div>
      )}

      {/* TRADING CONFIGURATION */}
      {activeSection === 'trading' && (
        <div className="space-y-4">
          {/* 4-book model — no global execution mode */}
          <div className="p-4 rounded-xl border bg-slate-500/10 border-slate-500/30">
            <div className="flex items-center gap-3">
              <span className="text-2xl">📚</span>
              <div>
                <h3 className="text-sm font-bold text-white">
                  Per-book execution — no global mode
                </h3>
                <p className="text-xs text-slate-400">
                  Each strategy carries its own book: SIM → PAPER → PAPER UAT (IBKR paper session) → LIVE.
                  Promote/demote from the Strategies pipeline; the Execution tab shows each book separately.
                </p>
              </div>
            </div>
          </div>

          {/* Capital Settings */}
          <div className="qr-surface p-4">
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
          <div className="qr-surface p-4">
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

      {/* RISK CONFIG — promotion & demotion thresholds */}
      {activeSection === 'risk' && (
        <div className="space-y-4">
          <div className="qr-surface p-4">
            <h3 className="text-sm font-black text-white uppercase tracking-wider mb-1">Risk Thresholds</h3>
            <p className="text-xs text-slate-500 mb-4">Breaching any threshold flags a deployed strategy for auto-demotion.</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                ['max_drawdown', 'Max Drawdown (%)'],
                ['min_sharpe_oos', 'Min Sharpe (OOS)'],
                ['high_turnover', 'High Turnover (%/yr)'],
                ['low_trade_count', 'Low Trade Count'],
              ].map(([key, label]) => (
                <div key={key}>
                  <label className="text-xs text-slate-400 block mb-2">{label}</label>
                  <input
                    type="text"
                    value={riskConfig[key]}
                    onChange={(e) => setRiskConfig({ ...riskConfig, [key]: e.target.value })}
                    className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm font-mono text-white"
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* NOTIFICATIONS — Telegram alerts */}
      {activeSection === 'notif' && (
        <div className="space-y-4">
          <div className="qr-surface p-4">
            <h3 className="text-sm font-black text-white uppercase tracking-wider mb-4">Telegram Alerts</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="text-xs text-slate-400 block mb-2">Bot Token</label>
                <input type="password" value={notifConfig.telegram_token}
                  onChange={(e) => setNotifConfig({ ...notifConfig, telegram_token: e.target.value })}
                  className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm font-mono text-white" />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-2">Chat ID</label>
                <input type="text" value={notifConfig.telegram_chat_id}
                  onChange={(e) => setNotifConfig({ ...notifConfig, telegram_chat_id: e.target.value })}
                  className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm font-mono text-white" />
              </div>
            </div>
            <div className="space-y-2">
              {[
                ['fills', 'Order fills', 'Every live execution'],
                ['demotes', 'Auto-demotions', 'Strategy demoted on risk breach'],
                ['stalls', 'Stuck workflows', 'Agent / pipeline stalls'],
                ['promotions', 'Promotions ready', 'Strategy passed all QA gates'],
              ].map(([key, label, hint]) => (
                <div key={key} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                  <div><span className="text-sm font-medium text-white">{label}</span><p className="text-xs text-slate-500">{hint}</p></div>
                  <button
                    onClick={() => setNotifConfig({ ...notifConfig, [key]: !notifConfig[key] })}
                    className={`w-12 h-6 rounded-full transition-all ${notifConfig[key] ? 'bg-emerald-500' : 'bg-slate-700'}`}
                  >
                    <div className={`w-5 h-5 rounded-full bg-white transition-all ${notifConfig[key] ? 'translate-x-6' : 'translate-x-0.5'}`} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* DATA SYNC */}
      {activeSection === 'sync' && (
        <div className="space-y-4">
          <div className="qr-surface p-4">
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
                      onClick={() => fetchWithTimeout('/api/sync/' + comp.id, { method: 'POST' }, 15000)}
                      className="mt-3 w-full py-1.5 text-xs bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 rounded"
                    >
                      🔄 Sync Now
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="qr-surface p-4">
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
              <div className="p-4 qr-surface text-center">
                <span className="text-2xl font-bold text-white">{dataSources.summary.total_feeds}</span>
                <span className="text-xs text-slate-500 block">Total Feeds</span>
              </div>
              <div className="p-4 qr-surface text-center">
                <span className="text-2xl font-bold text-blue-400">{dataSources.summary.ibkr_primary}</span>
                <span className="text-xs text-slate-500 block">IBKR Primary</span>
              </div>
              <div className="p-4 qr-surface text-center">
                <span className="text-2xl font-bold text-purple-400">{dataSources.summary.yahoo_primary}</span>
                <span className="text-xs text-slate-500 block">Yahoo Primary</span>
              </div>
              <div className="p-4 qr-surface text-center">
                <span className="text-2xl font-bold text-emerald-400">{dataSources.summary.database_primary}</span>
                <span className="text-xs text-slate-500 block">Database</span>
              </div>
            </div>
          )}

          {/* Data Sources Table */}
          <div className="qr-surface p-4">
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
                      <th className="text-left py-2">Last Refreshed</th>
                      <th className="text-center py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {dataSources.data_sources.map((ds, idx) => {
                      const lastRefreshed = ds.last_refreshed ? new Date(ds.last_refreshed) : null;
                      const isStale = lastRefreshed && (Date.now() - lastRefreshed.getTime()) > 24 * 60 * 60 * 1000;
                      return (
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
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            {lastRefreshed ? (
                              <>
                                <div className={`w-2 h-2 rounded-full ${isStale ? 'bg-amber-500' : 'bg-emerald-500 animate-pulse'}`} />
                                <span className={`text-[11px] ${isStale ? 'text-amber-400' : 'text-slate-300'}`}>
                                  {lastRefreshed.toLocaleString()}
                                </span>
                              </>
                            ) : (
                              <span className="text-[11px] text-slate-500">—</span>
                            )}
                          </div>
                        </td>
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
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="h-32 flex items-center justify-center text-slate-500">
                No data source information available
              </div>
            )}
          </div>

          {/* ETL Pipeline Freshness (gold.source_freshness) */}
          {dataSources?.freshness && (
            <div className="qr-surface p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-black text-white uppercase tracking-wider">
                  ETL Pipeline Freshness
                </h3>
                <span className="text-[10px] text-slate-500">
                  {dataSources.freshness.filter(f => f.stale).length} stale / {dataSources.freshness.length} sources
                </span>
              </div>
              <div className="overflow-x-auto max-h-96 overflow-y-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-[10px] text-slate-500 uppercase border-b border-white/10">
                      <th className="text-left py-2">Source</th>
                      <th className="text-left py-2">Asset Class</th>
                      <th className="text-left py-2">Max Date</th>
                      <th className="text-left py-2">Last Refreshed</th>
                      <th className="text-right py-2">Age (h)</th>
                      <th className="text-right py-2">Max Stale (h)</th>
                      <th className="text-center py-2">Status</th>
                      <th className="text-left py-2">Last Error</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {dataSources.freshness.map((f, idx) => (
                      <tr key={idx} className="text-xs">
                        <td className="py-2 text-white font-medium">{f.source}</td>
                        <td className="py-2 text-slate-400">{f.asset_class || '—'}</td>
                        <td className="py-2 text-slate-400">{f.max_date || '—'}</td>
                        <td className="py-2 text-slate-300 text-[11px]">
                          {f.last_refreshed_at ? new Date(f.last_refreshed_at).toLocaleString() : 'never'}
                        </td>
                        <td className="py-2 text-right text-slate-400">
                          {f.age_hours != null ? f.age_hours.toFixed(1) : '—'}
                        </td>
                        <td className="py-2 text-right text-slate-400">
                          {f.expected_max_staleness_hours ?? '—'}
                        </td>
                        <td className="py-2 text-center">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            f.stale ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'
                          }`}>
                            {f.stale ? 'STALE' : 'FRESH'}
                          </span>
                        </td>
                        <td className="py-2 text-[11px] text-rose-400 max-w-xs truncate" title={f.last_error || ''}>
                          {f.last_error || ''}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* US Equity Bar Quality (gold.v_us_equity_bar_quality, qr_etl).
              YELLOW = soft warning (self-heal possible), never a hard
              failure. null/missing view → UNKNOWN, never rendered GREEN. */}
          <div className="qr-surface p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-black text-white uppercase tracking-wider">
                US Equity Bar Quality
              </h3>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold bg-white/[0.06] ${bqView.badgeCl}`}
                title={bqView.tip}
              >
                {bqView.level === 'PENDING' ? '…' : bqView.level}
              </span>
            </div>
            {bqView.level === 'PENDING' && (
              <div className="text-[11px] text-slate-600">
                Probe pending — /api/system/freshness has not answered yet.
              </div>
            )}
            {bqView.level === 'UNKNOWN' && (
              <div className="text-[11px] text-slate-500">
                gold.v_us_equity_bar_quality is missing — bar quality cannot be
                determined. Owner: qr_etl (migration
                2026-08-24_us_equity_bar_quality.sql).
              </div>
            )}
            {(bqView.level === 'GREEN' || bqView.level === 'YELLOW') && barQ.bq && (
              <div className="space-y-2 text-xs">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div>
                    <div className="text-[10px] text-slate-500 uppercase">Latest suspect</div>
                    <div className="text-slate-300 font-mono">{barQ.bq.latest_suspect_date || '—'}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500 uppercase">Suspect rows (30d)</div>
                    <div className="text-slate-300 font-mono">{barQ.bq.recent_30d_rows ?? 0}</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500 uppercase">Gold / quarantined (30d)</div>
                    <div className="text-slate-300 font-mono">
                      {barQ.bq.recent_30d_gold_rows ?? 0} / {barQ.bq.recent_30d_quarantined_rows ?? 0}
                    </div>
                  </div>
                  <div>
                    <div className="text-[10px] text-slate-500 uppercase">All-time rows</div>
                    <div className="text-slate-300 font-mono">{barQ.bq.total_rows ?? 0}</div>
                  </div>
                </div>
                {(barQ.bq.recent_30d_tickers || []).length > 0 && (
                  <div className="text-[11px] text-slate-400">
                    Blocking tickers (30d):{' '}
                    <span className="text-slate-200 font-mono">{barQ.bq.recent_30d_tickers.join(', ')}</span>
                    {' '}· {barQ.bq.distinct_tickers ?? 0} tickers all-time
                  </div>
                )}
                <div className="text-[10px] text-slate-600">
                  {bqView.level === 'YELLOW'
                    ? 'Soft warning — unresolved Yahoo synthetic zero-volume flat-bar suspects in the last 30d; episodes can self-heal as Yahoo backfills real bars (EA 2026-08-05..10 did). Quarantined rows live in bronze.yf_suspect_bars.'
                    : 'No unresolved Yahoo suspect bars in the last 30d.'}
                  {' '}Source: gold.v_us_equity_bar_quality (qr_etl).
                </div>
              </div>
            )}
          </div>

          {/* Data Source Legend */}
          <div className="p-4 qr-surface">
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
          <div className="qr-surface p-4">
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
          <div className="qr-surface p-4">
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

      {/* SYSTEM HEALTH */}
      {activeSection === 'health' && (
        <div className="space-y-4">
          {/* Market Clocks */}
          <div className="qr-surface p-4">
            <h3 className="text-sm font-black text-white uppercase tracking-wider mb-4">Market Clocks</h3>
            <div className="grid grid-cols-3 gap-4">
              {[
                { city: 'HK', time: clocks.hkt, open: statuses.hk },
                { city: 'LON', time: clocks.lon, open: statuses.lon },
                { city: 'NYC', time: clocks.nyc, open: statuses.nyc },
              ].map(m => (
                <div key={m.city} className="p-4 rounded-lg bg-slate-800/50 border border-white/5 flex items-center gap-3">
                  <span className={`w-2 h-2 rounded-full ${m.open ? 'bg-emerald-400 animate-pulse' : 'bg-slate-600'}`} />
                  <div>
                    <div className="text-xs text-slate-400">{m.city}</div>
                    <div className="text-sm font-bold text-white font-mono">{m.time}</div>
                    <div className="text-[10px] text-slate-500">{m.open ? 'Open' : 'Closed'}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Connection Status */}
          <div className="qr-surface p-4">
            <h3 className="text-sm font-black text-white uppercase tracking-wider mb-4">Connection Status</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-lg bg-slate-800/50 border border-white/5">
                <div className="text-xs text-slate-400">API Latency</div>
                <div className={`text-lg font-bold font-mono ${latencyMs != null && latencyMs < 500 ? 'text-emerald-400' : latencyMs != null && latencyMs < 2000 ? 'text-amber-400' : 'text-rose-400'}`}>
                  {latencyMs != null ? `${latencyMs}ms` : '—'}
                </div>
              </div>
              <div className="p-4 rounded-lg bg-slate-800/50 border border-white/5">
                <div className="text-xs text-slate-400">API Health</div>
                <div className={`text-lg font-bold ${healthData?.status === 'healthy' ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {healthData?.status || 'unknown'}
                </div>
              </div>
              <div className="p-4 rounded-lg bg-slate-800/50 border border-white/5">
                <div className="text-xs text-slate-400">WebSocket</div>
                <div className={`text-lg font-bold ${wsConnected ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {wsConnected ? 'Connected' : 'Disconnected'}
                </div>
              </div>
              <div className="p-4 rounded-lg bg-slate-800/50 border border-white/5">
                <div className="text-xs text-slate-400">Database</div>
                <div className={`text-lg font-bold ${healthData?.db_connected ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {healthData?.db_connected ? 'Connected' : 'Disconnected'}
                </div>
              </div>
            </div>
          </div>

          {/* Health Details */}
          {healthData && (
            <div className="qr-surface p-4">
              <h3 className="text-sm font-black text-white uppercase tracking-wider mb-4">Health Details</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                {Object.entries(healthData).map(([key, value]) => (
                  <div key={key} className="p-3 rounded-lg bg-slate-800/50">
                    <span className="text-xs text-slate-400 block uppercase">{key.replace(/_/g, ' ')}</span>
                    <span className={`font-mono ${typeof value === 'boolean' ? (value ? 'text-emerald-400' : 'text-rose-400') : 'text-white'}`}>
                      {typeof value === 'boolean' ? (value ? '✓' : '✗') : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
        </div>
      </div>
    </div>
  );
};

export default SettingsTab;
