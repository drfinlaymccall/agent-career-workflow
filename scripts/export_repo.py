#!/usr/bin/env python3
"""Build a deterministic toolkit-only archive, never a private-vault backup."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path

if __package__:
    from .privacy_check import scan
else:
    from privacy_check import scan

ROOT_FILES = {'README.md', 'AGENTS.md', 'LICENSE', 'SECURITY.md', 'CONTRIBUTING.md', 'pyproject.toml', '.gitignore'}
DIRECTORIES = {'careerflow', 'docs', 'prompts', 'tests', 'scripts', 'examples'}


def export(root: Path, destination: Path, denied: list[str] | None = None) -> dict:
    root = root.resolve()
    destination = destination.resolve()
    if destination.is_relative_to(root):
        raise ValueError('write release archives outside the toolkit directory')
    if destination.exists():
        raise ValueError('destination already exists; choose a new release filename')
    inspected, findings = scan(root, denied)
    if findings:
        raise ValueError('privacy scan failed; run privacy_check.py for finding locations')
    selected = []
    for path in inspected:
        rel = path.relative_to(root)
        if (len(rel.parts) == 1 and rel.name in ROOT_FILES) or rel.parts[0] in DIRECTORIES or str(rel) == '.github/workflows/check.yml':
            selected.append(path)
    required = {'README.md', 'LICENSE', 'pyproject.toml', 'careerflow/__main__.py'}
    if not required.issubset({str(p.relative_to(root)) for p in selected}):
        raise ValueError('required toolkit files missing')
    contents = {str(path.relative_to(root)): path.read_bytes() for path in selected}
    manifest = {name: hashlib.sha256(body).hexdigest() for name, body in sorted(contents.items())}
    contents['RELEASE-MANIFEST.json'] = (json.dumps({'schema_version': 1, 'sha256': manifest}, indent=2) + '\n').encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.careerflow-release-', suffix='.zip', dir=destination.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, body in sorted(contents.items()):
                info = zipfile.ZipInfo('agent-career-workflow/' + name, (2024, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, body)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError('archive integrity check failed')
            for name, body in contents.items():
                if archive.read('agent-career-workflow/' + name) != body:
                    raise ValueError('archive readback differs from source bytes')
        checksum = hashlib.sha256(temporary.read_bytes()).hexdigest()
        # Publish without replacement. A concurrent writer retains its output.
        os.link(temporary, destination)
    finally:
        # Remove only the temporary file owned by this invocation.
        temporary.unlink(missing_ok=True)
    return {'files': len(manifest), 'archive_members': len(contents), 'sha256': checksum}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--deny-file', type=Path)
    args = parser.parse_args()
    if args.deny_file and args.deny_file.resolve().is_relative_to(args.root.resolve()):
        parser.error('denylist must stay outside the release tree')
    denied = args.deny_file.read_text(encoding='utf-8').splitlines() if args.deny_file else []
    try:
        result = export(args.root, args.destination, denied)
    except (ValueError, OSError) as exc:
        parser.exit(1, f'Export failed: {exc}\n')
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
