"""Schema and lifecycle gates; validation never upgrades a role's status.

A verified flag is an operator attestation, not independent proof that a vacancy
is open or that an ATS board belongs to its stated employer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
import ipaddress
from pathlib import Path
import re
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import storage


class ValidationError(ValueError):
    """The proposed state is not valid and must not be written."""


ROLE_STATES = {
    "lead", "verified", "current_candidate", "preparing", "submitted",
    "outcome_known", "withheld_unverified", "market_intelligence", "declined",
    "closed", "expired",
}
SOURCE_TYPES = {"official_ats", "employer", "aggregator", "synthetic"}
VERIFICATION_STATES = {"unverified", "verified", "stale", "closed", "synthetic"}
EVIDENCE_STATES = {"unconfirmed", "human_confirmed", "document_verified", "synthetic"}
FEEDBACK_ACTIONS = {"strong_fit", "hide", "restore", "note"}
SUPPORTED_EVIDENCE = {"human_confirmed", "document_verified"}
ROLE_REQUIRED = {
    "schema_version", "kind", "id", "title", "organisation", "status", "official_url",
    "source_type", "verification_status", "last_verified", "closing_date", "location",
    "work_mode", "eligibility", "match_reasons", "gaps", "evidence_ids", "fit_decision",
    "human_interest", "submitted_at", "submission_note", "outcome_note", "synthetic",
}
FOLDERS = ("profile", "evidence", "roles", "employers", "applications", "feedback", "scans", "decisions", "output")
BOARD_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}\Z", re.ASCII)
DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z", re.ASCII)
TIMESTAMP_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})\Z", re.ASCII)
UNKNOWN_VALUES = {"", "unknown", "unconfirmed", "not known", "not specified", "unspecified", "tbc", "tbd", "to be confirmed", "pending", "n/a", "none", "null"}


def parse_date(value: object, *, nullable: bool = False) -> date | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or DATE_PATTERN.fullmatch(value) is None:
        raise ValidationError("Expected a date in YYYY-MM-DD format, without an invented time")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValidationError("Invalid calendar date") from error


def parse_timestamp(value: object, *, nullable: bool = False) -> datetime | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise ValidationError("Expected an aware ISO timestamp with a timezone")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValidationError("Invalid ISO timestamp") from error
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValidationError("Timestamp must include a timezone")
    return result


def safe_public_url(value: object) -> bool:
    """No network resolution: reject dangerous schemes, credentials and local hosts."""
    if not isinstance(value, str) or not value or len(value) > 4096:
        return False
    if any(ord(char) < 33 or ord(char) == 127 for char in value) or "\\" in value:
        return False
    try:
        parts = urlsplit(value)
        if parts.scheme != "https" or parts.username is not None or parts.password is not None:
            return False
        host = parts.hostname
        if not host or parts.port not in (None, 443):
            return False
        host = host.lower().rstrip(".")
        if host == "localhost" or host.endswith((".localhost", ".local", ".internal", ".test", ".invalid")):
            return False
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            if "." not in host or not re.fullmatch(r"[a-z0-9.-]+", host, flags=re.ASCII):
                return False
            labels = host.split(".")
            if any(not label or len(label) > 63 or label.startswith("-") or label.endswith("-") for label in labels):
                return False
            # Obscure numeric host forms must not bypass local-address checks.
            if all(label.isdigit() or label.lower().startswith("0x") for label in labels):
                return False
        else:
            if not address.is_global:
                return False
        return True
    except (ValueError, UnicodeError):
        return False


def _member(value: object, choices: set[str]) -> bool:
    return isinstance(value, str) and value in choices


def _text(value: object, *, nonempty: bool = False) -> bool:
    return isinstance(value, str) and (not nonempty or bool(value.strip()))


def _strings(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _base(record: dict, kind: str) -> list[str]:
    errors = []
    if type(record.get("schema_version")) is not int or record.get("schema_version") != 1:
        errors.append("schema_version must be integer 1")
    if record.get("kind") != kind:
        errors.append(f"kind must be {kind}")
    try:
        storage.require_id(record.get("id"))
    except ValueError as error:
        errors.append(str(error))
    return errors


def config_errors(config: dict) -> list[str]:
    errors = []
    if type(config.get("schema_version")) is not int or config.get("schema_version") != 1:
        errors.append("config.schema_version must be integer 1")
    if not _member(config.get("mode"), {"private", "demo"}):
        errors.append("config.mode must be private or demo")
    try:
        if not isinstance(config.get("timezone"), str):
            raise ValueError("missing timezone")
        ZoneInfo(config["timezone"])
    except (ValueError, ZoneInfoNotFoundError):
        errors.append("config.timezone must be a recognised timezone")
    age = config.get("max_verification_age_days")
    if type(age) is not int or age < 1:
        errors.append("config.max_verification_age_days must be a positive integer")
    sources = config.get("sources")
    if not isinstance(sources, list):
        errors.append("config.sources must be a list")
        return errors
    seen = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"config.sources[{index}] must be an object")
            continue
        adapter, board = source.get("adapter"), source.get("board")
        if not _member(adapter, {"greenhouse", "lever"}):
            errors.append(f"config.sources[{index}] has an unsupported adapter")
        if not isinstance(board, str) or BOARD_PATTERN.fullmatch(board) is None:
            errors.append(f"config.sources[{index}] has an unsafe board slug")
        if not _text(source.get("organisation"), nonempty=True):
            errors.append(f"config.sources[{index}] requires an organisation")
        if isinstance(adapter, str) and isinstance(board, str):
            pair = adapter, board
            if pair in seen:
                errors.append("config.sources contains a duplicate adapter/board")
            seen.add(pair)
    return errors


def validate_evidence(record: dict, *, config: dict) -> list[str]:
    errors = _base(record, "evidence")
    for key in ("claim", "source", "boundary"):
        if not _text(record.get(key), nonempty=True):
            errors.append(f"evidence.{key} must be a non-empty string")
    if not _member(record.get("status"), EVIDENCE_STATES):
        errors.append("evidence.status is invalid")
    synthetic = record.get("synthetic")
    if type(synthetic) is not bool:
        errors.append("evidence.synthetic must be a boolean")
    if synthetic is True and config.get("mode") != "demo":
        errors.append("Synthetic evidence is forbidden in a private vault")
    if (synthetic is True) != (record.get("status") == "synthetic"):
        errors.append("Synthetic evidence must remain labelled synthetic")
    return errors


def validate_role(record: dict, *, config: dict, evidence: dict[str, dict]) -> list[str]:
    errors = _base(record, "role")
    missing = ROLE_REQUIRED - record.keys()
    if missing:
        errors.append("Missing role fields: " + ", ".join(sorted(missing)))
    for key in ("title", "organisation", "location", "work_mode", "eligibility"):
        if not _text(record.get(key), nonempty=True):
            errors.append(f"role.{key} must be a non-empty string")
    for key in ("submission_note", "outcome_note"):
        if not _text(record.get(key)):
            errors.append(f"role.{key} must be a string")
    for key in ("match_reasons", "gaps", "evidence_ids"):
        if not _strings(record.get(key)):
            errors.append(f"role.{key} must be a list of strings")
    if not _member(record.get("status"), ROLE_STATES):
        errors.append("role.status is invalid")
    if not _member(record.get("source_type"), SOURCE_TYPES):
        errors.append("role.source_type is invalid")
    if not _member(record.get("verification_status"), VERIFICATION_STATES):
        errors.append("role.verification_status is invalid")
    if not _member(record.get("fit_decision"), {"pending", "approved"}):
        errors.append("role.fit_decision must be pending or approved")
    for key in ("human_interest", "synthetic"):
        if type(record.get(key)) is not bool:
            errors.append(f"role.{key} must be a boolean")
    url = record.get("official_url")
    if url is not None and not safe_public_url(url):
        errors.append("role.official_url must be a safe public HTTPS URL or null")
    for key in ("closing_date", "submitted_at"):
        try:
            parse_date(record.get(key), nullable=True)
        except ValueError as error:
            errors.append(f"role.{key}: {error}")
    try:
        verified_at = parse_timestamp(record.get("last_verified"), nullable=True)
    except ValueError as error:
        verified_at = None
        errors.append(f"role.last_verified: {error}")
    synthetic = record.get("synthetic") is True
    if synthetic:
        if config.get("mode") != "demo":
            errors.append("Synthetic roles are forbidden in a private vault")
        if record.get("source_type") != "synthetic" or record.get("verification_status") == "verified":
            errors.append("Synthetic roles must never be labelled official or verified")
    elif record.get("source_type") == "synthetic" or record.get("verification_status") == "synthetic":
        errors.append("Synthetic labels require synthetic=true")
    evidence_ids = record.get("evidence_ids", [])
    if not _strings(evidence_ids):
        evidence_ids = []
    if len(set(evidence_ids)) != len(evidence_ids):
        errors.append("role.evidence_ids contains duplicates")
    for identifier in evidence_ids:
        try:
            storage.require_id(identifier)
        except ValueError:
            errors.append("role.evidence_ids contains an invalid ID")
        if identifier not in evidence:
            errors.append(f"Unknown evidence reference: {identifier}")
        elif not synthetic and evidence[identifier].get("synthetic") is True:
            errors.append("Real roles cannot rely on synthetic evidence")
    state = record.get("status")
    gated = state in ("verified", "current_candidate", "preparing")
    demo_exemption = synthetic and config.get("mode") == "demo" and record.get("verification_status") == "synthetic"
    if gated:
        if not demo_exemption:
            if record.get("verification_status") != "verified" or record.get("source_type") not in ("official_ats", "employer") or not safe_public_url(url):
                errors.append("Verified/candidate/preparing roles require an official source and verification attestation")
        if verified_at is None:
            errors.append("Verified/candidate/preparing roles require last_verified")
    if state in ("current_candidate", "preparing"):
        for key in ("location", "eligibility"):
            if not isinstance(record.get(key), str) or record[key].strip().lower() in UNKNOWN_VALUES:
                errors.append(f"Candidate/preparing requires known {key}")
        if record.get("fit_decision") != "approved":
            errors.append("Candidate/preparing requires approved fit")
        if not evidence_ids:
            errors.append("Candidate/preparing requires supported evidence IDs")
        for identifier in evidence_ids:
            item = evidence.get(identifier, {})
            supported = _member(item.get("status"), SUPPORTED_EVIDENCE)
            if demo_exemption and item.get("synthetic") is True and item.get("status") == "synthetic":
                supported = True
            if not supported:
                errors.append(f"Evidence is not confirmed support: {identifier}")
    if state in ("submitted", "outcome_known"):
        if record.get("submitted_at") is None or not _text(record.get("submission_note"), nonempty=True):
            errors.append("Submitted/outcome_known requires historical submission date and explicit human confirmation note")
    if state == "outcome_known" and not _text(record.get("outcome_note"), nonempty=True):
        errors.append("Outcome_known requires an outcome note")
    return errors


def validate_feedback(record: dict, *, roles: dict[str, dict]) -> list[str]:
    errors = _base(record, "feedback")
    role_id = record.get("role_id")
    try:
        storage.require_id(role_id)
    except ValueError:
        errors.append("feedback.role_id is invalid")
    if not isinstance(role_id, str) or role_id not in roles:
        errors.append("Feedback refers to an unknown role ID")
    if not _member(record.get("action"), FEEDBACK_ACTIONS):
        errors.append("feedback.action is invalid")
    if not _text(record.get("reason"), nonempty=record.get("action") == "hide"):
        errors.append("feedback.reason must be a string; hide requires a reason")
    try:
        parse_timestamp(record.get("recorded_at"))
    except ValueError as error:
        errors.append(f"feedback.recorded_at: {error}")
    return errors


def validate_scan(record: dict) -> list[str]:
    errors = _base(record, "scan")
    timestamps = []
    for key in ("started_at", "completed_at"):
        try:
            timestamps.append(parse_timestamp(record.get(key)))
        except ValueError as error:
            errors.append(f"scan.{key}: {error}")
    if len(timestamps) == 2 and timestamps[0] > timestamps[1]:
        errors.append("Scan completion precedes its start")
    if not _member(record.get("status"), {"success", "partial", "failed"}):
        errors.append("scan.status is invalid")
    if not _text(record.get("coverage_note"), nonempty=True):
        errors.append("scan.coverage_note must explain coverage limitations")
    counts = ("source_count", "successful_sources", "failed_sources", "fetched", "imported", "skipped")
    for key in counts:
        if type(record.get(key)) is not int or record[key] < 0:
            errors.append(f"scan.{key} must be a non-negative integer")
    sources = record.get("sources")
    if not isinstance(sources, list):
        errors.append("scan.sources must contain per-source results")
        return errors
    if record.get("source_count") != len(sources):
        errors.append("scan.source_count disagrees with the recorded source results")
    totals = {"fetched": 0, "imported": 0, "skipped": 0}
    successful = 0
    for source in sources:
        if not isinstance(source, dict):
            errors.append("Each scan source result must be an object")
            continue
        if not _member(source.get("adapter"), {"greenhouse", "lever"}):
            errors.append("Scan source adapter is invalid")
        if not isinstance(source.get("board"), str) or BOARD_PATTERN.fullmatch(source["board"]) is None:
            errors.append("Scan source board is invalid")
        if not _text(source.get("organisation"), nonempty=True):
            errors.append("Scan source organisation is required")
        if not _member(source.get("status"), {"success", "failed"}):
            errors.append("Scan source status is invalid")
        successful += source.get("status") == "success"
        if source.get("status") == "failed" and not _text(source.get("error"), nonempty=True):
            errors.append("Failed scan source requires an error description")
        if source.get("error") is not None and not isinstance(source["error"], str):
            errors.append("Scan source error must be a string or null")
        for key in totals:
            if type(source.get(key)) is not int or source[key] < 0:
                errors.append(f"Scan source {key} must be a non-negative integer")
            else:
                totals[key] += source[key]
    for key, total in totals.items():
        if record.get(key) != total:
            errors.append(f"scan.{key} disagrees with per-source counts")
    if record.get("successful_sources") != successful or record.get("failed_sources") != len(sources) - successful:
        errors.append("Scan success/failure counts disagree with source results")
    expected = "failed" if successful == 0 else "success" if successful == len(sources) else "partial"
    if record.get("status") != expected:
        errors.append("Scan status disagrees with source results")
    return errors


@dataclass
class ValidationReport:
    counts: dict[str, int] = field(default_factory=lambda: {section: 0 for section in storage.SECTIONS})
    errors: list[str] = field(default_factory=list)
    config: dict = field(default_factory=dict)
    records: dict[str, list[dict]] = field(default_factory=lambda: {section: [] for section in storage.SECTIONS})

    @property
    def valid(self) -> bool:
        return not self.errors


def validate_vault(vault: Path | str) -> ValidationReport:
    report = ValidationReport()
    try:
        root = storage.safe_path(vault)
    except (OSError, ValueError) as error:
        report.errors.append(f"Vault path: {error}")
        return report
    try:
        report.config = storage.load_config(root)
    except (OSError, ValueError) as error:
        report.errors.append(f"Vault configuration: {error}")
    else:
        report.errors.extend(config_errors(report.config))
    for folder in FOLDERS:
        try:
            if not storage.safe_path(root / folder).is_dir():
                report.errors.append(f"Missing vault folder: {folder}")
        except ValueError as error:
            report.errors.append(f"{folder}: {error}")
    identities: set[str] = set()
    for section in storage.SECTIONS:
        try:
            directory = storage.safe_path(root / section)
            entries = sorted(directory.iterdir()) if directory.is_dir() else []
        except (OSError, ValueError) as error:
            report.errors.append(f"{section}: {error}")
            continue
        # Count canonical filenames even when one entry is malformed/unsafe;
        # an invalid config or symlink must not make existing counts become zero.
        paths = [path for path in entries if path.suffix == ".md"]
        report.counts[section] = len(paths)
        for path in entries:
            if path.suffix != ".md":
                try:
                    storage.safe_path(path)
                except (OSError, ValueError) as error:
                    report.errors.append(f"{section}/{path.name}: {error}")
        for path in paths:
            label = f"{section}/{path.name}"
            try:
                metadata, _ = storage.read_record(path)
            except (OSError, ValueError) as error:
                report.errors.append(f"{label}: {error}")
                continue
            report.records[section].append(metadata)
            identifier = metadata.get("id")
            if isinstance(identifier, str):
                if path.stem != identifier:
                    report.errors.append(f"{label}: filename must exactly match the record ID")
                if identifier in identities:
                    report.errors.append(f"{label}: duplicate record ID")
                identities.add(identifier)
    evidence = {item["id"]: item for item in report.records["evidence"] if isinstance(item.get("id"), str)}
    roles = {item["id"]: item for item in report.records["roles"] if isinstance(item.get("id"), str)}
    for section, items in report.records.items():
        for item in items:
            if section == "roles":
                errors = validate_role(item, config=report.config, evidence=evidence)
            elif section == "evidence":
                errors = validate_evidence(item, config=report.config)
            elif section == "feedback":
                errors = validate_feedback(item, roles=roles)
            elif section == "scans":
                errors = validate_scan(item)
            else:
                errors = _base(item, {"employers": "employer", "decisions": "decision"}[section])
            label = str(item.get("id", "record without ID"))
            report.errors.extend(f"{section}/{label}: {error}" for error in errors)
    return report


def require_valid_vault(vault: Path | str) -> ValidationReport:
    report = validate_vault(vault)
    if report.errors:
        raise ValidationError("Vault validation failed: " + "; ".join(report.errors))
    return report
