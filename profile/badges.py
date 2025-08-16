"""Utilities for assigning and retrieving user badges and frames."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

REWARDS_FILE = Path("profile/badges.json")


def _load() -> Dict[str, Dict[str, List[str]]]:
    if REWARDS_FILE.exists():
        try:
            with REWARDS_FILE.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
                return {
                    uid: {
                        "badges": info.get("badges", []),
                        "frames": info.get("frames", []),
                    }
                    for uid, info in data.items()
                }
        except json.JSONDecodeError:
            pass
    return {}


def _save(data: Dict[str, Dict[str, List[str]]]) -> None:
    REWARDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with REWARDS_FILE.open("w", encoding="utf-8") as fh:
        json.dump(data, fh)


def assign_badge(
    user_id: str, badge_id: Optional[str] = None, frame_id: Optional[str] = None
) -> Dict[str, List[str]]:
    """Assign *badge_id* and/or *frame_id* to *user_id*.

    Returns the user's updated rewards.
    """
    data = _load()
    rewards = data.setdefault(user_id, {"badges": [], "frames": []})
    if badge_id and badge_id not in rewards["badges"]:
        rewards["badges"].append(badge_id)
    if frame_id and frame_id not in rewards["frames"]:
        rewards["frames"].append(frame_id)
    _save(data)
    return rewards


def get_rewards(user_id: str) -> Dict[str, List[str]]:
    """Return rewards for *user_id*."""
    data = _load()
    return data.get(user_id, {"badges": [], "frames": []})


def badge_paths(user_id: str) -> List[str]:
    """Return absolute paths to badges for *user_id*."""
    return [str(Path("assets/badges") / f"{bid}.png") for bid in get_rewards(user_id)["badges"]]


def frame_paths(user_id: str) -> List[str]:
    """Return absolute paths to frames for *user_id*."""
    return [str(Path("assets/frames") / f"{fid}.png") for fid in get_rewards(user_id)["frames"]]
