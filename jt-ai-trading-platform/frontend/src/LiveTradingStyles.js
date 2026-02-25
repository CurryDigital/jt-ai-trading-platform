import React from 'react';

// Professional Live Trading Dashboard Styles
export const LiveTradingStyles = `
  /* Clean, professional dark theme */
  .trading-dashboard {
    background: #0a0a0b;
    min-height: 100vh;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  }
  
  /* Header */
  .trading-header {
    background: linear-gradient(180deg, #111113 0%, #0a0a0b 100%);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding: 1.5rem 2rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .trading-header h1 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #fff;
    letter-spacing: -0.02em;
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
  
  /* Stats Grid */
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
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: -0.02em;
  }
  
  .stat-card .value.positive {
    color: #10b981;
  }
  
  .stat-card .value.negative {
    color: #ef4444;
  }
  
  .stat-card .value.neutral {
    color: #fff;
  }
  
  /* Main Content */
  .trading-content {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 1.5rem;
    padding: 0 2rem 2rem;
  }
  
  @media (max-width: 1024px) {
    .trading-content {
      grid-template-columns: 1fr;
    }
  }
  
  /* Tables */
  .trading-table-container {
    background: #111113;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    overflow: hidden;
  }
  
  .trading-table-header {
    padding: 1rem 1.25rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .trading-table-header h3 {
    font-size: 0.875rem;
    font-weight: 600;
    color: #fff;
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
  
  /* Position badges */
  .position-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.625rem;
    border-radius: 4px;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
  }
  
  .position-badge.long {
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
  }
  
  .position-badge.short {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }
  
  .position-badge.flat {
    background: rgba(107, 114, 128, 0.1);
    color: #6b7280;
  }
  
  /* Price columns */
  .price {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 500;
  }
  
  .price.long {
    color: #10b981;
  }
  
  .price.short {
    color: #ef4444;
  }
  
  /* PnL */
  .pnl {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
  }
  
  .pnl.positive {
    color: #10b981;
  }
  
  .pnl.negative {
    color: #ef4444;
  }
  
  /* Side buttons */
  .side-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 3.5rem;
    padding: 0.25rem 0;
    border-radius: 4px;
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
  }
  
  .side-badge.buy {
    background: rgba(16, 185, 129, 0.1);
    color: #10b981;
  }
  
  .side-badge.sell {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }
  
  /* Action buttons */
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
  
  .btn-primary {
    background: #3b82f6;
    color: #fff;
  }
  
  .btn-primary:hover {
    background: #2563eb;
  }
  
  .btn-danger {
    background: transparent;
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
  }
  
  .btn-danger:hover {
    background: rgba(239, 68, 68, 0.1);
  }
  
  .btn-success {
    background: #10b981;
    color: #fff;
  }
  
  .btn-success:hover {
    background: #059669;
  }
  
  /* Trade Log */
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
  
  .trade-log-scroll {
    max-height: 400px;
    overflow-y: auto;
  }
  
  /* Empty state */
  .empty-state {
    padding: 3rem;
    text-align: center;
    color: #6b7280;
  }
  
  /* Inventory panel */
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
  }
  
  .inventory-list {
    padding: 0.5rem;
  }
  
  .inventory-item {
    padding: 0.875rem 1rem;
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
  }
  
  .inventory-item-symbol {
    font-weight: 600;
    color: #fff;
    font-size: 0.875rem;
  }
  
  .inventory-item-details {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin-top: 0.25rem;
  }
  
  .inventory-item-price {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #9ca3af;
  }
  
  .inventory-item-pnl {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    font-size: 0.875rem;
  }
  
  /* Scrollbar */
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
`;

export default LiveTradingStyles;
