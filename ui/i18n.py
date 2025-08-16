import os
from pathlib import Path
import yaml

_LOCALE_CACHE = {}

def load_strings(lang: str | None = None) -> dict:
    """Load UI strings for the given language from locales/<lang>.yaml.

    Caches loaded locales to avoid repeated disk reads.
    """
    lang = lang or os.environ.get("UI_LANG", "en")
    if lang not in _LOCALE_CACHE:
        loc_file = Path(__file__).resolve().parent.parent / "locales" / f"{lang}.yaml"
        with open(loc_file, "r", encoding="utf-8") as f:
            _LOCALE_CACHE[lang] = yaml.safe_load(f) or {}
    return _LOCALE_CACHE[lang]
