import sys
sys.path.insert(0, '.')
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
r = client.get('/api/strategies/researcher?fresh=1')
print('status:', r.status_code)
if r.status_code == 200:
    data = r.json()
    print('count:', data.get('count'))
    if data.get('strategies'):
        first = data['strategies'][0]
        print('first id:', first.get('id'))
        print('trade_count_oos:', first.get('trade_count_oos'))
        print('backtest_trades:', first.get('backtest_trades'))
        print('sharpe_ratio:', first.get('sharpe_ratio'))
else:
    print(r.text)
