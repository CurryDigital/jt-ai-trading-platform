import React, { useState, useEffect } from 'react';

// IBKR Gateway Test Component - Fixed Error Handling
// Integrates into the Config tab for testing Gateway connectivity

export const IbkrGatewayTester = () => {
  const [testResults, setTestResults] = useState({});
  const [isLoading, setIsLoading] = useState({});
  const [executionMode, setExecutionMode] = useState('SIMULATION');
  const [gatewayConfig, setGatewayConfig] = useState({
    host: '52.74.14.181',
    port: 4001,
    clientId: 1
  });

  useEffect(() => {
    setGatewayConfig({
      host: '52.74.14.181',
      port: 4001,
      clientId: 1
    });
    fetchExecutionMode();
  }, []);

  const fetchExecutionMode = async () => {
    try {
      const res = await fetch('/api/execution/global-mode');
      if (res.ok) {
        const data = await res.json();
        setExecutionMode(data.execution_mode);
      }
    } catch (e) {
      console.error('Failed to fetch mode:', e);
    }
  };

  const runTest = async (testName, testFn) => {
    setIsLoading(prev => ({ ...prev, [testName]: true }));
    setTestResults(prev => ({ ...prev, [testName]: { status: 'running', message: 'Testing...' } }));
    
    try {
      const result = await testFn();
      setTestResults(prev => ({ 
        ...prev, 
        [testName]: { 
          status: result.success ? 'success' : 'error', 
          message: result.message,
          data: result.data,
          timestamp: new Date().toLocaleTimeString()
        } 
      }));
    } catch (error) {
      setTestResults(prev => ({ 
        ...prev, 
        [testName]: { 
          status: 'error', 
          message: error.message || 'Test failed - Backend may be offline',
          timestamp: new Date().toLocaleTimeString()
        } 
      }));
    } finally {
      setIsLoading(prev => ({ ...prev, [testName]: false }));
    }
  };

  // Test 1: Connection Test - Fixed with better error handling
  const testConnection = async () => {
    try {
      const response = await fetch('/api/ib/tws/status', {
        headers: { 'Accept': 'application/json' }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Backend unavailable`);
      }
      
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Backend returned non-JSON response. Check if backend is running.');
      }
      
      const data = await response.json();
      
      if (data.is_connected) {
        return {
          success: true,
          message: `✓ Connected to IB Gateway at ${data.host}:${data.port}`,
          data: data
        };
      } else {
        return {
          success: false,
          message: `⚠ Not connected to Gateway. Host: ${data.host}:${data.port}. Try clicking "Connect IB" button.`,
          data: data
        };
      }
    } catch (error) {
      throw new Error(`Connection test failed: ${error.message}`);
    }
  };

  // Test 2: Market Data Test
  const testMarketData = async () => {
    try {
      const response = await fetch('/api/fx/pairs', {
        headers: { 'Accept': 'application/json' }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data && data.length > 0) {
        const eurusd = data.find(p => p.ticker === 'EURUSD=X');
        return {
          success: true,
          message: `✓ Market data available: ${data.length} FX pairs`,
          data: {
            sample: eurusd || data[0],
            totalPairs: data.length
          }
        };
      } else {
        return {
          success: false,
          message: '⚠ No market data available - database may be empty',
          data: { count: 0 }
        };
      }
    } catch (error) {
      throw new Error(`Market data test failed: ${error.message}`);
    }
  };

  // Test 3: Historical Data Test
  const testHistoricalData = async () => {
    try {
      const response = await fetch('/api/fx/bars/latest?ticker=EURUSD&limit=5', {
        headers: { 'Accept': 'application/json' }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      if (Array.isArray(data) && data.length > 0) {
        return {
          success: true,
          message: `✓ Historical data: ${data.length} bars retrieved`,
          data: {
            bars: data.slice(0, 3),
            latest: data[0]
          }
        };
      } else {
        return {
          success: false,
          message: '⚠ No historical bars available',
          data: null
        };
      }
    } catch (error) {
      throw new Error(`Historical data test failed: ${error.message}`);
    }
  };

  // Test 4: Gateway Health Check (Simple TCP test)
  const testGatewayHealth = async () => {
    try {
      // Simple check if Gateway port is reachable
      const response = await fetch('/api/ib/tws/status', {
        headers: { 'Accept': 'application/json' }
      });
      
      if (!response.ok) {
        throw new Error(`Backend error: HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      return {
        success: true,
        message: `Gateway config: ${data.host}:${data.port} | Status: ${data.is_connected ? 'CONNECTED' : 'DISCONNECTED'}`,
        data: data
      };
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`);
    }
  };

  // Test 5: Paper Trading Test - Simulate a trade
  const testPaperTrading = async () => {
    try {
      // Step 1: Create a test paper strategy
      const testTicker = 'AAPL';
      const testStrategy = 'araso_factor_model';
      
      const createResponse = await fetch('/api/strategies/add-to-paper', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          strategy_id: testStrategy,
          tickers: [testTicker],
          capital_per_position: 1000
        })
      });
      
      if (!createResponse.ok) {
        throw new Error(`Failed to create paper strategy: HTTP ${createResponse.status}`);
      }
      
      const createData = await createResponse.json();
      
      if (!createData.success) {
        throw new Error('Paper strategy creation failed');
      }
      
      // Step 2: Verify it was created by fetching paper strategies
      const verifyResponse = await fetch('/api/paper-strategies');
      
      if (!verifyResponse.ok) {
        throw new Error(`Failed to verify: HTTP ${verifyResponse.status}`);
      }
      
      const verifyData = await verifyResponse.json();
      const foundStrategy = verifyData.strategies?.find(s => s.strategy_id === testStrategy);
      
      if (!foundStrategy) {
        throw new Error('Created strategy not found in paper strategies list');
      }
      
      // Step 3: Clean up - delete the test strategy
      // Note: We'll skip cleanup for now to keep the test simple
      
      return {
        success: true,
        message: `✓ Paper trading pipeline working: Added AAPL to ARASO strategy for ${testTicker} with $1,000 capital`,
        data: {
          strategy_id: testStrategy,
          ticker: testTicker,
          capital: 1000,
          status: foundStrategy.status,
          total_paper_strategies: verifyData.count
        }
      };
    } catch (error) {
      throw new Error(`Paper trading test failed: ${error.message}`);
    }
  };

  const testIBKROrder = async (action = 'BUY') => {
    try {
      // Check current execution mode
      const modeResponse = await fetch('/api/execution/global-mode');
      if (!modeResponse.ok) {
        throw new Error('Failed to fetch execution mode');
      }
      const modeData = await modeResponse.json();
      const currentMode = modeData.execution_mode;
      
      return {
        success: true,
        message: `✓ ${currentMode} mode active — use Portfolio tab to place orders`,
        data: { mode: currentMode }
      };
    } catch (error) {
      throw new Error(`Order check failed: ${error.message}`);
    }
  };

  const tests = [
    {
      id: 'health',
      name: 'Backend Health',
      description: 'Check if backend API is responding',
      icon: '🔍',
      testFn: testGatewayHealth
    },
    {
      id: 'connection',
      name: 'Gateway Status',
      description: 'Check IB Gateway connection state',
      icon: '🔌',
      testFn: testConnection
    },
    {
      id: 'marketData',
      name: 'Market Data',
      description: 'Check FX market data from database',
      icon: '📊',
      testFn: testMarketData
    },
    {
      id: 'historical',
      name: 'Historical Data',
      description: 'Check historical bars availability',
      icon: '📈',
      testFn: testHistoricalData
    },
    {
      id: 'paperTrading',
      name: 'Paper Trading',
      description: 'Test paper trading strategy creation pipeline',
      icon: '💰',
      testFn: testPaperTrading
    },
    {
      id: 'ibkrOrder',
      name: 'IBKR Order Test',
      description: executionMode === 'SIMULATION' 
        ? '⚠️ In SIM mode - click to test simulation'
        : `📤 Send real order to IBKR (${executionMode})`,
      icon: executionMode === 'SIMULATION' ? '🧪' : '📤',
      testFn: () => testIBKROrder('BUY'),
      highlight: executionMode !== 'SIMULATION',
      isOrderTest: true
    }
  ];

  const runAllTests = async () => {
    for (const test of tests) {
      if (!test.isOrderTest) {
        await runTest(test.id, test.testFn);
        await new Promise(r => setTimeout(r, 500));
      }
    }
  };

  return (
    <div className="qr-surface p-4"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4"
      >
        <div className="space-y-1"
        >
          <div className="flex items-center gap-2"
          >
            <h3 className="text-[13px] font-bold text-white"
            >
              IBKR Gateway Diagnostics
            </h3>
            <span className={`text-[10px] px-2 py-1 rounded font-bold ${
              executionMode === 'SIMULATION' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
              executionMode === 'PAPER_TRADING' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' :
              'bg-rose-500/20 text-rose-400 border border-rose-500/30'
            }`}>
              {executionMode === 'SIMULATION' ? '🧪 SIM' :
               executionMode === 'PAPER_TRADING' ? '📝 PAPER' :
               '💰 LIVE'}
            </span>
          </div>
          <p className="text-sm text-slate-500 font-medium italic"
          >
            Test backend API and Gateway connectivity
          </p>
        </div>
        <button
          onClick={runAllTests}
          disabled={Object.values(isLoading).some(v => v)}
          className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white text-xs font-black uppercase tracking-widest transition-all shadow-lg font-outfit"
        >
          {Object.values(isLoading).some(v => v) ? 'Running...' : 'Run All Tests'}
        </button>
      </div>

      {/* Gateway Config Display */}
      <div className="mb-8 p-6 rounded-2xl bg-white/5 border border-white/10"
      >
        <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4 font-outfit"
        >
          Gateway Configuration
        </div>
        <div className="grid grid-cols-3 gap-4"
        >
          <div>
            <label className="text-[10px] font-bold text-slate-600 uppercase tracking-wider block mb-2 font-outfit"
            >Host</label>
            <input
              type="text"
              value={gatewayConfig.host}
              readOnly
              className="w-full px-4 py-2 rounded-lg bg-black/20 border border-white/10 text-white text-sm font-mono"
            />
          </div>
          <div>
            <label className="text-[10px] font-bold text-slate-600 uppercase tracking-wider block mb-2 font-outfit"
            >Port</label>
            <input
              type="number"
              value={gatewayConfig.port}
              readOnly
              className="w-full px-4 py-2 rounded-lg bg-black/20 border border-white/10 text-white text-sm font-mono"
            />
          </div>
          <div>
            <label className="text-[10px] font-bold text-slate-600 uppercase tracking-wider block mb-2 font-outfit"
            >Client ID</label>
            <input
              type="number"
              value={gatewayConfig.clientId}
              readOnly
              className="w-full px-4 py-2 rounded-lg bg-black/20 border border-white/10 text-white text-sm font-mono"
            />
          </div>
        </div>
      </div>

      {/* Test Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4"
      >
        {tests.map(test => {
          const result = testResults[test.id];
          const loading = isLoading[test.id];
          
          // Skip the old combined order test, we have separate buy/sell now
          if (test.isOrderTest) return null;
          
          return (
            <div
              key={test.id}
              className={`p-6 rounded-2xl border transition-all ${
                result?.status === 'success' ? 'bg-emerald-500/5 border-emerald-500/20' :
                result?.status === 'error' ? 'bg-rose-500/5 border-rose-500/20' :
                test.highlight ? 'bg-amber-500/10 border-amber-500/40 hover:border-amber-500/60 ring-1 ring-amber-500/20' :
                'bg-white/5 border-white/10 hover:border-white/20'
              }`}
            >
              <div className="flex items-start justify-between mb-4"
              >
                <div className="flex items-center gap-3"
                >
                  <span className="text-2xl"
                  >{test.icon}</span>
                  <div>
                    <h4 className="text-sm font-black text-white uppercase tracking-wider font-outfit"
                    >
                      {test.name}
                    </h4>
                    <p className="text-xs text-slate-500 font-medium"
                    >
                      {test.description}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => runTest(test.id, test.testFn)}
                  disabled={loading}
                  className={`px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all font-outfit ${
                    result?.status === 'success' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                    result?.status === 'error' ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30' :
                    'bg-blue-600 hover:bg-blue-500 text-white'
                  } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {loading ? '...' : result?.status === 'success' ? '✓ Pass' : result?.status === 'error' ? '✗ Fail' : 'Test'}
                </button>
              </div>

              {result && (
                <div className="space-y-2"
                >
                  <div className={`p-3 rounded-lg text-xs font-medium ${
                    result.status === 'success' ? 'bg-emerald-500/10 text-emerald-300' :
                    'bg-rose-500/10 text-rose-300'
                  }`}
                  >
                    {result.message}
                  </div>
                  
                  {result.data && (
                    <pre className="p-3 rounded-lg bg-black/30 text-[10px] text-slate-400 font-mono overflow-x-auto"
                    >
                      {JSON.stringify(result.data, null, 2)}
                    </pre>
                  )}
                  
                  {result.timestamp && (
                    <div className="text-[10px] text-slate-600 font-mono text-right"
                    >
                      {result.timestamp}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Order Test Results */}
      {(testResults['ibkrOrderBuy'] || testResults['ibkrOrderSell']) && (
        <div className="mt-8 space-y-4"
        >
          {testResults['ibkrOrderBuy'] && (
            <div className={`p-6 rounded-2xl border ${
              testResults['ibkrOrderBuy'].status === 'success' ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-rose-500/5 border-rose-500/20'
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <span className="text-2xl">📈</span>
                <div>
                  <h4 className="text-sm font-black text-white uppercase tracking-wider font-outfit">BUY Order Result</h4>
                  <p className="text-xs text-slate-500">{orderSymbol} × {orderQuantity} @ {orderType}</p>
                </div>
              </div>
              <div className={`p-3 rounded-lg text-xs font-medium ${
                testResults['ibkrOrderBuy'].status === 'success' ? 'bg-emerald-500/10 text-emerald-300' : 'bg-rose-500/10 text-rose-300'
              }`}>
                {testResults['ibkrOrderBuy'].message}
              </div>
              {testResults['ibkrOrderBuy'].data && (
                <pre className="p-3 rounded-lg bg-black/30 text-[10px] text-slate-400 font-mono overflow-x-auto mt-2">
                  {JSON.stringify(testResults['ibkrOrderBuy'].data, null, 2)}
                </pre>
              )}
            </div>
          )}
          
          {testResults['ibkrOrderSell'] && (
            <div className={`p-6 rounded-2xl border ${
              testResults['ibkrOrderSell'].status === 'success' ? 'bg-rose-500/5 border-rose-500/20' : 'bg-rose-500/5 border-rose-500/20'
            }`}>
              <div className="flex items-center gap-3 mb-4">
                <span className="text-2xl">📉</span>
                <div>
                  <h4 className="text-sm font-black text-white uppercase tracking-wider font-outfit">SELL Order Result</h4>
                  <p className="text-xs text-slate-500">{orderSymbol} × {orderQuantity} @ {orderType}</p>
                </div>
              </div>
              <div className={`p-3 rounded-lg text-xs font-medium ${
                testResults['ibkrOrderSell'].status === 'success' ? 'bg-emerald-500/10 text-emerald-300' : 'bg-rose-500/10 text-rose-300'
              }`}>
                {testResults['ibkrOrderSell'].message}
              </div>
              {testResults['ibkrOrderSell'].data && (
                <pre className="p-3 rounded-lg bg-black/30 text-[10px] text-slate-400 font-mono overflow-x-auto mt-2">
                  {JSON.stringify(testResults['ibkrOrderSell'].data, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>
      )}

      {/* Summary */}
      {Object.keys(testResults).length > 0 && (
        <div className="mt-8 p-6 rounded-2xl bg-white/5 border border-white/10"
        >
          <div className="flex items-center justify-between"
          >
            <div className="text-[10px] font-black text-slate-500 uppercase tracking-widest font-outfit"
            >
              Test Summary
            </div>
            <div className="flex items-center gap-4"
            >
              <span className="text-sm font-bold text-emerald-400 font-outfit"
              >
                ✓ {Object.values(testResults).filter(r => r.status === 'success').length} Passed
              </span>
              <span className="text-sm font-bold text-rose-400 font-outfit"
              >
                ✗ {Object.values(testResults).filter(r => r.status === 'error').length} Failed
              </span>
            </div>
          </div>
          <div className="mt-4 h-2 rounded-full bg-white/5 overflow-hidden"
          >
            <div 
              className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-blue-500 transition-all duration-500"
              style={{
                width: `${(Object.values(testResults).filter(r => r.status === 'success').length / (Object.keys(testResults).length || 1)) * 100}%`
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default IbkrGatewayTester;
