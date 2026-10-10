#!/usr/bin/env python3
"""Heuristic publication scan. This is not proof that content is anonymous."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

IGNORED = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache', 'build', 'dist'}
TEXT_SUFFIXES = {'.md', '.py', '.toml', '.json', '.yml', '.yaml', '.html', '.css', '.js', '.txt', '.sh', '.svg'}
TEXT_NAMES = {'LICENSE', 'Makefile', '.gitignore', '.gitattributes'}
EMAIL = re.compile(r'\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b')
HOME_PATH = re.compile(r'/(?:home|Users)/[A-Za-z0-9_.-]+|[A-Z]:\\Users\\[^\s\\]+')
SECRET = re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9_-]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')
PRIVATE_NAMES = {'.private-vault', '.env', 'credentials.json', 'secrets.json', 'config.local.json'}


def reserved_domain(domain: str) -> bool:
    domain = domain.lower()
    return domain in {'example.com', 'example.org', 'example.net'} or domain.endswith(('.example', '.invalid', '.test', '.example.com', '.example.org', '.example.net'))


def scan(root: Path, denied: list[str] | None = None) -> tuple[list[Path], list[str]]:
    """Return inspected text paths and findings without printing matched secrets."""
    root = root.resolve()
    if not root.is_dir():
        raise ValueError('scan root must be an existing directory')
    findings: list[str] = []
    files: list[Path] = []
    terms = [term.casefold() for term in (denied or []) if term.strip()]
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if any(part in IGNORED or part.endswith('.egg-info') for part in relative.parts):
            continue
        if path.is_symlink():
            findings.append(f'{relative}: symlink is not permitted in a release')
            continue
        if not path.is_file():
            continue
        if path.name in PRIVATE_NAMES or path.name.startswith('.env.') or path.suffix.lower() in {'.pem', '.key', '.sqlite', '.sqlite3', '.db', '.eml'}:
            findings.append(f'{relative}: private or secret-bearing file type')
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in TEXT_NAMES:
            findings.append(f'{relative}: unreviewed binary or unsupported file type')
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            findings.append(f'{relative}: unreadable or non-UTF-8 content')
            continue
        files.append(path)
        if any(term in (str(relative) + '\n' + text).casefold() for term in terms):
            findings.append(f'{relative}: private denylist match')
        if HOME_PATH.search(text):
            findings.append(f'{relative}: absolute personal home path')
        if any(not reserved_domain(match.group(1)) for match in EMAIL.finditer(text)):
            findings.append(f'{relative}: non-example email address')
        if SECRET.search(text):
            findings.append(f'{relative}: credential-shaped content')
    return files, findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--deny-file', type=Path, help='private newline-separated terms; keep OUTSIDE the repository')
    args = parser.parse_args()
    if args.deny_file and args.deny_file.resolve().is_relative_to(args.root.resolve()):
        parser.error('denylist must be outside the release tree')
    denied = args.deny_file.read_text(encoding='utf-8').splitlines() if args.deny_file else []
    try:
        files, findings = scan(args.root, denied)
    except ValueError as exc:
        parser.error(str(exc))
    for finding in findings:
        print(f'FAIL {finding}')
    print(f'PRIVACY_SCAN files={len(files)} findings={len(findings)}; heuristic only, semantic and history review required')
    return 1 if findings else 0


if __name__ == '__main__':
    raise SystemExit(main())
