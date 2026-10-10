"""Private Markdown records, strict JSON frontmatter, and cooperative locking.

Writers in this package share an advisory vault lock. This protects cooperating
processes, not against a hostile process with the same filesystem permissions.
Markdown is authoritative; JSON is only used for configuration and flat metadata.
"""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import threading
from typing import Iterator


class StorageError(ValueError):
    """A record or filesystem location cannot be handled safely."""


ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{0,79}\Z", re.ASCII)
KEY_PATTERN = re.compile(r"[a-z][a-z0-9_]*\Z", re.ASCII)
SECTIONS = ("roles", "evidence", "feedback", "scans", "employers", "decisions")
MAX_RECORD_BYTES = 2 * 1024 * 1024
MAX_JSON_BYTES = 8 * 1024 * 1024
_LOCKS = threading.local()


def require_id(value: object) -> str:
    if not isinstance(value, str) or ID_PATTERN.fullmatch(value) is None:
        raise StorageError("ID must be lowercase letters, digits or hyphens, start with a letter or digit, and contain 1–80 characters")
    return value


def safe_path(path: Path | str) -> Path:
    """Check each existing component without resolving away traversal/symlinks."""
    result = Path(path).expanduser()
    if ".." in result.parts:
        raise StorageError("Parent traversal is not allowed")
    result = result.absolute()
    for component in reversed((result, *result.parents)):
        try:
            mode = component.lstat().st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise StorageError("Symlink paths are not allowed")
        if component != result and not stat.S_ISDIR(mode):
            raise StorageError("A parent path is not a directory")
    return result


def secure_mkdir(path: Path | str) -> Path:
    target = safe_path(path)
    missing = []
    current = target
    while not current.exists():
        missing.append(current)
        current = current.parent
    for directory in reversed(missing):
        try:
            directory.mkdir(mode=0o700)
        except FileExistsError:
            safe_path(directory)
    if not target.is_dir():
        raise StorageError("Expected a directory")
    return target


