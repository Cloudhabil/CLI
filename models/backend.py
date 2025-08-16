import os
from abc import ABC, abstractmethod
from typing import List, Dict

import requests


class BaseChatClient(ABC):
    """Minimal interface for chat model backends."""

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Send chat messages and return the model response."""


class OllamaChat(BaseChatClient):
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


class OpenAIChat(BaseChatClient):
    def __init__(self, endpoint: str, model: str, api_key: str | None = None):
        self.endpoint = endpoint or "https://api.openai.com/v1/chat/completions"
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

    def chat(self, messages: List[Dict[str, str]]) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.model, "messages": messages}
        r = requests.post(self.endpoint, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        return (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )


def make_client(kind: str, endpoint: str, model: str):
    if kind == "ollama":
        return OllamaChat(endpoint, model)
    if kind == "openai":
        return OpenAIChat(endpoint, model)
    raise ValueError(f"unknown model backend {kind}")
