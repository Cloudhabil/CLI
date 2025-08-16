"""Utility functions for managing user points and rankings."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

# File where points are persisted
POINTS_FILE = Path("profile/points.json")

# Mapping of reasons to point values
POINT_VALUES: Dict[str, int] = {
    "chat": 1,
    "referral": 5,
    "contribution": 10,
}


def _load_points() -> Dict[str, int]:
    """Load existing point totals from disk."""
    if POINTS_FILE.exists():
        with POINTS_FILE.open("r", encoding="utf-8") as fh:
            try:
                return json.load(fh)
            except json.JSONDecodeError:
                return {}
    return {}


def _save_points(data: Dict[str, int]) -> None:
    """Persist point totals to disk."""
    POINTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with POINTS_FILE.open("w", encoding="utf-8") as fh:
        json.dump(data, fh)


def award_points(user_id: str, reason: str) -> int:
    """Award points to *user_id* for *reason*.

    Returns the user's new total.
    """
    data = _load_points()
    delta = POINT_VALUES.get(reason, 0)
    data[user_id] = data.get(user_id, 0) + delta
    _save_points(data)
    return data[user_id]


def get_rankings() -> List[Tuple[str, int]]:
    """Return a list of (user_id, points) sorted by points descending."""
    data = _load_points()
    return sorted(data.items(), key=lambda kv: kv[1], reverse=True)
