from __future__ import annotations

import os


def get_secret(name: str) -> str | None:
    """Read a secret without logging it; on Windows also check the HKCU environment key."""

    value = os.getenv(name)
    if value:
        return value
    if os.name != "nt":
        return None
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            registry_value, _ = winreg.QueryValueEx(key, name)
        cleaned = str(registry_value).strip()
        return cleaned or None
    except (FileNotFoundError, OSError):
        return None
