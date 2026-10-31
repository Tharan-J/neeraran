#!/usr/bin/env bash
set -e

echo "Starting NEERARAN Platform..."
PYTHONPATH=. python3 -m uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

trap "kill $API_PID 2>/dev/null || true" EXIT

npm run dev --prefix apps/web
