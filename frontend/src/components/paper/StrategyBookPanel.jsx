import React, { useState } from 'react';
import StrategyRow from './StrategyRow';

const GROUPS = [
  { key: 'approved',    label: 'ACTIVE NOW',    color: 'text-emerald-400',  border: 'border-emerald-500/20' },
  { key: 'backtesting', label: 'BACKTESTING',   color: 'text-blue-400',     border: 'border-blue-500/20' },
  { key: 'rejected',    label: 'ARCHIVED',      color: 'text-slate-400',    border: 'border-slate-500/20' },
  { key: 'pending',     label: 'PENDING',       color: 'text-amber-400',    border: 'border-amber-500/20' },
];

export default function StrategyBookPanel({ data }) {
  const strategies = data?.strategies || [];
  const [collapsed, setCollapsed] = useState(new Set(['rejected', 'pending']));

  if (!strategies.length) {
    return (
      <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-4">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Strategy Book</h3>
        <p className="text-sm text-slate-500 mt-2">No strategies</p>
      </div>
    );
  }

  const toggleGroup = (key) => {
    setCollapsed(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  return (
    <div className="rounded-lg bg-slate-800/50 border border-slate-700/50 p-3">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
          Strategy Book ({strategies.length})
        </h3>
        <div className="text-[10px] text-slate-500">
          Click row to expand
        </div>
      </div>

      <div className="space-y-3">
        {GROUPS.map(group => {
          const groupStrats = strategies.filter(s => s.status === group.key);
          if (!groupStrats.length) return null;
          const isCollapsed = collapsed.has(group.key);

          return (
            <div key={group.key}>
              <button
                onClick={() => toggleGroup(group.key)}
                className={`flex items-center gap-2 w-full text-left pb-1 border-b ${group.border} mb-1`}
              >
                <span className="text-[10px]"
                >{isCollapsed ? '▸' : '▾'}</span>
                <span className={`text-[10px] font-bold uppercase tracking-wider ${group.color}`}>
                  {group.label}
                </span>
                <span className="text-[10px] text-slate-500">({groupStrats.length})</span>
              </button>

              {!isCollapsed && (
                <div className="space-y-1 mt-1">
                  {groupStrats.map(s => (
                    <StrategyRow key={s.strategy_id} strategy={s} isArchived={group.key === 'rejected'} />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
