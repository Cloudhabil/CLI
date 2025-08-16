import requests
import threading
import time
from typing import Callable, Dict


class BusClient:
    def __init__(self, base_url: str, topic: str, handler: Callable[[Dict], None]):
        self.base_url = base_url.rstrip('/')
        self.topic = topic
        self.handler = handler
        self._stop = False

    def run(self):
        while not self._stop:
            try:
                r = requests.get(f"{self.base_url}/get", params={"topic": self.topic}, timeout=60)
                if r.status_code == 200:
                    self.handler(r.json())
            except Exception:
                time.sleep(1)

    def stop(self):
        self._stop = True

    async def publish(self, topic: str, data: str):
        requests.post(f"{self.base_url}/publish", json={"topic": topic, "data": {"text": data}})
