from __future__ import annotations

import ctypes
import os
from collections.abc import Callable
from ctypes import wintypes
from dataclasses import dataclass

_CRED_TYPE_GENERIC = 1
_ERROR_NOT_FOUND = 1168
_IS_WINDOWS = os.name == "nt"


class WindowsCredentialError(RuntimeError):
    """A safe-to-report Windows Credential Manager lookup failure."""


@dataclass(frozen=True)
class _GenericCredential:
    username: str
    blob: bytes


class _CredentialAttributeW(ctypes.Structure):
    _fields_ = [
        ("Keyword", wintypes.LPWSTR),
        ("Flags", wintypes.DWORD),
        ("ValueSize", wintypes.DWORD),
        ("Value", ctypes.POINTER(ctypes.c_ubyte)),
    ]


class _CredentialW(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.POINTER(_CredentialAttributeW)),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


def _read_generic_credential(target: str) -> _GenericCredential | None:
    if not _IS_WINDOWS:
        return None

    advapi32 = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    cred_read = advapi32.CredReadW
    cred_read.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.POINTER(_CredentialW)),
    ]
    cred_read.restype = wintypes.BOOL
    cred_free = advapi32.CredFree
    cred_free.argtypes = [ctypes.c_void_p]
    cred_free.restype = None

    credential_pointer = ctypes.POINTER(_CredentialW)()
    if not cred_read(target, _CRED_TYPE_GENERIC, 0, ctypes.byref(credential_pointer)):
        error_code = ctypes.get_last_error()
        if error_code == _ERROR_NOT_FOUND:
            return None
        raise WindowsCredentialError(
            f"Windows Credential Manager lookup failed (error {error_code})"
        )

    try:
        credential = credential_pointer.contents
        username = credential.UserName or ""
        blob = (
            ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize)
            if credential.CredentialBlobSize
            else b""
        )
        return _GenericCredential(username=username, blob=blob)
    finally:
        cred_free(credential_pointer)


def read_keyring_rs_password(
    service: str,
    username: str,
    *,
    reader: Callable[[str], _GenericCredential | None] | None = None,
) -> str | None:
    """Read a password written by keyring-rs from Windows Credential Manager.

    keyring-rs maps ``(service, username)`` to the Windows Generic Credential
    target ``username.service`` and writes password text as UTF-16 little endian.
    The username is checked again after lookup so a malformed or manually
    replaced record fails closed.
    """

    if not service or not username:
        raise ValueError("service and username must be non-empty")
    if not _IS_WINDOWS:
        return None

    credential = (reader or _read_generic_credential)(f"{username}.{service}")
    if credential is None:
        return None
    if credential.username != username:
        raise WindowsCredentialError("Windows credential identity did not match the request")
    if len(credential.blob) % 2:
        raise WindowsCredentialError("Windows credential contains an invalid password encoding")
    try:
        password = credential.blob.decode("utf-16-le")
    except UnicodeDecodeError as exc:
        raise WindowsCredentialError(
            "Windows credential contains an invalid password encoding"
        ) from exc
    return password or None
