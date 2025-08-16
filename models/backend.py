import requests
from typing import List, Dict, Any


class OllamaChat:
    def __init__(self, endpoint: str, model: str):
        self.endpoint = endpoint
        self.model = model

    def chat(self, messages: List[Dict[str, str]]) -> str:
        payload = {"model": self.model, "messages": messages}
        r = requests.post(self.endpoint, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict):
            return data.get("message", {}).get("content", "")
        return ""


def make_client(kind: str, endpoint: str, model: str):
    if kind == "ollama":
        return OllamaChat(endpoint, model)
    raise ValueError(f"unknown model backend {kind}")
