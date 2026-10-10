"""Private, disposable SQLite search over explicitly allowed Markdown roots.

Canonical Markdown is never updated. The complete projection is rebuilt under
the same cooperative vault lock as record writes, then atomically replaced.
No extension loading, network access, FTS query language or JSON ledger is used.
"""
from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import stat
import tempfile

MAX_DOCUMENT_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_DOCUMENTS = 10000
MAX_DIRECTORY_DEPTH = 12
_ROOTS = ("profile", "roles", "evidence", "employers", "applications", "feedback", "scans", "decisions")
_EXCLUDED = frozenset({
    "output", "secrets", "secret", "credentials", "credential", "passwords", "tokens", "private-keys",
    "backups", "backup", "system", "proc", "sys", "dev", "etc", "node_modules", "__pycache__", "venv",
})


def _excluded(path: Path) -> bool:
    name = path.name.casefold()
    stem = path.stem.casefold()
    return (name.startswith(".") or name in _EXCLUDED or stem in _EXCLUDED or
            any(stem.startswith(prefix + "-") or stem.startswith(prefix + "_")
                for prefix in ("secrets", "credentials", "passwords", "tokens")))


def _paths(root: Path):
    """Walk allowlisted roots only, refusing links rather than following them."""
    from .storage import safe_path

    def walk(directory, depth):
        if depth > MAX_DIRECTORY_DEPTH:
            raise ValueError("Index document tree exceeds the depth limit")
        safe_path(directory)
        if not directory.is_dir():
            raise ValueError("Index source root must be a directory")
        for entry in sorted(directory.iterdir(), key=lambda path: path.name):
            if _excluded(entry):
                continue
            safe_path(entry)
            mode = entry.lstat().st_mode
            if stat.S_ISDIR(mode):
                yield from walk(entry, depth + 1)
            elif entry.suffix.casefold() == ".md":
                if not stat.S_ISREG(mode):
                    raise ValueError("Indexed Markdown must be a regular file")
                yield entry

    start = safe_path(root / "00-start-here.md")
    if start.exists():
        if not start.is_file():
            raise ValueError("Start document must be a regular file")
        yield start
    for name in _ROOTS:
        directory = safe_path(root / name)
        if directory.exists():
            yield from walk(directory, 0)


