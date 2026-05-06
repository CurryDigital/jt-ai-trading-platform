import React, { useState, useEffect } from 'react';
import { api } from '../utils';

const inputCls = 'px-2 py-1.5 bg-slate-800/80 border border-white/10 rounded-lg text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/50';

export const AlertConfigPanel = () => {
  // --- Status ---
  const [status, setStatus] = useState(null);
  const [config, setConfig] = useState(null);

  // --- Configure form ---
  const [botToken, setBotToken] = useState('');
  const [chatId, setChatId] = useState('');
  const [configuring, setConfiguring] = useState(false);
  const [configMsg, setConfigMsg] = useState(null);

  // --- Test alerts ---
  const [customMessage, setCustomMessage] = useState('');
  const [testMsg, setTestMsg] = useState(null);
  const [testBusy, setTestBusy] = useState(null); // which button is busy

  // --- Daily summary ---
  const [summaryBusy, setSummaryBusy] = useState(false);
  const [summaryMsg, setSummaryMsg] = useState(null);

  // --- Fetch helpers ---
  const refresh = async () => {
    const [s, c] = await Promise.all([
      api.get('/api/alerts/status'),
      api.get('/api/alerts/config'),
    ]);
    if (s) setStatus(s);
    if (c) setConfig(c);
  };

  useEffect(() => { refresh(); }, []);

  const enabled = status?.enabled || config?.enabled || false;

  // --- Configure handler ---
  const handleConfigure = async () => {
    if (!botToken.trim() || !chatId.trim()) {
      setConfigMsg({ ok: false, text: 'Bot token and chat ID are required' });
      return;
    }
    setConfiguring(true);
    setConfigMsg(null);
    try {
      const res = await api.post('/api/alerts/configure', {
        bot_token: botToken.trim(),
        chat_id: chatId.trim(),
      });
      if (res?.status === 'success') {
        setConfigMsg({ ok: true, text: 'Configured successfully' });
        setBotToken('');
        setChatId('');
        refresh();
      } else {
        setConfigMsg({ ok: false, text: res?.detail || res?.message || 'Configuration failed' });
      }
    } catch {
      setConfigMsg({ ok: false, text: 'Network error' });
    }
    setConfiguring(false);
  };

  // --- Test alert handler ---
  const handleTest = async (type) => {
    setTestBusy(type);
    setTestMsg(null);
    try {
      const body = { type };
      if (type === 'custom' && customMessage.trim()) {
        body.message = customMessage.trim();
      }
      const res = await api.post('/api/alerts/test', body);
      if (res?.status === 'sent' || res?.success) {
        setTestMsg({ ok: true, text: `${type} alert sent` });
      } else {
        setTestMsg({ ok: false, text: res?.detail || res?.error || 'Send failed' });
      }
    } catch {
      setTestMsg({ ok: false, text: 'Network error' });
    }
    setTestBusy(null);
  };

  // --- Daily summary handler ---
  const handleDailySummary = async () => {
    setSummaryBusy(true);
    setSummaryMsg(null);
    try {
      const res = await api.post('/api/alerts/send-daily-summary', {});
      if (res?.status === 'sent') {
        setSummaryMsg({ ok: true, text: 'Daily summary sent' });
      } else {
        setSummaryMsg({ ok: false, text: res?.error || 'Failed to send summary' });
      }
    } catch {
      setSummaryMsg({ ok: false, text: 'Network error' });
    }
    setSummaryBusy(false);
  };

  return (
    <div className="qr-surface p-3 space-y-3">
      {/* Header with status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-white">Telegram Alerts</span>
          <span className={`qr-chip ${enabled ? 'qr-chip-emerald' : 'qr-chip-rose'}`}>
            <span
              className={`inline-block w-1.5 h-1.5 rounded-full mr-1 ${
                enabled ? 'bg-emerald-400' : 'bg-rose-400'
              }`}
            />
            {enabled ? 'ENABLED' : 'DISABLED'}
          </span>
        </div>
        {status?.chat_id && (
          <span className="text-[10px] text-slate-500 font-mono">
            chat {status.chat_id}
          </span>
        )}
      </div>

      {/* Thresholds summary (from /api/alerts/config) */}
      {config?.thresholds && (
        <div className="flex flex-wrap gap-1.5">
          {Object.entries(config.thresholds).map(([key, val]) => (
            <span key={key} className="qr-chip qr-chip-amber text-[9px]">
              {key.replace(/_/g, ' ')}: <span className="qr-num">{val}</span>
            </span>
          ))}
        </div>
      )}

      {/* --- Configuration --- */}
      <div>
        <span className="qr-label">Configuration</span>
        <div className="mt-1.5 space-y-1.5">
          <input
            type="text"
            placeholder="Bot Token"
            value={botToken}
            onChange={(e) => setBotToken(e.target.value)}
            className={`${inputCls} w-full`}
          />
          <input
            type="text"
            placeholder="Chat ID"
            value={chatId}
            onChange={(e) => setChatId(e.target.value)}
            className={`${inputCls} w-full`}
          />
          <div className="flex items-center gap-2">
            <button
              onClick={handleConfigure}
              disabled={configuring}
              className="qr-btn-primary"
            >
              {configuring ? 'Configuring...' : 'Configure'}
            </button>
            {configMsg && (
              <span className={`text-[10px] ${configMsg.ok ? 'text-emerald-400' : 'text-rose-400'}`}>
                {configMsg.text}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* --- Test Alerts --- */}
      <div>
        <span className="qr-label">Test Alerts</span>
        <div className="mt-1.5 space-y-1.5">
          <div className="flex items-center gap-1.5 flex-wrap">
            <button
              onClick={() => handleTest('trade')}
              disabled={!!testBusy || !enabled}
              className="qr-btn-primary"
            >
              {testBusy === 'trade' ? 'Sending...' : 'Trade Alert'}
            </button>
            <button
              onClick={() => handleTest('drawdown')}
              disabled={!!testBusy || !enabled}
              className="qr-btn-primary"
            >
              {testBusy === 'drawdown' ? 'Sending...' : 'Drawdown Alert'}
            </button>
            <button
              onClick={() => handleTest('custom')}
              disabled={!!testBusy || !enabled}
              className="qr-btn-ghost"
            >
              {testBusy === 'custom' ? 'Sending...' : 'Custom'}
            </button>
          </div>
          <input
            type="text"
            placeholder="Custom message (optional)"
            value={customMessage}
            onChange={(e) => setCustomMessage(e.target.value)}
            className={`${inputCls} w-full`}
          />
          {testMsg && (
            <span className={`text-[10px] ${testMsg.ok ? 'text-emerald-400' : 'text-rose-400'}`}>
              {testMsg.text}
            </span>
          )}
          {!enabled && (
            <span className="text-[10px] text-slate-500">
              Configure Telegram above to enable test alerts
            </span>
          )}
        </div>
      </div>

      {/* --- Daily Summary --- */}
      <div>
        <span className="qr-label">Daily Summary</span>
        <div className="mt-1.5 flex items-center gap-2">
          <button
            onClick={handleDailySummary}
            disabled={summaryBusy || !enabled}
            className="qr-btn-ghost"
          >
            {summaryBusy ? 'Sending...' : 'Send Daily Summary'}
          </button>
          {summaryMsg && (
            <span className={`text-[10px] ${summaryMsg.ok ? 'text-emerald-400' : 'text-rose-400'}`}>
              {summaryMsg.text}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default AlertConfigPanel;
