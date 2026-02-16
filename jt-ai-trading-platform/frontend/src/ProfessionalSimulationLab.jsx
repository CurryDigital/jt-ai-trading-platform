import React, { useState } from 'react';

export const ProfessionalSimulationLab = ({ 
  quantMatrix, 
  activeStrategies,
  onDeploy,
  onOpenBulk
}) => {
  const [expandedTemplates, setExpandedTemplates] = useState({});

  const toggleTemplate = (tid) => {
    setExpandedTemplates(prev => ({
      ...prev,
      [tid]: !prev[tid]
    }));
  };

  // Helper to format currency
  const formatMoney = (val) => {
    const num = Number(val) || 0;
    const sign = num >= 0 ? '+' : '-';
    return `${sign}$${Math.abs(num).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
  };

  const formatPercent = (val) => `${(Number(val) || 0).toFixed(1)}%`;

  // IBKR FX Commission Simulation (approx $2 per lot / 100k units, min $2)
  // Scaling for micro lots: ~0.2-0.5 pips effective spread + comms
  const calculateSimCommission = (trades30d, lotSize = 10000) => {
    // Est daily trades = trades30d / 30
    const dailyTrades = trades30d / 30;
    // Comm per trade (round trip)
    const commPerTrade = Math.max(2.0, (lotSize / 100000) * 2.0); 
    return dailyTrades * commPerTrade;
  };

  if (!quantMatrix?.discovery) {
    return (
      <div className="p-12 text-center text-slate-500 font-mono animate-pulse">
        INITIALIZING_SIMULATION_MATRIX...
      </div>
    );
  }

  return (
    <div className="trading-dashboard">
      {/* Header */}
      <div className="trading-header">
        <div>
          <h1>Simulation Lab</h1>
          <p style={{ color: '#6b7280', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            Backtest validation & forward testing environment
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <span className="status-badge" style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6', border: '1px solid rgba(59, 130, 246, 0.2)' }}>
            SIMULATION_MODE
          </span>
          <button onClick={onOpenBulk} className="btn btn-primary">
            Manage Portfolio
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="trading-content" style={{ gridTemplateColumns: '1fr' }}>
        <div className="trading-table-container">
          <div className="trading-table-header">
            <h3>Strategy Matrix</h3>
            <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>
              Click rows to expand details
            </span>
          </div>
          
          <div className="sim-table-wrapper">
            {Object.entries(quantMatrix.discovery).map(([tid, pairs]) => {
              const template = quantMatrix.active?.[tid] || { name: tid, description: 'Strategy Template' };
              const isExpanded = expandedTemplates[tid];
              
              // Aggregate Stats
              const pairList = Object.values(pairs);
              const avgWin = pairList.reduce((a, b) => a + (b.accuracy || 0), 0) / (pairList.length || 1);
              const totalTrades30d = pairList.reduce((a, b) => a + (b.trades_30d || 0), 0);
              const avgSharpe = pairList.reduce((a, b) => a + (b.sharpe || 0), 0) / (pairList.length || 1);

              return (
                <div key={tid} className="strategy-group">
                  {/* Parent Row */}
                  <div 
                    className={`strategy-header ${isExpanded ? 'expanded' : ''}`}
                    onClick={() => toggleTemplate(tid)}
                  >
                    <div className="strategy-info">
                      <div className="strategy-icon">
                        {isExpanded ? '−' : '+'}
                      </div>
                      <div>
                        <div className="strategy-name">{template.name}</div>
                        <div className="strategy-desc">{template.description}</div>
                      </div>
                    </div>
                    
                    <div className="strategy-metrics">
                      <div className="metric">
                        <label>Avg Win Rate</label>
                        <span className={avgWin > 60 ? 'positive' : 'neutral'}>{avgWin.toFixed(1)}%</span>
                      </div>
                      <div className="metric">
                        <label>30D Trades</label>
                        <span>{totalTrades30d}</span>
                      </div>
                      <div className="metric">
                        <label>Avg Sharpe</label>
                        <span className={avgSharpe > 1.5 ? 'positive' : 'neutral'}>{avgSharpe.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Expanded Content */}
                  {isExpanded && (
                    <div className="strategy-details">
                      <table className="trading-table">
                        <thead>
                          <tr>
                            <th>Ticker</th>
                            <th>1D Trades (Est)</th>
                            <th>1D Return</th>
                            <th>7D Return</th>
                            <th>Est. Comm (Daily)</th>
                            <th>Win Rate</th>
                            <th>Sharpe</th>
                            <th style={{ textAlign: 'right' }}>Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(pairs).map(([pair, stats]) => {
                            const dailyTrades = Math.round(stats.trades_30d / 30);
                            // Synthesize estimates based on stats (for demo)
                            const est1d = stats.avg_pnl_per_trade_pct * 0.8; 
                            const est7d = est1d * 5.5; 
                            const comms = calculateSimCommission(stats.trades_30d);
                            
                            // Check if active in SIMULATION
                            const activeSim = activeStrategies.find(s => 
                              s.target_ticker === pair && 
                              s.params?.template_id === tid &&
                              s.params?.execution_mode === 'SIMULATION'
                            );

                            return (
                              <tr key={pair}>
                                <td style={{ fontWeight: 600, color: '#fff' }}>
                                  {pair.replace('=X', '')}
                                </td>
                                <td>{dailyTrades}</td>
                                <td className={est1d > 0 ? 'pnl positive' : 'pnl negative'}>
                                  {formatPercent(est1d)}
                                </td>
                                <td className={est1d > 0 ? 'pnl positive' : 'pnl negative'}>
                                  {formatPercent(est7d)}
                                </td>
                                <td style={{ fontFamily: 'monospace', color: '#9ca3af' }}>
                                  -${comms.toFixed(2)}
                                </td>
                                <td className={stats.accuracy > 65 ? 'positive' : 'neutral'}>
                                  {stats.accuracy}%
                                </td>
                                <td>{stats.sharpe}</td>
                                <td style={{ textAlign: 'right' }}>
                                  {activeSim ? (
                                    <button className="btn btn-danger" style={{ fontSize: '0.7rem', padding: '0.25rem 0.75rem' }} onClick={() => onDeploy(pair, tid, 10000, 'terminate', activeSim.id)}>
                                      Stop Sim
                                    </button>
                                  ) : (
                                    <button className="btn btn-primary" style={{ fontSize: '0.7rem', padding: '0.25rem 0.75rem' }} onClick={() => onDeploy(pair, tid)}>
                                      Run Sim
                                    </button>
                                  )}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <style>{`
        .sim-table-wrapper {
          display: flex;
          flex-direction: column;
        }
        
        .strategy-group {
          border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        
        .strategy-group:last-child {
          border-bottom: none;
        }
        
        .strategy-header {
          padding: 1.5rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
          cursor: pointer;
          transition: background 0.2s;
        }
        
        .strategy-header:hover {
          background: rgba(255,255,255,0.02);
        }
        
        .strategy-header.expanded {
          background: rgba(255,255,255,0.03);
          border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        
        .strategy-info {
          display: flex;
          gap: 1rem;
          align-items: center;
        }
        
        .strategy-icon {
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: rgba(255,255,255,0.1);
          display: flex;
          align-items: center;
          justify-content: center;
          color: #fff;
          font-weight: bold;
          font-size: 14px;
        }
        
        .strategy-name {
          font-weight: 700;
          color: #fff;
          font-size: 1rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        
        .strategy-desc {
          color: #6b7280;
          font-size: 0.75rem;
          margin-top: 0.25rem;
        }
        
        .strategy-metrics {
          display: flex;
          gap: 2rem;
        }
        
        .metric {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
        }
        
        .metric label {
          font-size: 0.65rem;
          color: #6b7280;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 0.25rem;
        }
        
        .metric span {
          font-family: 'JetBrains Mono', monospace;
          font-weight: 600;
          font-size: 0.875rem;
          color: #d1d5db;
        }
        
        .metric span.positive { color: #10b981; }
        
        .strategy-details {
          background: rgba(0,0,0,0.2);
          animation: slideDown 0.2s ease-out;
        }
        
        @keyframes slideDown {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
};

export default ProfessionalSimulationLab;
