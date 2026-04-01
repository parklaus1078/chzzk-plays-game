#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source backend/.venv/bin/activate
cd backend
python run.py &
echo "Backend started on :8080"
echo "Overlay: open overlay/dist/index.html in OBS browser source"
