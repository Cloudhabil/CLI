from __future__ import annotations

from pathlib import Path
import shutil
import yaml
from profile.badges import badge_paths, frame_paths

CONFIG_PATH = Path("config/avatar_evolution.yaml")
ASSETS_DIR = Path("assets/avatars")
PROFILE_DIR = Path("profile/avatars")


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def determine_stage(lineage: str, points: int) -> str | None:
    cfg = load_config()
    lineage_cfg = cfg.get(lineage, {})
    if not lineage_cfg:
        return None
    stages = sorted(lineage_cfg.items(), key=lambda x: x[1])
    stage = None
    for name, threshold in stages:
        if points >= threshold:
            stage = name
        else:
            break
    return stage


def evolve_avatar(user_id: str, lineage: str, points: int) -> dict:
    """Update avatar for ``user_id`` if ``points`` reaches a new stage.

    Returns a mapping containing the avatar path along with any badges and frames.
    """
    stage = determine_stage(lineage, points)
    if stage is None:
        raise ValueError(f"Unknown lineage '{lineage}' or insufficient data")

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    stage_file = PROFILE_DIR / f"{user_id}.stage"
    prev_stage = stage_file.read_text().strip() if stage_file.exists() else None
    if stage != prev_stage:
        src = ASSETS_DIR / lineage / f"{stage}.png"
        dest = PROFILE_DIR / f"{user_id}.png"
        shutil.copyfile(src, dest)
        stage_file.write_text(stage)
    avatar_path = str((PROFILE_DIR / f"{user_id}.png").resolve())
    return {
        "avatar": avatar_path,
        "badges": badge_paths(user_id),
        "frames": frame_paths(user_id),
    }