@contextmanager
def vault_lock(vault: Path | str) -> Iterator[None]:
    """Re-entrant per thread; flock also serialises other threads/processes."""
    root = safe_path(vault)
    if not root.is_dir():
        raise StorageError("Vault directory does not exist")
    key = str(root)
    active = getattr(_LOCKS, "active", None)
    if active is None:
        active = _LOCKS.active = {}
    if key in active:
        active[key][1] += 1
        try:
            yield
        finally:
            active[key][1] -= 1
        return
    path = safe_path(root / ".vault.lock")
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise StorageError("Vault lock must be a regular file")
        os.fchmod(fd, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        active[key] = [fd, 1]
        try:
            yield
        finally:
            del active[key]
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def _lock_root(path: Path) -> Path:
    for parent in path.parents:
        if (parent / ".private-vault").exists():
            safe_path(parent / ".private-vault")
            return parent
    # Low-level record operations also work outside an initialised vault.
    # In that case their existing parent is the cooperative lock boundary.
    if not path.parent.is_dir():
        raise StorageError("Parent directory does not exist")
    return path.parent


def _reject_constant(value: str) -> None:
    raise StorageError("Non-finite numbers are not valid JSON")


def _object_without_duplicates(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise StorageError("Duplicate JSON key")
        result[key] = value
    return result


def strict_json_loads(text: str) -> object:
    try:
        value = json.loads(text, object_pairs_hook=_object_without_duplicates, parse_constant=_reject_constant)
        # Also reject numeric overflow such as 1e999, which the decoder accepts.
        json.dumps(value, allow_nan=False)
        return value
    except (json.JSONDecodeError, TypeError, ValueError, RecursionError) as error:
        if isinstance(error, StorageError):
            raise
        raise StorageError("Malformed JSON data") from error


def _read_text(path: Path | str, *, limit: int) -> str:
    target = safe_path(path)
    if not target.is_file():
        raise StorageError("Expected an existing regular file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(target, flags)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise StorageError("Expected a regular file")
        with os.fdopen(fd, "rb", closefd=False) as handle:
            raw = handle.read(limit + 1)
        if len(raw) > limit:
            raise StorageError("File exceeds the supported size limit")
        return raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise StorageError("File is not valid UTF-8") from error
    finally:
        os.close(fd)


def read_json(path: Path | str) -> object:
    return strict_json_loads(_read_text(path, limit=MAX_JSON_BYTES))


def load_config(vault: Path | str) -> dict:
    root = safe_path(vault)
    marker = safe_path(root / ".private-vault")
    if not marker.is_file():
        raise StorageError("Not an initialised private vault (missing .private-vault)")
    value = read_json(root / "config.json")
    if not isinstance(value, dict):
        raise StorageError("Vault configuration must be a JSON object")
    return value


def read_record(path: Path) -> tuple[dict, str]:
    text = _read_text(path, limit=MAX_RECORD_BYTES)
    # Only LF delimits metadata lines; JSON strings may contain U+2028/U+2029.
    # Splitting on all Unicode line separators would corrupt valid strings.
    lines = text.split("\n")
    if not lines or lines[0].rstrip("\r") != "---":
        raise StorageError("Record must start with a frontmatter delimiter")
    metadata: dict = {}
    for index, line in enumerate(lines[1:], 1):
        if line.rstrip("\r") == "---":
            return metadata, "\n".join(lines[index + 1:])
        line = line.rstrip("\r")
        key, separator, raw = line.partition(":")
        if not separator or KEY_PATTERN.fullmatch(key) is None or not raw.strip():
            raise StorageError("Frontmatter requires one key: JSON-value per line")
        if key in metadata:
            raise StorageError("Duplicate frontmatter key")
        metadata[key] = strict_json_loads(raw.strip())
    raise StorageError("Record has no closing frontmatter delimiter")


def _record_text(metadata: dict, body: str) -> str:
    if not isinstance(metadata, dict) or not isinstance(body, str):
        raise StorageError("Record requires a metadata object and Markdown string")
    lines = ["---\n"]
    for key, value in metadata.items():
        if not isinstance(key, str) or KEY_PATTERN.fullmatch(key) is None:
            raise StorageError("Invalid frontmatter key")
        try:
            encoded = json.dumps(value, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError, RecursionError) as error:
            raise StorageError("Metadata values must be JSON-compatible") from error
        lines.append(f"{key}: {encoded}\n")
    lines.append("---\n")
    lines.append(body)
    text = "".join(lines)
    if len(text.encode("utf-8")) > MAX_RECORD_BYTES:
        raise StorageError("Record exceeds the supported size limit")
    return text


def atomic_write_text(path: Path | str, text: str, *, overwrite: bool = True) -> None:
    if not isinstance(text, str):
        raise StorageError("Text must be a string")
    target = safe_path(path)
    root = _lock_root(target)
    with vault_lock(root):
        target = safe_path(target)
        if not target.parent.is_dir():
            raise StorageError("Parent directory does not exist")
        if target.exists() and not target.is_file():
            raise StorageError("Cannot replace a non-regular file")
        if target.exists() and not overwrite:
            raise StorageError("Refusing to overwrite an existing file")
        fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
        temporary_path = Path(temporary)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
                os.fchmod(handle.fileno(), 0o600)
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            safe_path(target)
            if overwrite:
                os.replace(temporary_path, target)
            else:
                # Atomic no-clobber publication, even for non-cooperating writers.
                os.link(temporary_path, target, follow_symlinks=False)
                temporary_path.unlink()
            directory_fd = os.open(target.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            temporary_path.unlink(missing_ok=True)


def write_record(path: Path, metadata: dict, body: str, *, overwrite: bool = True) -> None:
    atomic_write_text(path, _record_text(metadata, body), overwrite=overwrite)


def record_paths(vault: Path | str, section: str) -> list[Path]:
    if section not in SECTIONS:
        raise StorageError("Unknown record section")
    directory = safe_path(safe_path(vault) / section)
    if not directory.exists():
        return []
    if not directory.is_dir():
        raise StorageError("Record section is not a directory")
    paths = []
    for path in sorted(directory.iterdir()):
        safe_path(path)
        if path.suffix == ".md":
            if not path.is_file():
                raise StorageError("Markdown records must be regular files")
            paths.append(path)
    return paths


def list_records(vault: Path, section: str) -> list[dict]:
    return [read_record(path)[0] for path in record_paths(vault, section)]
