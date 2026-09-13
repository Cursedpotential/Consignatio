from __future__ import annotations

import pytest

from casebible_index import secrets, windows_credentials
from casebible_index.windows_credentials import WindowsCredentialError


def _credential(username: str, password: str) -> windows_credentials._GenericCredential:
    return windows_credentials._GenericCredential(
        username=username,
        blob=password.encode("utf-16-le"),
    )


def test_keyring_rs_target_and_utf16_interoperability() -> None:
    requested_targets: list[str] = []

    def reader(target: str) -> windows_credentials._GenericCredential:
        requested_targets.append(target)
        return _credential("INTAKE_SURREAL_PASSWORD", "test-only-secret")

    result = windows_credentials.read_keyring_rs_password(
        "propria-intake-dev",
        "INTAKE_SURREAL_PASSWORD",
        reader=reader,
    )

    assert result == "test-only-secret"
    assert requested_targets == ["INTAKE_SURREAL_PASSWORD.propria-intake-dev"]


def test_keyring_reader_returns_none_when_record_is_absent() -> None:
    assert (
        windows_credentials.read_keyring_rs_password(
            "propria-intake-dev",
            "INTAKE_SURREAL_PASSWORD",
            reader=lambda _target: None,
        )
        is None
    )


def test_keyring_reader_fails_closed_on_wrong_identity() -> None:
    with pytest.raises(WindowsCredentialError, match="identity"):
        windows_credentials.read_keyring_rs_password(
            "propria-intake-dev",
            "INTAKE_SURREAL_PASSWORD",
            reader=lambda _target: _credential("OTHER_SECRET", "test-only-secret"),
        )


def test_keyring_reader_fails_closed_on_malformed_blob() -> None:
    malformed = windows_credentials._GenericCredential(
        username="INTAKE_SURREAL_PASSWORD",
        blob=b"x",
    )

    with pytest.raises(WindowsCredentialError, match="invalid password encoding"):
        windows_credentials.read_keyring_rs_password(
            "propria-intake-dev",
            "INTAKE_SURREAL_PASSWORD",
            reader=lambda _target: malformed,
        )


def test_surreal_password_uses_keychain_and_not_hkcu(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("INTAKE_SURREAL_PASSWORD", raising=False)
    monkeypatch.setattr(
        secrets,
        "read_keyring_rs_password",
        lambda service, username: f"{service}:{username}:test-only",
    )

    assert secrets.get_secret("INTAKE_SURREAL_PASSWORD") == (
        "propria-intake-dev:INTAKE_SURREAL_PASSWORD:test-only"
    )


def test_process_environment_does_not_override_windows_keychain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("INTAKE_SURREAL_PASSWORD", "process-only-test-secret")
    monkeypatch.setattr(
        secrets,
        "read_keyring_rs_password",
        lambda _service, _username: "keychain-test-secret",
    )

    assert secrets.get_secret("INTAKE_SURREAL_PASSWORD") == "keychain-test-secret"
