from __future__ import annotations

import os

from .windows_credentials import read_keyring_rs_password

_WINDOWS_KEYCHAIN_SERVICE = "propria-intake-dev"
_WINDOWS_KEYCHAIN_ONLY = frozenset({"INTAKE_SURREAL_PASSWORD"})


def get_secret(name: str) -> str | None:
    """Read a secret without logging it or returning secret-bearing diagnostics.

    ``INTAKE_SURREAL_PASSWORD`` is keychain-only on Windows. It is never read
    from either the process environment or the ordinary HKCU Environment key,
    because a process environment value may itself have been inherited from
    that registry location. Non-Windows deployments may supply it through their
    runtime's injected process environment.
    """

    if os.name == "nt" and name in _WINDOWS_KEYCHAIN_ONLY:
        return read_keyring_rs_password(_WINDOWS_KEYCHAIN_SERVICE, name)
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
