import sys
import types
import json
from pathlib import Path

from fastapi.testclient import TestClient

# Provide minimal social_hooks before importing agent_server
dummy_hooks = types.ModuleType("integrations.social_hooks")


def init_cron():
    pass


dummy_hooks.init_cron = init_cron  # type: ignore[attr-defined]
sys.modules["integrations.social_hooks"] = dummy_hooks

# Stub profile modules required by agent_server
profile_pkg = types.ModuleType("profile")
points_mod = types.ModuleType("profile.points")
badges_mod = types.ModuleType("profile.badges")


def award_points(user_id: str, reason: str) -> int:  # noqa: D401 - simple stub
    return 0


def get_rankings():  # noqa: D401 - simple stub
    return []


def assign_badge(user_id: str, badge_id: str | None, frame_id: str | None):  # noqa: D401
    return {}


points_mod.award_points = award_points  # type: ignore[attr-defined]
points_mod.get_rankings = get_rankings  # type: ignore[attr-defined]
badges_mod.assign_badge = assign_badge  # type: ignore[attr-defined]

sys.modules["profile"] = profile_pkg
sys.modules["profile.points"] = points_mod
sys.modules["profile.badges"] = badges_mod

import agent_server


class DummyClient:
    def chat(self, messages):
        return "pong"


class DummySubscriber:
    def __init__(self):
        self.sent = []

    async def publish(self, topic, data):
        self.sent.append((topic, data))


def test_chat_and_publish(monkeypatch):
    monkeypatch.setattr(agent_server, "client", DummyClient())
    dummy_sub = DummySubscriber()
    monkeypatch.setattr(agent_server, "subscriber", dummy_sub)
    recorded = []

    def fake_add_entry(**kw):
        recorded.append(kw)

    monkeypatch.setattr(agent_server, "add_entry", fake_add_entry)

    client = TestClient(agent_server.app)
    r = client.post("/chat", json={"sender": "user", "message": "hi"})
    assert r.status_code == 200
    assert r.json()["reply"] == "pong"
    r = client.post("/publish", json={"sender": "user", "message": "hello"})
    assert r.status_code == 200
    assert dummy_sub.sent == [(agent_server.role, "hello")]
    kinds = {e["kind"] for e in recorded}
    assert {"chat", "publish"}.issubset(kinds)
