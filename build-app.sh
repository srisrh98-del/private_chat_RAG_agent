#!/usr/bin/env bash
# Build frontend and Electron desktop app. Run from project root.
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "Building frontend..."
cd frontend && npm run build && cd ..

echo "Building desktop app..."
cd desktop && npm run pack && cd ..

echo "Installing Chat Agent.app..."
rm -rf "$ROOT/Chat Agent.app"
cp -R "$ROOT/desktop/dist/mac-arm64/Chat Agent.app" "$ROOT/"

echo "Done. Double-click 'Chat Agent.app' in this folder."
echo "The app opens in its own window (not Safari). Keep it inside: $ROOT"
echo "Ollama must be running for chat to work."
