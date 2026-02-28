#!/usr/bin/env bash
# One-click launcher: starts backend and frontend. Run from project root.
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ ! -d "backend/venv" ]; then
  echo "Run install first: ./install.sh"
  exit 1
fi

export CHAT_AGENT_ROOT="$ROOT"

# Backend from backend dir so "app" package is found
echo "Starting backend on http://127.0.0.1:8000"
(cd backend && "$ROOT/backend/venv/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8000) &
BACKEND_PID=$!

sleep 2
echo "Starting frontend on http://127.0.0.1:5173"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

cleanup() {
  kill $BACKEND_PID 2>/dev/null || true
  kill $FRONTEND_PID 2>/dev/null || true
}
trap cleanup EXIT

wait
