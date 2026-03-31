#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source backend/.venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
echo "Backend started on :8000"
echo "Overlay: open overlay/dist/index.html in OBS browser source"
