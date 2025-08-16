"""Client for interacting with the message bus.

All network requests are wrapped in exception handling. Any errors are
recorded to the knowledge base via :func:`kb.add_entry`. Both GET and POST
operations support an optional retry mechanism with exponential backoff,
configurable via the ``retries`` and ``backoff`` parameters on
``BusClient``.
"""

import os
import requests
import time
from typing import Callable, Dict, Optional

from kb import add_entry


class BusClient:
    def __init__(
        self,
        base_url: str,
        topic: str,
        handler: Callable[[Dict], None],
        *,
        retries: int = 0,
        backoff: float = 0.0,
        token: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip('/')
        self.topic = topic
        self.handler = handler
        self.retries = retries
        self.backoff = backoff
        self.token = token or os.environ.get("BUS_TOKEN")
        self._stop = False

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        retries: Optional[int] = None,
        backoff: Optional[float] = None,
        **kwargs,
    ):
        retries = self.retries if retries is None else retries
        backoff = self.backoff if backoff is None else backoff
        url = f"{self.base_url}/{endpoint}"
        headers = kwargs.pop("headers", {})
        if self.token:
            headers.setdefault("Authorization", f"Bearer {self.token}")
        for attempt in range(retries + 1):
            try:
                return requests.request(method, url, timeout=60, headers=headers, **kwargs)
            except Exception as exc:  # pragma: no cover - logging path
                add_entry(kind="bus_client_error", data=f"{method.upper()} {url} failed: {exc}")
                if attempt < retries:
                    delay = backoff * (2 ** attempt)
                    if delay:
                        time.sleep(delay)
        return None

    def run(self):
        while not self._stop:
            r = self._request("get", "get", params={"topic": self.topic})
            if r and r.status_code == 200:
                self.handler(r.json())
            else:
                time.sleep(1)

    def stop(self):
        self._stop = True

    async def publish(
        self,
        topic: str,
        data: str,
        *,
        retries: Optional[int] = None,
        backoff: Optional[float] = None,
    ):
        self._request(
            "post",
            "publish",
            retries=retries,
            backoff=backoff,
            json={"topic": topic, "data": {"text": data}},
        )
