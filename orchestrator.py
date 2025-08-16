import os
import subprocess
import time
import yaml
import requests
import typer
from models.backend import make_client
from kb import add_entry
from admin_policy import evaluate_ceo_decision

app = typer.Typer()

with open('configs/models.yaml', 'r', encoding='utf-8') as f:
    MODELS = yaml.safe_load(f)['models']
with open('configs/agents.yaml', 'r', encoding='utf-8') as f:
    AGENTS_CONF = yaml.safe_load(f)

BUS_HOST = os.environ.get('BUS_HOST', '127.0.0.1')
BUS_PORT = int(os.environ.get('BUS_PORT', '7088'))
BUS_URL = f"http://{BUS_HOST}:{BUS_PORT}"

PROCS = []

def spawn_bus():
    p = subprocess.Popen(['python', 'bus_server.py'], env={**os.environ, 'PYTHONUNBUFFERED':'1'})
    PROCS.append(p)
    time.sleep(1)

def spawn_stripe():
    p = subprocess.Popen(['python', 'stripe_server.py'], env={**os.environ, 'PYTHONUNBUFFERED':'1'})
    PROCS.append(p)
    time.sleep(1)

def spawn_agent(role, cfg):
    m = MODELS[cfg['model']]
    env = {**os.environ,
           'AGENT_ROLE': role,
           'MODEL_KIND': m['kind'],
           'MODEL_ENDPOINT': m['endpoint'],
           'MODEL_NAME': m['model'],
           'AGENT_PROMPT': cfg['prompt'],
           'BUS_URL': BUS_URL}
    cmd = ['uvicorn', 'agent_server:app', '--host', os.environ.get('AGENT_HOST','127.0.0.1'), '--port', str(cfg['port'])]
    p = subprocess.Popen(cmd, env=env)
    PROCS.append(p)
    time.sleep(1)

def wake_agent(role, cfg):
    url = f"http://{os.environ.get('AGENT_HOST','127.0.0.1')}:{cfg['port']}/wake"
    for _ in range(10):
        try:
            requests.post(url, timeout=5)
            return
        except Exception:
            time.sleep(0.5)

def wake_all():
    for role in AGENTS_CONF['admin']['wake_order']:
        wake_agent(role, AGENTS_CONF['agents'][role])

def route(sender, target, text):
    requests.post(f"{BUS_URL}/publish", json={'topic': target, 'sender': sender, 'text': text}, timeout=5)

def check_ceo(decision_summary: str):
    verdict = evaluate_ceo_decision(decision_summary)
    add_entry('policy', 'CEO', verdict)
    if verdict == 'harmful':
        route('ADMIN', 'CHRO', decision_summary)
        route('ADMIN', 'COO', decision_summary)
    return verdict

@app.command()
def boot():
    spawn_bus()
    spawn_stripe()
    for role, cfg in AGENTS_CONF['agents'].items():
        spawn_agent(role, cfg)
    wake_all()
    add_entry('orchestrator', 'boot', 'system online')
    while True:
        time.sleep(3600)

@app.command()
def shell():
    os.environ['BUS_URL'] = BUS_URL
    subprocess.call(['python', 'admin_tui.py'])

if __name__ == '__main__':
    app()
