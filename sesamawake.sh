#!/bin/bash
set -e
VENV=.venv
[ ! -d "$VENV" ] && python3 -m venv $VENV
source $VENV/bin/activate
pip install -r requirements.txt >/dev/null
[ ! -f .env.local ] && [ -f .env.example ] && cp .env.example .env.local
set -a; source .env.local; set +a
python -m integrations.google_oauth >/dev/null
python orchestrator.py boot &
if [ "$1" != "-NoTUI" ]; then
  python orchestrator.py shell
fi
