"""Utilities for notifying external social platforms via webhooks or scheduled jobs."""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict

import httpx
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()


def _post(url: str | None, payload: Dict[str, Any]) -> None:
    """Send *payload* to *url* if defined, ignoring network errors."""
    if not url:
        return
    try:
        httpx.post(url, json=payload, timeout=10)
    except Exception:
        pass


def instagram_webhook(event: str, data: Dict[str, Any] | None = None) -> None:
    payload = {"event": event, "data": data or {}, "ts": datetime.utcnow().isoformat()}
    _post(os.getenv("INSTAGRAM_WEBHOOK_URL"), payload)


def youtube_webhook(event: str, data: Dict[str, Any] | None = None) -> None:
    payload = {"event": event, "data": data or {}, "ts": datetime.utcnow().isoformat()}
    _post(os.getenv("YOUTUBE_WEBHOOK_URL"), payload)


def discord_webhook(event: str, data: Dict[str, Any] | None = None) -> None:
    payload = {"event": event, "data": data or {}, "ts": datetime.utcnow().isoformat()}
    _post(os.getenv("DISCORD_WEBHOOK_URL"), payload)


def init_cron() -> None:
    """Start background scheduler with periodic social webhooks."""
    if not scheduler.running:
        scheduler.start()
    scheduler.add_job(lambda: instagram_webhook("cron"), "cron", minute=0)
    scheduler.add_job(lambda: youtube_webhook("cron"), "cron", minute=20)
    scheduler.add_job(lambda: discord_webhook("cron"), "cron", minute=40)
