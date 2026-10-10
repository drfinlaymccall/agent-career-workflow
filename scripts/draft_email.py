#!/usr/bin/env python3
"""Create an UNSENT plain-text digest email. No credentials or network access."""
from __future__ import annotations

import argparse
import os
import re
from email import policy
from email.message import EmailMessage
from pathlib import Path


def make_draft(digest: str, sender: str, recipient: str, subject: str) -> bytes:
    for address in (sender, recipient):
        if not re.fullmatch(r'[^\s<>@,;]+@[^\s<>@,;]+\.[^\s<>@,;]+', address):
            raise ValueError('use one plain email address for sender and recipient')
    if not subject.strip() or '\r' in subject or '\n' in subject:
        raise ValueError('subject must be a non-empty single line')
    if not digest.strip():
        raise ValueError('digest is empty')
    message = EmailMessage(policy=policy.SMTP)
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = subject
    message['X-Unsent'] = '1'
    message.set_content(digest)
    return message.as_bytes()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('digest', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--sender', required=True)
    parser.add_argument('--recipient', required=True)
    parser.add_argument('--subject', required=True)
    args = parser.parse_args()
    toolkit = Path(__file__).resolve().parents[1]
    if args.output.resolve().is_relative_to(toolkit):
        parser.error('email drafts must stay outside the public toolkit')
    try:
        data = make_draft(args.digest.read_text(encoding='utf-8'), args.sender, args.recipient, args.subject)
        # Exclusive creation prevents silently replacing a reviewed draft.
        fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'Draft failed: {exc}\n')
    print('UNSENT email draft created; nothing was delivered')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
