import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_secrets_checked = False
_secrets_available = False


def _check_secrets_file() -> bool:
    global _secrets_checked, _secrets_available
    if _secrets_checked:
        return _secrets_available

    _secrets_checked = True
    candidates = [
        Path(".streamlit/secrets.toml"),
        Path.home() / ".streamlit" / "secrets.toml",
    ]
    _secrets_available = any(path.is_file() for path in candidates)
    return _secrets_available


def get_setting(key: str, default: str = "") -> str:
    env_value = os.getenv(key)
    if env_value:
        return env_value

    if _check_secrets_file():
        try:
            import streamlit as st

            if key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass

    return default
