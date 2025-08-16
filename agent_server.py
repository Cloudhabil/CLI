import os
import threading
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, List, Dict, Optional
import yaml

from models.backend import make_client
from kb import add_entry
from bus_client import BusClient

app = FastAPI()

role = os.environ.get("ROLE", "AGENT")
config_model = os.environ.get("MODEL_KIND", "ollama")
config_endpoint = os.environ.get("MODEL_ENDPOINT", "http://127.0.0.1:11434/api/chat")
config_name = os.environ.get("MODEL_NAME", "llama3.1:latest")
client = make_client(config_model, config_endpoint, config_name)

BUS_URL = os.environ.get("BUS_URL")
subscriber: Optional[BusClient] = None
history: List[Dict[str, str]] = []
user_settings: Dict[str, Dict[str, str]] = {}

prompt_path = os.environ.get("PROMPT_FILE")
if prompt_path and os.path.exists(prompt_path):
    with open(prompt_path, "r", encoding="utf-8") as f:
        history.append({"role": "system", "content": f.read().strip()})


class ChatRequest(BaseModel):
    sender: str = ""
    message: str


class SettingsRequest(BaseModel):
    type: str
    language: str


class LayoutRequest(BaseModel):
    layout: Optional[Dict[str, Any]] = None


@app.on_event("startup")
async def startup_event():
    if BUS_URL:
        global subscriber
        subscriber = BusClient(BUS_URL, role, handle_bus_message)
        threading.Thread(target=subscriber.run, daemon=True).start()


def handle_bus_message(msg: Dict[str, str]):
    add_entry(kind="bus_message", topic=role, payload=msg)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest):
    history.append({"role": "user", "content": req.message})
    reply = client.chat(history)
    history.append({"role": "assistant", "content": reply})
    add_entry(kind="chat", role=role, sender=req.sender, message=req.message, reply=reply)
    return {"reply": reply}


@app.post("/wake")
async def wake():
    add_entry(kind="wake", role=role)
    return {"status": "awake"}


@app.post("/handoff")
async def handoff(req: ChatRequest):
    add_entry(kind="handoff", role=role, data=req.message)
    return {"status": "ok"}


@app.post("/publish")
async def publish(req: ChatRequest):
    if subscriber:
        await subscriber.publish(role, req.message)
    add_entry(kind="publish", role=role, data=req.message)
    return {"status": "published"}


@app.patch("/profile/{user_id}/settings")
async def update_settings(user_id: str, req: SettingsRequest):
    user_settings[user_id] = req.dict()
    return {"status": "ok", "user_id": user_id, "settings": user_settings[user_id]}


@app.put("/profile/{user_id}/layout")
async def update_layout(user_id: str, req: LayoutRequest):
    base = Path("profile/layouts")
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{user_id}.yaml"
    if req.layout is None:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}
        return {"status": "ok", "user_id": user_id, "layout": data}
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(req.layout, f)
    return {"status": "saved", "user_id": user_id, "layout": req.layout}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("agent_server:app", host="0.0.0.0", port=port)
