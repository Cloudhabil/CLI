from pathlib import Path
import yaml

LOCALES_DIR = Path(__file__).resolve().parent / "locales"


def load_texts(lang: str) -> dict:
    """Load localized UI strings for the given language code."""
    path = LOCALES_DIR / f"{lang}.yaml"
    if not path.exists():
        path = LOCALES_DIR / "en.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
