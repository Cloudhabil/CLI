#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install -r requirements.txt
[ -f .env.local ] || cp .env.example .env.local
PYTHONPATH=$ROOT python integrations/google_oauth.py
env PYTHONPATH=$ROOT BUS_URL=http://127.0.0.1:7088 AGENT_SERVER_SECRET=${AGENT_SERVER_SECRET} python orchestrator.py boot &
PID=$!
if [ "$1" != "-NoTUI" ]; then AGENT_SERVER_SECRET=${AGENT_SERVER_SECRET} PYTHONPATH=$ROOT python orchestrator.py shell; fi
wait $PID
