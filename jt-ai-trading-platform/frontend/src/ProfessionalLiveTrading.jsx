import React from 'react';

// Professional Live Trading Component
// Usage: Replace the 'quant' live tab content in App.jsx with this component

export const ProfessionalLiveTrading = ({ 
  quantMatrix, 
  quantStrategies, 
  velocityTrades,
  displayPositions,
  onDeploy,
  onOpenBulk,
  onClosePosition,
  ibStatus,
  fetchIbData,
  connectIb,
  fetchData
}) => {
  // Calculate totals
  const activeStrategies = quantStrategies?.filter(s => s.params?.execution_mode !== 'SIMULATION') || [];
  const totalRealized = Object.values(quantMatrix?.active || {}).reduce(
    (acc, template) => acc + Object.values(template?.pairs || {}).reduce(
      (sum, pair) => sum + (pair?.realized_pnl || 0), 0
    ), 0
  );
  const totalUnrealized = Object.values(quantMatrix?.active || {}).reduce(
    (acc, template) => acc + Object.values(template?.pairs || {}).reduce(
      (sum, pair) => sum + (pair?.unrealized_pnl || 0), 0
    ), 0
  );
  const totalTrades = Object.values(quantMatrix?.active || {}).reduce(
    (acc, t) => acc + (t?.total_trades || 0), 0
  );

  const formatPnL = (val) => {
    const num = Number(val) || 0;
    const sign = num >= 0 ? '+' : '';
    return `${sign}$${Math.abs(num).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
  };

  const formatPrice = (val) => {
    const num = Number(val) || 0;
    if (num === 0) return '-';
    return num.toFixed(4);
  };

  const formatPercent = (val) => {
    const num = Number(val) || 0;
    const sign = num >= 0 ? '+' : '';
    return `${sign}${num.toFixed(2)}%`;
  };

  return (
    <div className="trading-dashboard">
      {/* Header */}
      <div className="trading-header">
        <div>
          <h1>Live Trading</h1>
          <p style={{ color: '#6b7280', fontSize: '0.875rem', marginTop: '0.25rem' }}>
            {activeStrategies.length} active strategies • {totalTrades} trades executed
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          {/* IBKR Auth Buttons */}
          {ibStatus?.web !== 'Authenticated' ? (
            <>
              <button 
                onClick={() => {
                  const width = 600, height = 900;
                  const left = (window.screen.width - width) / 2;
                  const top = (window.screen.height - height) / 2;
                  window.open('/sso/Login?forwardTo=22', 'ib_login_popup', 
                    `width=${width},height=${height},top=${top},left=${left},resizable=yes,scrollbars=yes,status=yes`);
                }}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '6px',
                  background: '#3b82f6',
                  color: '#fff',
                  border: 'none',
                  fontSize: '0.75rem',
                  fontWeight: 500,
                  cursor: 'pointer'
                }}
              >
                Authorize IBKR
              </button>
              <button 
                onClick={fetchIbData}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '6px',
                  background: 'transparent',
                  color: '#9ca3af',
                  border: '1px solid rgba(255,255,255,0.1)',
                  fontSize: '0.75rem',
                  fontWeight: 500,
                  cursor: 'pointer'
                }}
              >
                Sync Session
              </button>
            </>
          ) : (
            <>
              <span className="status-badge live">IBKR Connected</span>
              <button 
                onClick={() => { fetchIbData?.(); fetchData?.(); }}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '6px',
                  background: 'rgba(16,185,129,0.1)',
                  color: '#10b981',
                  border: '1px solid rgba(16,185,129,0.2)',
                  fontSize: '0.75rem',
                  fontWeight: 500,
                  cursor: 'pointer'
                }}
              >
                Refresh
              </button>
              <button 
                onClick={connectIb}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '6px',
                  background: 'transparent',
                  color: '#9ca3af',
                  border: '1px solid rgba(255,255,255,0.1)',
                  fontSize: '0.75rem',
                  fontWeight: 500,
                  cursor: 'pointer'
                }}
              >
                Init Socket
              </button>
            </>
          )}
          <span className="status-badge live">Live</span>
          <button 
            onClick={onOpenBulk}
            className="btn btn-success"
          >
            + Deploy Cluster
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <label>Realized P&L</label>
          <div className={`value ${totalRealized >= 0 ? 'positive' : 'negative'}`}>
            {formatPnL(totalRealized)}
          </div>
        </div>
        <div className="stat-card">
          <label>Unrealized P&L</label>
          <div className={`value ${totalUnrealized >= 0 ? 'positive' : 'negative'}`}>
            {formatPnL(totalUnrealized)}
          </div>
        </div>
        <div className="stat-card">
          <label>Total P&L</label>
          <div className={`value ${(totalRealized + totalUnrealized) >= 0 ? 'positive' : 'negative'}`}>
            {formatPnL(totalRealized + totalUnrealized)}
          </div>
        </div>
        <div className="stat-card">
          <label>Open Positions</label>
          <div className="value neutral">
            {displayPositions?.length || 0}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="trading-content">
        {/* Strategy Matrix */}
        <div className="trading-table-container">
          <div className="trading-table-header">
            <h3>Strategy Performance</h3>
          </div>
          <table className="trading-table">
            <thead>
              <tr>
                <th>Strategy</th>
                <th>Position</th>
                <th>Long Avg</th>
                <th>Short Avg</th>
                <th>Market</th>
                <th>Realized</th>
                <th>Unrealized</th>
                <th>Return</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {quantMatrix?.active && Object.entries(quantMatrix.active).flatMap(([tid, template]) => 
                Object.entries(template?.pairs || {}).map(([pair, data]) => {
                  if (!data?.is_active) return null;
                  const netQty = data?.inventory_qty || 0;
                  const posType = netQty > 0 ? 'LONG' : netQty < 0 ? 'SHORT' : 'FLAT';
                  const allocated = data?.allocated_capital || 10000;
                  const totalPnL = (data?.realized_pnl || 0) + (data?.unrealized_pnl || 0);
                  const returnPct = allocated > 0 ? (totalPnL / allocated) * 100 : 0;
                  
                  return (
                    <tr key={`${tid}-${pair}`}>
                      <td>
                        <div style={{ fontWeight: 600, color: '#fff' }}>
                          {pair?.replace('=X', '')}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                          {template?.name}
                        </div>
                      </td>
                      <td>
                        <span className={`position-badge ${posType.toLowerCase()}`}>
                          {posType}
                        </span>
                        {netQty !== 0 && (
                          <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.25rem' }}>
                            {Math.abs(netQty).toLocaleString()} units
                          </div>
                        )}
                      </td>
                      <td className="price long">{formatPrice(data?.long_avg_price)}</td>
                      <td className="price short">{formatPrice(data?.short_avg_price)}</td>
                      <td className="price">{formatPrice(data?.market_price)}</td>
                      <td className={`pnl ${(data?.realized_pnl || 0) >= 0 ? 'positive' : 'negative'}`}>
                        {formatPnL(data?.realized_pnl)}
                      </td>
                      <td className={`pnl ${(data?.unrealized_pnl || 0) >= 0 ? 'positive' : 'negative'}`}>
                        {formatPnL(data?.unrealized_pnl)}
                      </td>
                      <td className={`pnl ${returnPct >= 0 ? 'positive' : 'negative'}`}>
                        {formatPercent(returnPct)}
                      </td>
                      <td>
                        <button 
                          onClick={() => onDeploy?.(pair, tid, allocated, 'terminate', data?.id)}
                          className="btn btn-danger"
                        >
                          Close
                        </button>
                      </td>
                    </tr>
                  );
                })
              ).filter(Boolean)}
              {(!quantMatrix?.active || Object.keys(quantMatrix.active).length === 0) && (
                <tr>
                  <td colSpan="9">
                    <div className="empty-state">No active strategies</div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Inventory Panel */}
        <div className="inventory-panel">
          <div className="inventory-header">
            <h3>Live Holdings</h3>
          </div>
          <div className="inventory-list">
            {displayPositions?.length > 0 ? displayPositions.map((pos, i) => (
              <div key={i} className="inventory-item">
                <div>
                  <div className="inventory-item-header">
                    <span className="inventory-item-symbol">{pos?.symbol}</span>
                    <span className={`position-badge ${pos?.position > 0 ? 'long' : pos?.position < 0 ? 'short' : 'flat'}`}>
                      {pos?.position > 0 ? 'LONG' : pos?.position < 0 ? 'SHORT' : 'FLAT'}
                    </span>
                  </div>
                  <div className="inventory-item-details">
                    <span className="inventory-item-price">
                      {Math.abs(pos?.position || 0).toLocaleString()} units @ {formatPrice(pos?.avgCost)}
                    </span>
                  </div>
                </div>
                <div className={`inventory-item-pnl ${(pos?.unrealizedPnl || 0) >= 0 ? 'positive' : 'negative'}`}>
                  {formatPnL(pos?.unrealizedPnl)}
                </div>
              </div>
            )) : (
              <div className="empty-state">No positions</div>
            )}
          </div>
        </div>
      </div>

      {/* Trade Log */}
      <div style={{ padding: '0 2rem 2rem' }}>
        <div className="trade-log">
          <div className="trade-log-header">
            <h3>Trade Log</h3>
            <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>
              Last 50 trades
            </span>
          </div>
          <div className="trade-log-scroll">
            <table className="trading-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Symbol</th>
                  <th>Side</th>
                  <th>Price</th>
                  <th>Quantity</th>
                  <th>Value</th>
                  <th style={{ textAlign: 'right' }}>P&L</th>
                </tr>
              </thead>
              <tbody>
                {velocityTrades
                  ?.filter(t => !t?.strategy?.includes('SIMULATION'))
                  ?.slice(0, 50)
                  ?.map((trade, i) => (
                    <tr key={i}>
                      <td style={{ color: '#6b7280' }}>
                        {new Date(trade?.timestamp).toLocaleTimeString('en-HK', { 
                          timeZone: 'Asia/Hong_Kong', 
                          hour12: false,
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </td>
                      <td style={{ fontWeight: 600 }}>{trade?.ticker}</td>
                      <td>
                        <span className={`side-badge ${trade?.side?.toLowerCase()}`}>
                          {trade?.side}
                        </span>
                      </td>
                      <td className="price">{formatPrice(trade?.price)}</td>
                      <td>{trade?.quantity?.toLocaleString()}</td>
                      <td>{formatPnL(trade?.total_value)}</td>
                      <td style={{ textAlign: 'right' }} className={`pnl ${(trade?.pnl || 0) >= 0 ? 'positive' : 'negative'}`}>
                        {trade?.pnl !== null ? formatPnL(trade?.pnl) : '---'}
                      </td>
                    </tr>
                  ))}
                {(!velocityTrades || velocityTrades.filter(t => !t?.strategy?.includes('SIMULATION')).length === 0) && (
                  <tr>
                    <td colSpan="7">
                      <div className="empty-state">No trades recorded</div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Inject styles */}
      <style>{`
        .trading-dashboard {
          background: #0a0a0b;
          min-height: 100vh;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .trading-header {
          background: linear-gradient(180deg, #111113 0%, #0a0a0b 100%);
          border-bottom: 1px solid rgba(255,255,255,0.06);
          padding: 1.5rem 2rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .trading-header h1 {
          font-size: 1.5rem;
          font-weight: 600;
          color: #fff;
          letter-spacing: -0.02em;
          margin: 0;
        }
        
        .status-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.375rem 0.875rem;
          border-radius: 9999px;
          font-size: 0.75rem;
          font-weight: 500;
        }
        
        .status-badge.live {
          background: rgba(16, 185, 129, 0.1);
          color: #10b981;
          border: 1px solid rgba(16, 185, 129, 0.2);
        }
        
        .status-badge::before {
          content: '';
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: currentColor;
          animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
          padding: 1.5rem 2rem;
        }
        
        .stat-card {
          background: #111113;
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 12px;
          padding: 1.25rem;
        }
        
        .stat-card label {
          font-size: 0.75rem;
          color: #6b7280;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          font-weight: 500;
          display: block;
          margin-bottom: 0.5rem;
        }
        
        .stat-card .value {
          font-size: 1.5rem;
          font-weight: 600;
          font-family: 'SF Mono', Monaco, monospace;
          letter-spacing: -0.02em;
        }
        
        .stat-card .value.positive { color: #10b981; }
        .stat-card .value.negative { color: #ef4444; }
        .stat-card .value.neutral { color: #fff; }
        
        .trading-content {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 1.5rem;
          padding: 0 2rem 1.5rem;
        }
        
        @media (max-width: 1024px) {
          .trading-content { grid-template-columns: 1fr; }
        }
        
        .trading-table-container {
          background: #111113;
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 12px;
          overflow: hidden;
        }
        
        .trading-table-header {
          padding: 1rem 1.25rem;
          border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        
        .trading-table-header h3 {
          font-size: 0.875rem;
          font-weight: 600;
          color: #fff;
          margin: 0;
        }
        
        .trading-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.8125rem;
        }
        
        .trading-table thead {
          background: rgba(255,255,255,0.02);
        }
        
        .trading-table th {
          padding: 0.75rem 1rem;
          text-align: left;
          font-weight: 500;
          color: #6b7280;
          text-transform: uppercase;
          font-size: 0.6875rem;
          letter-spacing: 0.05em;
          border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        
        .trading-table td {
          padding: 0.875rem 1rem;
          border-bottom: 1px solid rgba(255,255,255,0.04);
          color: #d1d5db;
        }
        
        .trading-table tbody tr:hover {
          background: rgba(255,255,255,0.02);
        }
        
        .trading-table tbody tr:last-child td {
          border-bottom: none;
        }
        
        .position-badge {
          display: inline-flex;
          align-items: center;
          padding: 0.25rem 0.625rem;
          border-radius: 4px;
          font-size: 0.6875rem;
          font-weight: 600;
          text-transform: uppercase;
        }
        
        .position-badge.long { background: rgba(16, 185, 129, 0.1); color: #10b981; }
        .position-badge.short { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
        .position-badge.flat { background: rgba(107, 114, 128, 0.1); color: #6b7280; }
        
        .price { font-family: 'SF Mono', Monaco, monospace; font-weight: 500; }
        .price.long { color: #10b981; }
        .price.short { color: #ef4444; }
        
        .pnl { font-family: 'SF Mono', Monaco, monospace; font-weight: 600; }
        .pnl.positive { color: #10b981; }
        .pnl.negative { color: #ef4444; }
        
        .side-badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 3rem;
          padding: 0.25rem 0;
          border-radius: 4px;
          font-size: 0.6875rem;
          font-weight: 600;
          text-transform: uppercase;
        }
        
        .side-badge.buy { background: rgba(16, 185, 129, 0.1); color: #10b981; }
        .side-badge.sell { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
        
        .btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          padding: 0.5rem 1rem;
          border-radius: 6px;
          font-size: 0.75rem;
          font-weight: 500;
          transition: all 0.15s ease;
          border: none;
          cursor: pointer;
        }
        
        .btn-success {
          background: #10b981;
          color: #fff;
        }
        
        .btn-success:hover {
          background: #059669;
        }
        
        .btn-danger {
          background: transparent;
          color: #ef4444;
          border: 1px solid rgba(239, 68, 68, 0.3);
        }
        
        .btn-danger:hover {
          background: rgba(239, 68, 68, 0.1);
        }
        
        .inventory-panel {
          background: #111113;
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 12px;
          overflow: hidden;
        }
        
        .inventory-header {
          padding: 1rem 1.25rem;
          border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        
        .inventory-header h3 {
          font-size: 0.875rem;
          font-weight: 600;
          color: #fff;
          margin: 0;
        }
        
        .inventory-list {
          max-height: 500px;
          overflow-y: auto;
        }
        
        .inventory-item {
          padding: 1rem 1.25rem;
          border-bottom: 1px solid rgba(255,255,255,0.04);
          display: grid;
          grid-template-columns: 1fr auto;
          gap: 1rem;
          align-items: center;
        }
        
        .inventory-item:last-child {
          border-bottom: none;
        }
        
        .inventory-item-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 0.25rem;
        }
        
        .inventory-item-symbol {
          font-weight: 600;
          color: #fff;
          font-size: 0.875rem;
        }
        
        .inventory-item-price {
          font-family: 'SF Mono', Monaco, monospace;
          font-size: 0.75rem;
          color: #9ca3af;
        }
        
        .inventory-item-pnl {
          font-family: 'SF Mono', Monaco, monospace;
          font-weight: 600;
          font-size: 0.875rem;
        }
        
        .trade-log {
          background: #111113;
          border: 1px solid rgba(255,255,255,0.06);
          border-radius: 12px;
          overflow: hidden;
        }
        
        .trade-log-header {
          padding: 1rem 1.25rem;
          border-bottom: 1px solid rgba(255,255,255,0.06);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .trade-log-header h3 {
          font-size: 0.875rem;
          font-weight: 600;
          color: #fff;
          margin: 0;
        }
        
        .trade-log-scroll {
          max-height: 400px;
          overflow-y: auto;
        }
        
        .empty-state {
          padding: 3rem;
          text-align: center;
          color: #6b7280;
          font-size: 0.875rem;
        }
        
        ::-webkit-scrollbar {
          width: 6px;
          height: 6px;
        }
        
        ::-webkit-scrollbar-track {
          background: transparent;
        }
        
        ::-webkit-scrollbar-thumb {
          background: rgba(255,255,255,0.1);
          border-radius: 3px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
          background: rgba(255,255,255,0.15);
        }
      `}</style>
    </div>
  );
};

export default ProfessionalLiveTrading;
