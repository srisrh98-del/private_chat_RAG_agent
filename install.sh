#!/usr/bin/env bash
# Install backend (venv + deps) and frontend (npm). Run from project root.
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "Creating backend venv..."
python3 -m venv backend/venv
backend/venv/bin/pip install -r backend/requirements.txt

echo "Installing frontend deps..."
cd frontend && npm install && cd ..

echo "Done. Add PDFs to data/docs/ then run: ./run.sh"
