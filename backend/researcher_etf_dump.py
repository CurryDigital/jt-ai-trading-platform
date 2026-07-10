import sys, json
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
r = client.get('/api/strategies/researcher?fresh=1')
print('status:', r.status_code)
for s in r.json()['strategies']:
    if s['id'].startswith('ETF_'):
        print(json.dumps({k: s.get(k) for k in ['id','sharpe_ratio','trade_count_oos','backtest_trades','max_drawdown','win_rate','priority']}, indent=2))
