#!/bin/bash
cd /home/ubuntu/.openclaw/workspace/platform/jt-ai-trading-platform/backend

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Run the backend with auto-reload for development
exec python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
