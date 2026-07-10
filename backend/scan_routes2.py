import sys
sys.path.insert(0, '.')
from app.main import app

for r in app.routes:
    if hasattr(r, 'path'):
        if '/api/strategies/researcher' in r.path or '/api/strategies/pipeline-summary' in r.path or '/api/strategies/compare' in r.path:
            print(r.path, r.name, getattr(r, 'methods', None))
