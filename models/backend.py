import requests

class OllamaChat:
    def __init__(self, endpoint: str, model: str):
        self.endpoint = endpoint
        self.model = model

    def chat(self, messages):
        payload = {"model": self.model, "messages": messages}
        r = requests.post(self.endpoint, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        return data.get("message", {}).get("content", "")


def make_client(kind: str, endpoint: str, model: str):
    if kind == "ollama":
        return OllamaChat(endpoint, model)
    raise ValueError(f"unsupported model kind: {kind}")
