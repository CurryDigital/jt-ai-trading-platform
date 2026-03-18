#!/bin/bash
cd /home/ubuntu/.openclaw/workspace/platform/jt-ai-trading-platform/backend
exec python3 -m uvicorn app.main_minimal:app --host 127.0.0.1 --port 8000 --reload
