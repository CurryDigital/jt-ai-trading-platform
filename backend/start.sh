#!/bin/bash
cd /home/ubuntu/.openclaw/workspace/jt-ai-trading-platform/backend
export AZURE_OPENAI_API_KEY="9Hjt8RDYsjBflHI9C0qSJRQYSqfb04qgNyjm6JA42AnnV4BKb7qVJQQJ99BFACqBBLyXJ3w3AAABACOGWJK7"
export AZURE_OPENAI_ENDPOINT="https://databricksllmpoc.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT="gpt-4.1-nano"
export AZURE_OPENAI_API_VERSION="2025-03-01-preview"
export SERPER_API_KEY="fbccff7e2b07f4c417387bafadd141b97f1583be"
exec python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
