import yaml
from models.backend import make_client
from kb import add_entry
from pathlib import Path

CFG = yaml.safe_load(open(Path(__file__).parent / "configs" / "agents.yaml"))
MODEL_CFG = yaml.safe_load(open(Path(__file__).parent / "configs" / "models.yaml"))
admin_model = MODEL_CFG["models"][CFG["admin"]["model"]]
client = make_client(admin_model["kind"], admin_model["endpoint"], admin_model["model"])


def evaluate_ceo_decision(text: str) -> str:
    messages = [
        {"role": "system", "content": "You are the Admin policy engine. classify decision as acceptable or harmful."},
        {"role": "user", "content": text},
    ]
    reply = client.chat(messages).lower()
    verdict = "harmful" if "harm" in reply else "acceptable"
    add_entry(kind="policy", decision=text, verdict=verdict)
    return verdict
