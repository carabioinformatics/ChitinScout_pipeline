"""Stores user settings (currently the Entrez email) in a file on this computer."""
import json
import re
from pathlib import Path

CONFIG_FILE = Path.home() / ".chitinscout" / "config.json"
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(value: str) -> bool:
    return bool(value and _EMAIL_PATTERN.match(value.strip()))


def _load() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_email() -> str | None:
    return _load().get("email") or None


def set_email(email: str) -> None:
    config = _load()
    config["email"] = email.strip()
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))