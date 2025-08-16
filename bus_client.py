import threading
import requests
import os
import anyio
from kb import add_entry

class BusClient:
    def __init__(self, base_url: str, topic: str, handler):
        self.base_url = base_url
        self.topic = topic
        self.handler = handler
        self._stop = threading.Event()
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        with anyio.from_thread.start_blocking_portal() as portal:
            while not self._stop.is_set():
                try:
                    msg = requests.get(f"{self.base_url}/get/{self.topic}", timeout=60).json()
                    sender = msg.get('sender')
                    text = msg.get('text')
                    add_entry('bus_message', self.topic, f"{sender}: {text}")
                    portal.call(self.handler, sender, text)
                except Exception:
                    pass

    def publish(self, topic: str, sender: str, text: str):
        requests.post(f"{self.base_url}/publish", json={'topic': topic, 'sender': sender, 'text': text}, timeout=10)

    def close(self):
        self._stop.set()
