import json
from pathlib import Path

from fastapi.testclient import TestClient

import bus_server


def test_publish_get_cycle(monkeypatch):
    """Publish and retrieve a message via the bus."""
    recorded = []

    def fake_add_entry(**kw):
        recorded.append(kw)

    monkeypatch.setattr(bus_server, "add_entry", fake_add_entry)
    monkeypatch.setenv("BUS_TOKEN", "secret")

    client = TestClient(bus_server.app)
    msg = json.loads((Path(__file__).parent / "data" / "bus_messages.json").read_text())[0]
    headers = {"Authorization": "Bearer secret"}
    r = client.post("/publish", json=msg, headers=headers)
    assert r.status_code == 200
    r = client.get("/get", params={"topic": msg["topic"]}, headers=headers)
    assert r.status_code == 200
    assert r.json() == msg["data"]
    assert recorded and recorded[0]["kind"] == "bus_message"


def test_reject_invalid_token(monkeypatch):
    monkeypatch.setenv("BUS_TOKEN", "secret")
    client = TestClient(bus_server.app)
    msg = json.loads((Path(__file__).parent / "data" / "bus_messages.json").read_text())[0]
    headers = {"Authorization": "Bearer wrong"}
    r = client.post("/publish", json=msg, headers=headers)
    assert r.status_code == 401
    r = client.get("/get", params={"topic": msg["topic"]}, headers=headers)
    assert r.status_code == 401
    r = client.post("/publish", json=msg)
    assert r.status_code == 403
