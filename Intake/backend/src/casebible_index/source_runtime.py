"""Source identity and process exclusion. No remote requests or file deletion."""
from __future__ import annotations

import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path, PureWindowsPath


class SourceBusyError(RuntimeError):
    pass


@contextmanager
def source_lock(lock_dir: Path, source_id: str):
    """OS-owned lock released on process exit; stale lock files are harmless."""
    lock_dir.mkdir(parents=True, exist_ok=True)
    filename = hashlib.sha256(source_id.casefold().encode()).hexdigest() + ".lock"
    stream = (lock_dir / filename).open("a+b")
    acquired = False
    try:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except OSError as exc:
            raise SourceBusyError("This source already has an active Intake index process") from exc
        yield
    finally:
        if acquired:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


def resolve_source_alias(
    source: Path, source_id: str, registry_path: Path | None,
) -> tuple[Path, str]:
    """Map explicit Windows aliases onto one preferred root and portable ID.

    No mount discovery or remote probing. A registered subfolder scope gets the
    same derived ID whichever drive alias was used. Unregistered V:/Y: fail closed.
    """
    requested = PureWindowsPath(str(source))
    if registry_path is None:
        if requested.drive.casefold() in {"v:", "y:"}:
            raise ValueError("V:/Y: indexing requires INTAKE_SOURCE_REGISTRY for mount aliases")
        return source, source_id
    if registry_path.stat().st_size > 65536:
        raise ValueError("Source registry exceeds 64 KiB")
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    entries = data.get("sources") if isinstance(data, dict) else None
    if not isinstance(entries, list) or len(entries) > 100:
        raise ValueError("Invalid source registry")
    roots: list[tuple[PureWindowsPath, PureWindowsPath, str]] = []
    ids: set[str] = set()
    for entry in entries:
        identity = entry["source_id"]
        preferred = PureWindowsPath(entry["preferred_root"])
        aliases = entry["aliases"]
        if not isinstance(identity, str) or not identity.strip() or identity.casefold() in ids:
            raise ValueError("Source registry IDs must be unique nonempty strings")
        ids.add(identity.casefold())
        if not isinstance(aliases, list) or not preferred.is_absolute():
            raise ValueError("Source aliases and absolute preferred root required")
        for raw in dict.fromkeys([str(preferred), *aliases]):
            root = PureWindowsPath(raw)
            if not root.is_absolute() or ".." in root.parts:
                raise ValueError("Source alias must be an absolute normalized Windows path")
            if any(
                root.is_relative_to(other) or other.is_relative_to(root) for other, _, _ in roots
            ):
                raise ValueError("Overlapping source aliases are ambiguous")
            roots.append((root, preferred, identity))
    for root, preferred, identity in roots:
        if requested.is_relative_to(root):
            relative = requested.relative_to(root)
            if ".." in relative.parts:
                raise ValueError("Parent traversal is not a source scope")
            suffix = relative.as_posix().casefold()
            canonical_id = identity if suffix == "." else identity + "/" + suffix
            if source_id not in {"casebible", canonical_id}:
                raise ValueError("Requested source ID conflicts with registered alias identity")
            return Path(str(preferred / relative)), canonical_id
    if requested.drive.casefold() in {"v:", "y:"}:
        raise ValueError("Mount source is not registered")
    return source, source_id
