import importlib
import os

from core import settings as core_settings


def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("BUS_BASE_URL", "http://localhost:9999")
    importlib.reload(core_settings)
    assert core_settings.settings.BUS_BASE_URL.endswith(":9999")
