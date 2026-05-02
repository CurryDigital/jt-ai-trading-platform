import React, { useState } from 'react';
import { api } from '../utils';

export const LoginPage = ({ onLogin }) => {
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: user, password: pass }),
      });
      if (res.ok) {
        const data = await res.json();
        onLogin(data.token);
      } else {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || 'Login failed');
      }
    } catch {
      setError('Network error');
    }
    setBusy(false);
  };

  return (
    <div className="min-h-screen bg-[#05070a] flex items-center justify-center">
      <form onSubmit={submit} className="w-80 qr-surface p-6 space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-7 h-7 rounded-md bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center text-[11px] font-black text-white shadow-md shadow-blue-500/20">JT</div>
          <div>
            <div className="text-[13px] font-bold text-white tracking-tight">JTCML</div>
            <div className="text-[9px] text-slate-500">Quant Workspace</div>
          </div>
        </div>

        <div>
          <label className="qr-label block mb-1">Username</label>
          <input
            autoFocus
            value={user}
            onChange={(e) => setUser(e.target.value)}
            className="w-full px-3 py-2 bg-slate-900/60 border border-white/[0.08] rounded-md text-[12px] text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/50"
            placeholder="admin"
          />
        </div>
        <div>
          <label className="qr-label block mb-1">Password</label>
          <input
            type="password"
            value={pass}
            onChange={(e) => setPass(e.target.value)}
            className="w-full px-3 py-2 bg-slate-900/60 border border-white/[0.08] rounded-md text-[12px] text-white placeholder-slate-600 focus:outline-none focus:border-blue-500/50"
            placeholder="••••••••"
          />
        </div>

        {error && (
          <div className="text-[11px] text-rose-300 bg-rose-500/10 ring-1 ring-rose-500/25 rounded px-3 py-2">{error}</div>
        )}

        <button
          type="submit"
          disabled={busy || !user || !pass}
          className={`w-full py-2 rounded-md text-[12px] font-bold transition-colors ${
            busy || !user || !pass
              ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
              : 'bg-blue-500/20 text-blue-200 ring-1 ring-blue-500/40 hover:bg-blue-500/30'
          }`}
        >
          {busy ? 'Logging in…' : 'Login'}
        </button>

        <p className="text-[9px] text-slate-600 text-center">
          Auth is opt-in via <span className="font-mono">JTCML_AUTH=1</span>
        </p>
      </form>
    </div>
  );
};

export default LoginPage;