def _read_markdown(path: Path) -> str:
    from .storage import safe_path

    target = safe_path(path)
    if not target.is_file():
        raise ValueError("Indexed Markdown must be a regular file")
    descriptor = os.open(target, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_DOCUMENT_BYTES:
            raise ValueError("Index document is not regular or exceeds the size limit")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(MAX_DOCUMENT_BYTES + 1)
        if len(raw) > MAX_DOCUMENT_BYTES:
            raise ValueError("Index document exceeds the size limit")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("Indexed Markdown must be UTF-8") from None
        if "\x00" in text:
            raise ValueError("Indexed Markdown cannot contain NUL bytes")
        return text
    finally:
        os.close(descriptor)


def _database_path(vault: Path):
    from .storage import safe_path

    root = safe_path(vault)
    if not root.is_dir():
        raise ValueError("Vault directory does not exist")
    target = safe_path(root / "output" / "search.sqlite3")
    if target.exists() and not target.is_file():
        raise ValueError("Index must be a regular SQLite file")
    return root, target


def build_index(vault: Path) -> int:
    """Rebuild ``output/search.sqlite3`` and return the document count.

    Only Markdown in the documented roots is indexed. Hidden paths, output,
    backup, credential and system directories are excluded. Symlinks in the
    traversed tree cause a failure, leaving an existing projection intact.
    """
    from .storage import safe_path, secure_mkdir, vault_lock

    root, target = _database_path(vault)
    with vault_lock(root):
        _, target = _database_path(root)
        documents = []
        total = 0
        for path in _paths(root):
            if len(documents) >= MAX_DOCUMENTS:
                raise ValueError("Index exceeds the document count limit")
            text = _read_markdown(path)
            total += len(text.encode("utf-8"))
            if total > MAX_TOTAL_BYTES:
                raise ValueError("Index exceeds the total document size limit")
            documents.append((path.relative_to(root).as_posix(), text))
        secure_mkdir(target.parent)
        descriptor, name = tempfile.mkstemp(prefix=".search-", suffix=".sqlite3", dir=target.parent)
        temporary = Path(name)
        os.fchmod(descriptor, 0o600)
        os.close(descriptor)
        try:
            connection = sqlite3.connect(temporary)
            try:
                connection.execute("PRAGMA trusted_schema = OFF")
                connection.execute("PRAGMA journal_mode = DELETE")
                connection.execute("PRAGMA synchronous = FULL")
                connection.execute("CREATE TABLE documents (path TEXT PRIMARY KEY NOT NULL, content TEXT NOT NULL)")
                connection.executemany("INSERT INTO documents(path, content) VALUES (?, ?)", documents)
                connection.commit()
                actual = connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
                if actual != len(documents):
                    raise ValueError("Index document count did not verify")
            finally:
                connection.close()
            with temporary.open("rb") as handle:
                os.fsync(handle.fileno())
            safe_path(target)
            os.replace(temporary, target)
            directory = os.open(target.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            return len(documents)
        except sqlite3.Error:
            raise ValueError("Could not rebuild the private search index") from None
        finally:
            temporary.unlink(missing_ok=True)
            # SQLite normally removes the rollback journal on close.
            Path(str(temporary) + "-journal").unlink(missing_ok=True)


def _snippet(content: str, query: str) -> str:
    text = " ".join(content.split())
    position = text.casefold().find(query.casefold())
    start = max(0, position - 90) if position >= 0 else 0
    end = min(len(text), start + 320)
    return ("…" if start else "") + text[start:end] + ("…" if end < len(text) else "")


def search(vault: Path, query: str, limit: int = 10) -> list[dict]:
    """Search a previously built projection using escaped literal substrings.

    Paths are vault-relative, snippets are plain untrusted text, and ordering is
    deterministic. Callers rendering results must escape snippets themselves.
    Rebuild after Markdown changes; the index is not an authoritative ledger.
    """
    from .storage import vault_lock

    if not isinstance(query, str) or len(query) > 4096:
        raise ValueError("Search query must be text of at most 4096 characters")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("Search limit must be an integer from 1 to 100")
    query = query.strip()
    if not query:
        return []
    root, target = _database_path(vault)
    pattern = "%" + query.casefold().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    with vault_lock(root):
        _, target = _database_path(root)
        if not target.is_file():
            raise ValueError("Search index is missing; rebuild it with the index command")
        if target.stat().st_size > MAX_TOTAL_BYTES * 3:
            raise ValueError("Search index exceeds its supported size; rebuild it")
        connection = None
        try:
            connection = sqlite3.connect(target.as_uri() + "?mode=ro&immutable=1", uri=True)
            connection.execute("PRAGMA trusted_schema = OFF")
            connection.execute("PRAGMA query_only = ON")
            connection.create_function("casefold", 1, lambda value: value.casefold(), deterministic=True)
            rows = connection.execute(
                "SELECT path, content FROM documents "
                "WHERE casefold(path) LIKE ? ESCAPE '\\' OR casefold(content) LIKE ? ESCAPE '\\' "
                "ORDER BY path COLLATE BINARY LIMIT ?", (pattern, pattern, limit),
            ).fetchall()
            results = []
            for path, content in rows:
                if not isinstance(path, str) or Path(path).is_absolute() or ".." in Path(path).parts or not isinstance(content, str):
                    raise ValueError("Search index contains invalid data; rebuild it")
                results.append({"path": path, "snippet": _snippet(content, query)})
            return results
        except sqlite3.Error:
            raise ValueError("Search index is invalid or unreadable; rebuild it") from None
        finally:
            if connection is not None:
                connection.close()
