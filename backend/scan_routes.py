import sys
sys.path.insert(0, '.')
from app.main import app

for r in app.routes:
    if hasattr(r, 'path'):
        if 'researcher' in r.path.lower() or 'strategies' in r.path.lower():
            print(r.path, getattr(r, 'methods', None))
