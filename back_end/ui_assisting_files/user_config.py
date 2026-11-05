import json
import re
from pathlib import Path

CONFIG_FILE = Path.home() / ".chitinscout" / "config.json"
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def is_valid_email(value: str) -> bool:
    """
        Confirm that the email address follows the email pattern.
    """
    return bool(value and _EMAIL_PATTERN.match(value.strip()))

def _load() -> dict:
    """
        Load the JSON config file to use email address details when making Entrez queries.
    """
    try:
        return json.loads(CONFIG_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def get_email() -> str | None:
    """
        Get the email address of the user as specified and saved to the config file.
    """
    return _load().get("email") or None

def set_email(email: str) -> None:
    """
        Set the user email in the config file.
    """
    config = _load()
    config["email"] = email.strip()
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))