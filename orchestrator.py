import os
import subprocess
import time
import yaml
import typer
import requests
from pathlib import Path
from admin_policy import evaluate_ceo_decision

app = typer.Typer()
ROOT = Path(__file__).parent
CONFIG_AGENTS = yaml.safe_load(open(ROOT / "configs" / "agents.yaml"))
CONFIG_MODELS = yaml.safe_load(open(ROOT / "configs" / "models.yaml"))

processes = []


def spawn_bus():
    p = subprocess.Popen(["python", "bus_server.py"])
    processes.append(p)
    os.environ["BUS_URL"] = "http://127.0.0.1:7088"
    _wait_health("http://127.0.0.1:7088/health")


def spawn_stripe():
    p = subprocess.Popen(["python", "stripe_server.py"])
    processes.append(p)
    _wait_health("http://127.0.0.1:7077/health")


def spawn_agent(role: str, info: dict):
    model_cfg = CONFIG_MODELS["models"][info["model"]]
    env = os.environ.copy()
    env.update(
        {
            "ROLE": role,
            "PORT": str(info["port"]),
            "PROMPT_FILE": str(info["prompt"]),
            "MODEL_KIND": model_cfg["kind"],
            "MODEL_ENDPOINT": model_cfg["endpoint"],
            "MODEL_NAME": model_cfg["model"],
            "BUS_URL": os.environ.get("BUS_URL", ""),
        }
    )
    p = subprocess.Popen(["python", "agent_server.py"], env=env)
    processes.append(p)
    _wait_health(f"http://127.0.0.1:{info['port']}/health")
    requests.post(f"http://127.0.0.1:{info['port']}/wake")


def _wait_health(url: str, retries: int = 20):
    for _ in range(retries):
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError(f"service {url} not healthy")


def route(sender: str, target: str, text: str):
    bus = os.environ.get("BUS_URL", "http://127.0.0.1:7088")
    requests.post(f"{bus}/publish", json={"topic": target, "data": {"sender": sender, "text": text}})


def check_ceo(decision_summary: str):
    verdict = evaluate_ceo_decision(decision_summary)
    if verdict == "harmful":
        route("admin", "CHRO", decision_summary)
        route("admin", "COO", decision_summary)
    return verdict


@app.command()
def boot():
    spawn_bus()
    spawn_stripe()
    for role in CONFIG_AGENTS["admin"]["wake_order"]:
        spawn_agent(role, CONFIG_AGENTS["agents"][role])
    while True:
        time.sleep(60)


@app.command()
def shell():
    from admin_tui import main as tui_main

    tui_main(route, check_ceo)


if __name__ == "__main__":
    app()
