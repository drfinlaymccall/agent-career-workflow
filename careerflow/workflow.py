"""Explicit local operations over canonical Markdown records.

Network access exists only in scan(), through allowlisted connector adapters.
Neither feedback nor submission reporting contacts employers. Renderer, connector
and index integrations are imported lazily so the core remains independently
usable and testable.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import secrets
import shutil
import tempfile
from zoneinfo import ZoneInfo

from . import storage, templates, validation


class WorkflowError(ValueError):
    """The requested operation is not permitted in the current state."""


PATCH_FIELDS = {
    "title", "organisation", "status", "official_url", "source_type",
    "verification_status", "last_verified", "closing_date", "location", "work_mode",
    "eligibility", "match_reasons", "gaps", "evidence_ids", "fit_decision", "human_interest",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _event_id(prefix: str, now: datetime) -> str:
    return f"{prefix}-{now.strftime('%Y%m%dt%H%M%S%f')}-{secrets.token_hex(4)}"


def _error_if(errors: list[str]) -> None:
    if errors:
        raise validation.ValidationError("; ".join(errors))


def _by_id(records: list[dict]) -> dict[str, dict]:
    return {item["id"]: item for item in records}


def _read_role(root: Path, role_id: str) -> tuple[dict, str]:
    storage.require_id(role_id)
    path = storage.safe_path(root / "roles" / f"{role_id}.md")
    if not path.is_file():
        raise WorkflowError("Unknown role ID")
    record, body = storage.read_record(path)
    if record.get("id") != role_id:
        raise WorkflowError("Role ID does not exactly match its filename")
    return record, body


def _write_role(root: Path, record: dict, body: str) -> None:
    path = root / "roles" / f"{record['id']}.md"
    storage.write_record(path, record, body)
    actual, actual_body = storage.read_record(path)
    if actual != record or actual_body != body:
        raise storage.StorageError("Role write could not be verified")


def init_vault(vault: Path | str, *, demo: bool = False) -> Path:
    root = storage.safe_path(vault)
    toolkit = Path(__file__).resolve().parents[1]
    if root.is_relative_to(toolkit):
        raise WorkflowError("Keep private and demo vaults outside the toolkit directory")
    if root.exists() and not root.is_dir():
        raise WorkflowError("Vault path must be an empty directory or a new path")
    storage.secure_mkdir(root)
    with storage.vault_lock(root):
        if any(path.name != ".vault.lock" for path in root.iterdir()):
            raise WorkflowError("Refusing to overwrite a non-empty or already initialised vault")
        root.chmod(0o700)
        storage.atomic_write_text(root / ".private-vault", "Private local Markdown vault. Do not publish.\n", overwrite=False)
        config = {**templates.DEFAULT_CONFIG, "sources": [], "mode": "demo" if demo else "private"}
        storage.atomic_write_text(root / "config.json", json.dumps(config, indent=2) + "\n", overwrite=False)
        for folder in validation.FOLDERS:
            storage.secure_mkdir(root / folder)
        storage.atomic_write_text(root / ".gitignore", templates.GITIGNORE, overwrite=False)
        start = templates.START_HERE
        if demo:
            start = "# SYNTHETIC DEMO — no real career data or vacancies\n\nAll organisations, claims and application states below are fictional. Nothing has\nbeen submitted or sent. Synthetic labels must not be removed.\n\n" + start
        storage.atomic_write_text(root / "00-start-here.md", start, overwrite=False)
        profile = templates.DEMO_PROFILE_FILES if demo else templates.PROFILE_FILES
        for name, body in profile.items():
            storage.atomic_write_text(root / "profile" / name, body, overwrite=False)
        if demo:
            now = utc_now()
            evidence = templates.demo_evidence()
            roles = templates.demo_roles(now)
            feedback = templates.demo_feedback(now)
            for section, items in (("evidence", evidence), ("roles", roles), ("feedback", feedback)):
                for item in items:
                    storage.write_record(root / section / f"{item['id']}.md", item, "# SYNTHETIC DEMO\n\nWholly fictional source material. Never use as a real career claim.\n", overwrite=False)
            for role in roles:
                if role["status"] == "preparing":
                    path = storage.secure_mkdir(root / "applications" / role["id"])
                    linked = [item for item in evidence if item["id"] in role["evidence_ids"]]
                    for name, body in templates.application_files(role, linked).items():
                        storage.atomic_write_text(path / name, body, overwrite=False)
        validation.require_valid_vault(root)
    return root


def normalise_lead(payload: dict, *, config: dict) -> dict:
    """Discard imported authority/submission claims, retaining only lead facts."""
    if not isinstance(payload, dict):
        raise WorkflowError("Each imported lead must be a JSON object")
    identifier = storage.require_id(payload.get("id"))
    for key in ("title", "organisation"):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise WorkflowError(f"Imported lead requires a non-empty {key}")
    synthetic_value = payload.get("synthetic", False)
    if type(synthetic_value) is not bool:
        raise WorkflowError("Imported synthetic flag must be a boolean")
    synthetic_hint = synthetic_value or payload.get("source_type") == "synthetic" or payload.get("verification_status") == "synthetic"
    if synthetic_hint and config.get("mode") != "demo":
        raise WorkflowError("Synthetic data must not be imported into a private vault")
    if synthetic_hint and not synthetic_value:
        raise WorkflowError("Synthetic data must be explicitly labelled synthetic=true")
    source_type = "synthetic" if synthetic_value else payload.get("source_type", "aggregator")
    official_url = payload.get("official_url")
    if official_url is not None and not validation.safe_public_url(official_url):
        raise WorkflowError("Imported official_url must be a safe public HTTPS URL or null")
    record = {
        "schema_version": 1, "kind": "role", "id": identifier,
        "title": payload["title"], "organisation": payload["organisation"],
        "status": "lead", "official_url": official_url, "source_type": source_type,
        "verification_status": "unverified", "last_verified": None,
        "closing_date": payload.get("closing_date"),
        "location": payload.get("location", "unknown"), "work_mode": payload.get("work_mode", "unknown"),
        "eligibility": payload.get("eligibility", "unknown"),
        "match_reasons": [], "gaps": ["Official verification and suitability assessment required"],
        "evidence_ids": [], "fit_decision": "pending", "human_interest": False,
        "submitted_at": None, "submission_note": "", "outcome_note": "",
        "synthetic": synthetic_value,
    }
    _error_if(validation.validate_role(record, config=config, evidence={}))
    return record


def import_leads(vault: Path | str, payload: list[dict]) -> dict:
    root = storage.safe_path(vault)
    with storage.vault_lock(root):
        report = validation.require_valid_vault(root)
        if not isinstance(payload, list):
            raise WorkflowError("Lead input must be a JSON list")
        proposed = [normalise_lead(item, config=report.config) for item in payload]
        ids = [item["id"] for item in proposed]
        if len(ids) != len(set(ids)):
            raise WorkflowError("Duplicate lead IDs within an import batch")
        existing = _by_id(report.records["roles"])
        other_ids = {item["id"] for section, items in report.records.items() if section != "roles" for item in items}
        if any(identifier in other_ids for identifier in ids):
            raise WorkflowError("Imported ID conflicts with another record kind")
        pending = [item for item in proposed if item["id"] not in existing]
        created: list[Path] = []
        try:
            for item in pending:
                path = root / "roles" / f"{item['id']}.md"
                body = "# Unverified imported lead\n\nImported facts are not verified suitability or availability. Check the official\nsource and record bounded evidence before considering this role a candidate.\n"
                if item["synthetic"]:
                    body = "# SYNTHETIC DEMO\n\n" + body
                storage.write_record(path, item, body, overwrite=False)
                created.append(path)
                if storage.read_record(path) != (item, body):
                    raise storage.StorageError("Imported record readback failed")
        except Exception:
            for path in created:
                path.unlink(missing_ok=True)
            raise
        return {"imported": len(pending), "skipped": len(proposed) - len(pending), "ids": [item["id"] for item in pending]}


def update_role(vault: Path | str, role_id: str, patch: dict) -> dict:
    storage.require_id(role_id)
    if not isinstance(patch, dict) or not patch:
        raise WorkflowError("Patch must be a non-empty JSON object")
    forbidden = set(patch) - PATCH_FIELDS
    if forbidden:
        raise WorkflowError("Forbidden patch fields: " + ", ".join(sorted(str(key) for key in forbidden)))
    root = storage.safe_path(vault)
    with storage.vault_lock(root):
        report = validation.require_valid_vault(root)
        current, body = _read_role(root, role_id)
        proposed = {**current, **patch}
        new_state = proposed.get("status")
        if new_state != current["status"]:
            if new_state in ("preparing", "submitted", "outcome_known"):
                raise WorkflowError("Use the explicit preparation/submission workflow; outcome notes require evidenced manual review")
            if current["status"] in ("submitted", "outcome_known"):
                raise WorkflowError("Update-role cannot regress or alter historical submission/outcome state")
        _error_if(validation.validate_role(proposed, config=report.config, evidence=_by_id(report.records["evidence"])))
        _write_role(root, proposed, body)
        return proposed


def add_feedback(vault: Path | str, role_id: str, action: str, reason: str = "", *, event_id: str | None = None) -> dict:
    storage.require_id(role_id)
    if not isinstance(action, str) or action not in validation.FEEDBACK_ACTIONS:
        raise WorkflowError("Feedback action must be strong_fit, hide, restore or note")
    if not isinstance(reason, str) or (action == "hide" and not reason.strip()):
        raise WorkflowError("Hide feedback requires a non-empty reason")
    now = utc_now()
    identifier = storage.require_id(event_id if event_id is not None else _event_id("feedback", now))
    root = storage.safe_path(vault)
    with storage.vault_lock(root):
        report = validation.require_valid_vault(root)
        _read_role(root, role_id)
        path = storage.safe_path(root / "feedback" / f"{identifier}.md")
        if path.exists():
            existing, _ = storage.read_record(path)
            if all(existing.get(key) == value for key, value in {"id": identifier, "role_id": role_id, "action": action, "reason": reason}.items()):
                return existing
            raise WorkflowError("Feedback event ID conflicts with an immutable existing event")
        if any(item["id"] == identifier for items in report.records.values() for item in items):
            raise WorkflowError("Feedback event ID conflicts with another record")
        record = {
            "schema_version": 1, "kind": "feedback", "id": identifier,
            "role_id": role_id, "action": action, "reason": reason,
            "recorded_at": now.isoformat(),
        }
        _error_if(validation.validate_feedback(record, roles=_by_id(report.records["roles"])))
        body = "# Local human preference feedback\n\nThis immutable event does not change employer, submission or outcome state.\n"
        storage.write_record(path, record, body, overwrite=False)
        loaded, loaded_body = storage.read_record(path)
        if loaded != record or loaded_body != body:
            raise storage.StorageError("Feedback readback failed")
        return record


def _check_fresh_for_preparation(role: dict, config: dict, now: datetime) -> None:
    checked = validation.parse_timestamp(role["last_verified"])
    if checked is None or checked > now + timedelta(minutes=5):
        raise WorkflowError("Verification timestamp is missing or in the future")
    if now - checked > timedelta(days=config["max_verification_age_days"]):
        raise WorkflowError("Verification is stale; recheck before preparation")
    deadline = validation.parse_date(role["closing_date"], nullable=True)
    today = now.astimezone(ZoneInfo(config["timezone"])).date()
    if deadline is not None and deadline < today:
        raise WorkflowError("Closing date has passed; recheck before preparation")


def prepare(vault: Path | str, role_id: str, *, resume: bool = False) -> Path:
    storage.require_id(role_id)
    root = storage.safe_path(vault)
    with storage.vault_lock(root):
        report = validation.require_valid_vault(root)
        role, body = _read_role(root, role_id)
        if role["status"] != "current_candidate":
            raise WorkflowError("Preparation requires an existing current_candidate state")
        _check_fresh_for_preparation(role, report.config, utc_now())
        destination = storage.safe_path(root / "applications" / role_id)
        if destination.exists():
            if not resume:
                raise WorkflowError("Refusing to overwrite an existing application folder; use --resume to retain an existing scaffold")
            if not destination.is_dir():
                raise WorkflowError("Existing application path is not a directory")
            for name in templates.application_files(role, []).keys():
                if not storage.safe_path(destination / name).is_file():
                    raise WorkflowError("Existing application scaffold is incomplete; review it manually before resuming")
            proposed = {**role, "status": "preparing"}
            _error_if(validation.validate_role(proposed, config=report.config, evidence=_by_id(report.records["evidence"])))
            _write_role(root, proposed, body)
            return destination
        if resume:
            raise WorkflowError("No existing application scaffold to resume")
        proposed = {**role, "status": "preparing"}
        evidence = _by_id(report.records["evidence"])
        _error_if(validation.validate_role(proposed, config=report.config, evidence=evidence))
        staged = Path(tempfile.mkdtemp(prefix=".prepare-", dir=root / "applications"))
        published = False
        try:
            linked = [evidence[identifier] for identifier in role["evidence_ids"]]
            for name, content in templates.application_files(role, linked).items():
                storage.atomic_write_text(staged / name, content, overwrite=False)
            storage.safe_path(destination)
            if destination.exists():
                raise WorkflowError("Application folder appeared during preparation")
            os.rename(staged, destination)
            published = True
            _write_role(root, proposed, body)
        except Exception:
            # Remove only this operation's new scaffold, never an existing folder.
            if published:
                shutil.rmtree(destination)
            raise
        finally:
            if staged.exists():
                shutil.rmtree(staged)
        return destination


def submit(vault: Path | str, role_id: str, date: str, confirmation: str, *, human_confirmed: bool = False) -> dict:
    storage.require_id(role_id)
    if human_confirmed is not True or not isinstance(confirmation, str) or not confirmation.strip():
        raise WorkflowError("Submission reporting requires --human-confirmed and an explicit non-empty confirmation")
    submitted_date = validation.parse_date(date)
    root = storage.safe_path(vault)
    with storage.vault_lock(root):
        report = validation.require_valid_vault(root)
        today = utc_now().astimezone(ZoneInfo(report.config["timezone"])).date()
        if submitted_date is None or submitted_date > today:
            raise WorkflowError("Submission report date cannot be in the future")
        role, body = _read_role(root, role_id)
        if role["status"] != "preparing":
            raise WorkflowError("Submission reporting requires an existing preparing state")
        proposed = {**role, "status": "submitted", "submitted_at": date, "submission_note": confirmation}
        _error_if(validation.validate_role(proposed, config=report.config, evidence=_by_id(report.records["evidence"])))
        _write_role(root, proposed, body)
        return proposed


def scan(vault: Path | str, *, fetcher=None) -> dict:
    """Record complete/partial/failed coverage; never infer closure from absence.

    fetcher is an injection point for offline tests. Default imports the real
    connector only when this explicit network command is used.
    """
    root = storage.safe_path(vault)
    with storage.vault_lock(root):
        report = validation.require_valid_vault(root)
        sources = report.config["sources"]
        if fetcher is None and sources:
            from .connectors import fetch_source
            fetcher = fetch_source
        started = utc_now()
        results = []
        imported = skipped = fetched = 0
        for source in sources:
            # Pass recognised fields only. Unknown config cannot change endpoints
            # or invoke commands, executable adapters, credentials or redirects.
            approved_source = {key: source[key] for key in ("adapter", "board", "organisation")}
            result = {**approved_source, "status": "failed", "fetched": 0, "imported": 0, "skipped": 0, "error": None}
            try:
                leads = fetcher(approved_source, timeout=20.0)
                if not isinstance(leads, list):
                    raise WorkflowError("Connector did not return a list")
                result["fetched"] = len(leads)
                fetched += len(leads)
                outcome = import_leads(root, leads)
                result.update(status="success", imported=outcome["imported"], skipped=outcome["skipped"])
                imported += outcome["imported"]
                skipped += outcome["skipped"]
            except Exception:
                # Exception strings can contain response bodies, URLs or secrets.
                # Keep canonical logs concise and safe rather than serialising them.
                result["error"] = "Source fetch or record validation failed; check the approved public board configuration and retry."
            results.append(result)
        success_count = sum(item["status"] == "success" for item in results)
        failure_count = len(results) - success_count
        status = "failed" if success_count == 0 else "partial" if failure_count else "success"
        completed = utc_now()
        record = {
            "schema_version": 1, "kind": "scan", "id": _event_id("scan", completed),
            "started_at": started.isoformat(), "completed_at": completed.isoformat(),
            "status": status, "source_count": len(sources), "successful_sources": success_count,
            "failed_sources": failure_count, "fetched": fetched, "imported": imported,
            "skipped": skipped, "sources": results,
            "coverage_note": "Only configured, approved public boards were checked. This is not a labour-market census; missing roles are not assumed closed." if sources else "No sources configured; no network calls or vacancy checks were made.",
        }
        path = root / "scans" / f"{record['id']}.md"
        body = "# Explicit source scan\n\n" + record["coverage_note"] + "\n"
        storage.write_record(path, record, body, overwrite=False)
        if storage.read_record(path) != (record, body):
            raise storage.StorageError("Scan record readback failed")
        return record


def latest_scan(report: validation.ValidationReport) -> dict | None:
    def key(item: dict):
        value = item.get("completed_at", item.get("recorded_at"))
        try:
            parsed = validation.parse_timestamp(value)
        except ValueError:
            parsed = None
        return (parsed.timestamp() if parsed else float("-inf"), item["id"])
    return max(report.records["scans"], key=key, default=None)


def dashboard(vault: Path | str) -> Path:
    from .render import render_dashboard
    root = storage.safe_path(vault)
    with storage.vault_lock(root):
        report = validation.require_valid_vault(root)
        html = render_dashboard(report.records["roles"], report.records["feedback"], config=report.config, scan=latest_scan(report), now=utc_now())
        path = root / "output" / "dashboard.html"
        storage.atomic_write_text(path, html)
        return path


def digest(vault: Path | str) -> tuple[Path, Path]:
    from .render import render_digest
    root = storage.safe_path(vault)
    with storage.vault_lock(root):
        report = validation.require_valid_vault(root)
        markdown, html = render_digest(report.records["roles"], report.records["feedback"], config=report.config, scan=latest_scan(report), now=utc_now())
        paths = root / "output" / "digest.md", root / "output" / "digest.html"
        storage.atomic_write_text(paths[0], markdown)
        storage.atomic_write_text(paths[1], html)
        return paths
