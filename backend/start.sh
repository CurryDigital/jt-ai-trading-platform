#!/bin/bash
cd /home/ubuntu/.hermes/profiles/qr_frontend/workspace/jt-ai-trading-platform/backend

# Restore PATH stripped by some parent shells
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin:$PATH"

# Load environment variables from .env file
set -a
source .env
set +a

# Run the backend bound to all interfaces (Cloudflare origin expects 0.0.0.0:8000)
exec .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log
