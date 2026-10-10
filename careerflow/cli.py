"""Command-line interface. Importing the CLI does not contact any network."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from . import __version__, storage, validation, workflow


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="careerflow", description="Private Markdown career workflow; no automatic submission, sending or scheduling.")
    result.add_argument("--version", action="version", version=f"careerflow {__version__}")
    commands = result.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Create an empty private vault or a clearly synthetic demonstration")
    init.add_argument("vault", type=Path)
    init.add_argument("--demo", action="store_true", help="Create fictional operations/community-services examples")
    for name, description in (
        ("validate", "Validate records and report actual counts"),
        ("dashboard", "Write a local HTML dashboard after validation"),
        ("digest", "Write local Markdown and HTML digests; nothing is sent"),
        ("scan", "Explicitly fetch configured public boards; import only unverified leads"),
        ("index", "Rebuild the disposable local search index"),
    ):
        command = commands.add_parser(name, help=description)
        command.add_argument("vault", type=Path)
    import_command = commands.add_parser("import-leads", help="Import a JSON list as unverified leads, never privileged states")
    import_command.add_argument("vault", type=Path)
    import_command.add_argument("input", type=Path)
    feedback = commands.add_parser("feedback", help="Append immutable local preference feedback; no employer-state changes")
    feedback.add_argument("vault", type=Path)
    feedback.add_argument("role_id")
    feedback.add_argument("action", choices=sorted(validation.FEEDBACK_ACTIONS))
    feedback.add_argument("--reason", default="", help="Required and non-empty for hide")
    feedback.add_argument("--event-id", help="Stable ID for safe retries; conflicting reuse is rejected")
    update = commands.add_parser("update-role", help="Patch allowed verification/fit fields; operator attestation is not automatic proof")
    update.add_argument("vault", type=Path)
    update.add_argument("role_id")
    update.add_argument("--patch", type=Path, required=True)
    prepare = commands.add_parser("prepare", help="Create no-overwrite working scaffolds for a current candidate")
    prepare.add_argument("vault", type=Path)
    prepare.add_argument("role_id")
    prepare.add_argument("--resume", action="store_true", help="Resume an existing complete scaffold without changing its files")
    submit = commands.add_parser("submit", help="Record a human report of external submission; NEVER submits or sends")
    submit.add_argument("vault", type=Path)
    submit.add_argument("role_id")
    submit.add_argument("--date", required=True, help="Reported external submission date, YYYY-MM-DD")
    submit.add_argument("--confirmation", required=True, help="Explicit human confirmation; receipt/outcome remains unknown")
    submit.add_argument("--human-confirmed", action="store_true", help="A human has explicitly reported this submission")
    search = commands.add_parser("search", help="Search the local derived index; no external search")
    search.add_argument("vault", type=Path)
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)
    return result


def _report_validation(report: validation.ValidationReport) -> None:
    print(" ".join(f"{name}={report.counts[name]}" for name in ("roles", "evidence", "feedback", "scans", "employers", "decisions")))
    for error in report.errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print("Valid vault." if report.valid else "Invalid vault.")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        command = args.command
        if command == "init":
            workflow.init_vault(args.vault, demo=args.demo)
            print("Created synthetic demonstration vault; no real claims or submissions." if args.demo else "Created empty private vault; complete the profile interview before assessing roles.")
        elif command == "validate":
            with storage.vault_lock(args.vault):
                report = validation.validate_vault(args.vault)
            _report_validation(report)
            return 0 if report.valid else 1
        elif command == "dashboard":
            workflow.dashboard(args.vault)
            print("Wrote output/dashboard.html (local only).")
        elif command == "digest":
            workflow.digest(args.vault)
            print("Wrote output/digest.md and output/digest.html (drafts only; nothing sent).")
        elif command == "import-leads":
            payload = storage.read_json(args.input)
            outcome = workflow.import_leads(args.vault, payload)
            print(f"Imported {outcome['imported']} unverified leads; skipped {outcome['skipped']} existing IDs without changes.")
        elif command == "feedback":
            record = workflow.add_feedback(args.vault, args.role_id, args.action, args.reason, event_id=args.event_id)
            print(f"Recorded feedback {record['id']} for {record['role_id']}; employer/submission state unchanged.")
        elif command == "update-role":
            workflow.update_role(args.vault, args.role_id, storage.read_json(args.patch))
            print(f"Updated {args.role_id}; preserved the Markdown body. Verification is an operator attestation, not automatic proof.")
        elif command == "prepare":
            workflow.prepare(args.vault, args.role_id, resume=args.resume)
            verb = "Resumed without overwriting" if args.resume else "Created"
            print(f"{verb} applications/{args.role_id}/ working scaffolds; role is preparing. Nothing submitted or sent.")
        elif command == "submit":
            workflow.submit(args.vault, args.role_id, args.date, args.confirmation, human_confirmed=args.human_confirmed)
            print(f"Recorded human-reported external submission for {args.role_id}; toolkit sent nothing. Employer receipt/outcome remains unknown.")
        elif command == "scan":
            record = workflow.scan(args.vault)
            print(f"Scan {record['status']}: sources={record['source_count']} successful={record['successful_sources']} failed={record['failed_sources']} fetched={record['fetched']} imported={record['imported']} skipped={record['skipped']}.")
            print(record["coverage_note"])
            if record["status"] == "failed":
                return 1
        elif command == "index":
            from .index import build_index
            with storage.vault_lock(args.vault):
                validation.require_valid_vault(args.vault)
                count = build_index(args.vault)
            print(f"Indexed {count} local documents in output/search.sqlite3; Markdown remains canonical.")
        elif command == "search":
            if args.limit < 1 or args.limit > 100:
                raise ValueError("Search limit must be between 1 and 100")
            from .index import search
            with storage.vault_lock(args.vault):
                validation.require_valid_vault(args.vault)
                matches = search(args.vault, args.query, limit=args.limit)
            for match in matches:
                print(f"{match['path']}: {match['snippet']}")
            if not matches:
                print("No local matches.")
        return 0
    except (OSError, ValueError, ImportError) as error:
        # Filesystem exceptions can disclose machine-specific absolute paths.
        message = "Filesystem operation failed; check the vault path and permissions." if isinstance(error, OSError) else str(error)
        if isinstance(error, ImportError):
            message = "A required toolkit integration module is unavailable; check the installation."
        print(f"Error: {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
