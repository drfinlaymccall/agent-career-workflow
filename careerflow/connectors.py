"""Bounded, unauthenticated readers for operator-approved public ATS boards.

An API listing is an unverified lead, not evidence of suitability or independent
proof that a board belongs to an employer. No redirect, proxy, login, scraping,
or URL supplied by a job posting is used to fetch data.
"""
from __future__ import annotations

import hashlib
import http.client
import ipaddress
import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request

MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_RECORDS = 5000
MAX_TIMEOUT = 60.0
_BOARD = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}\Z", re.ASCII)
_PROVIDER_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,199}\Z", re.ASCII)
_ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true",
    "lever": "https://api.lever.co/v0/postings/{board}?mode=json",
}


class ConnectorError(ValueError):
    """Safe, concise source failure; remote exception details are not exposed."""


SourceError = ConnectorError


def safe_public_url(value: object) -> str | None:
    """Accept only syntactically public HTTPS links without credentials.

    This does not resolve DNS or attest employer ownership. These URLs are only
    displayed as links; they are never connector network destinations.
    """
    if not isinstance(value, str) or not value or len(value) > 4096:
        return None
    if any(ord(char) <= 32 or ord(char) == 127 for char in value) or "\\" in value:
        return None
    try:
        parts = urllib.parse.urlsplit(value)
        if parts.scheme.lower() != "https" or parts.username is not None or parts.password is not None:
            return None
        if parts.port not in (None, 443) or not parts.hostname:
            return None
        host = parts.hostname.lower()
        if not host.isascii() or host.endswith("."):
            return None
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            if "." not in host or len(host) > 253:
                return None
            if any(host == suffix or host.endswith("." + suffix)
                   for suffix in ("localhost", "local", "internal", "lan", "home", "test", "invalid", "onion")):
                return None
            labels = host.split(".")
            if not all(re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label, re.ASCII)
                       for label in labels):
                return None
            # Reject legacy numeric IP encodings, including dotted octal forms.
            if not re.search(r"[a-z]", labels[-1], re.ASCII):
                return None
        else:
            if not address.is_global or address.is_multicast or address.is_unspecified:
                return None
        return value
    except (ValueError, UnicodeError):
        return None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _fetch_json(url: str, timeout: float):
    """Read a byte-bounded document with socket and elapsed-time limits."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.netloc not in {"boards-api.greenhouse.io", "api.lever.co"}:
        raise ConnectorError("Source endpoint is not on the HTTPS allowlist")
    # Disable ambient proxy configuration; only the two fixed HTTPS hosts are used.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    request = urllib.request.Request(url, headers={
        "Accept": "application/json", "Accept-Encoding": "identity", "User-Agent": "careerflow/1",
    }, method="GET")
    deadline = time.monotonic() + timeout
    try:
        with opener.open(request, timeout=timeout) as response:
            if response.geturl() != url:
                raise ConnectorError("Source redirect refused")
            if response.getcode() != 200:
                raise ConnectorError("Source returned an unsuccessful HTTP status")
            length = response.headers.get("Content-Length")
            if length is not None:
                try:
                    advertised = int(length)
                except (TypeError, ValueError):
                    raise ConnectorError("Source returned an invalid content length") from None
                if not 0 <= advertised <= MAX_RESPONSE_BYTES:
                    raise ConnectorError("Source response exceeds the byte limit")
            encoding = response.headers.get("Content-Encoding", "identity")
            if encoding.lower() not in ("identity", ""):
                raise ConnectorError("Source returned an unsupported content encoding")
            chunks = []
            size = 0
            read = getattr(response, "read1", response.read)
            while True:
                if time.monotonic() >= deadline:
                    raise ConnectorError("Source request timed out")
                chunk = read(min(65536, MAX_RESPONSE_BYTES + 1 - size))
                if time.monotonic() >= deadline:
                    raise ConnectorError("Source request timed out")
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_RESPONSE_BYTES:
                    raise ConnectorError("Source response exceeds the byte limit")
                chunks.append(chunk)
            raw = b"".join(chunks)
    except urllib.error.HTTPError as exc:
        if 300 <= exc.code < 400:
            message = "Source redirect refused"
        else:
            message = f"Source HTTP failure ({exc.code})"
        exc.close()
        raise ConnectorError(message) from None
    except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):
        raise ConnectorError("Source network request failed or timed out") from None
    try:
        data = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        # This also rejects exponent overflow (for example 1e999), not just NaN.
        json.dumps(data, allow_nan=False)
        return data
    except (ValueError, UnicodeError, RecursionError):
        raise ConnectorError("Source returned malformed JSON") from None


def _text(value: object, label: str, default: str = "unknown", max_length: int = 4096) -> str:
    if value is None:
        return default
    if not isinstance(value, str) or len(value) > max_length:
        raise ConnectorError(f"Source has an invalid {label} field")
    return value.strip() or default


def _stable_id(adapter: str, board: str, provider_id: str) -> str:
    candidate = f"{adapter}-{board}-{provider_id}"
    unambiguous = adapter == "greenhouse" or re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", provider_id, re.ASCII)
    if unambiguous and len(candidate) <= 80 and re.fullmatch(r"[a-z0-9][a-z0-9-]*", candidate, re.ASCII):
        return candidate
    # Hash the original case-sensitive identity, not a lossy sanitised version.
    identity = json.dumps([adapter, board, provider_id], separators=(",", ":"))
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32]
    prefix = board[:24].lower().replace("_", "-")
    return f"{adapter}-{prefix}-{digest}"


def _normalise(item: dict, source: dict) -> dict:
    adapter, board = source["adapter"], source["board"]
    provider_id = item.get("id")
    if adapter == "greenhouse":
        if isinstance(provider_id, bool) or not isinstance(provider_id, (str, int)):
            raise ConnectorError("Source has a missing or invalid job ID")
        provider_id = str(provider_id)
        if not re.fullmatch(r"[0-9]{1,80}", provider_id, re.ASCII):
            raise ConnectorError("Source has an invalid job ID")
        location = item.get("location")
        if location is not None and not isinstance(location, dict):
            raise ConnectorError("Source has an invalid location field")
        title = item.get("title")
        location = (location or {}).get("name")
        official_url = item.get("absolute_url")
        work_mode = "unknown"
    else:
        if not isinstance(provider_id, str) or not _PROVIDER_ID.fullmatch(provider_id):
            raise ConnectorError("Source has a missing or invalid job ID")
        categories = item.get("categories")
        if categories is not None and not isinstance(categories, dict):
            raise ConnectorError("Source has an invalid categories field")
        location = (categories or {}).get("location")
        title = item.get("text")
        official_url = item.get("hostedUrl")
        work_mode = _text(item.get("workplaceType"), "workplace type", max_length=100)
    return {
        "schema_version": 1, "kind": "role", "id": _stable_id(adapter, board, provider_id),
        "title": _text(title, "title", "Untitled role"), "organisation": source["organisation"].strip(),
        "status": "lead", "official_url": safe_public_url(official_url), "source_type": "official_ats",
        "verification_status": "unverified", "last_verified": None, "closing_date": None,
        "location": _text(location, "location"), "work_mode": work_mode, "eligibility": "unknown",
        "match_reasons": [], "gaps": ["Eligibility, fit and current availability have not been verified"],
        "evidence_ids": [], "fit_decision": "pending", "human_interest": False,
        "submitted_at": None, "submission_note": "", "outcome_note": "", "synthetic": False,
    }


def fetch_source(source: dict, *, timeout: float = 20.0) -> list[dict]:
    """Fetch an approved Greenhouse or Lever board, returning only lead records.

    Raises ``ConnectorError`` (a ``ValueError``) on invalid configuration,
    transport failure, oversized documents, or malformed provider data. Nothing
    is written and no credentials are read. Tests can inject ``build_opener``.
    """
    if not isinstance(source, dict):
        raise ConnectorError("Source configuration must be an object")
    adapter, board = source.get("adapter"), source.get("board")
    if not isinstance(adapter, str) or adapter not in _ENDPOINTS:
        raise ConnectorError("Unsupported source adapter")
    if not isinstance(board, str) or not _BOARD.fullmatch(board):
        raise ConnectorError("Source board must be an alphanumeric, underscore or hyphen slug (1–100 characters)")
    organisation = source.get("organisation")
    if not isinstance(organisation, str) or not organisation.strip() or len(organisation) > 300:
        raise ConnectorError("Source organisation must be a non-empty display name (up to 300 characters)")
    if isinstance(timeout, bool) or not isinstance(timeout, (float, int)) or not 0 < timeout <= MAX_TIMEOUT or not math.isfinite(timeout):
        raise ConnectorError("Source timeout must be greater than zero and no more than 60 seconds")
    data = _fetch_json(_ENDPOINTS[adapter].format(board=board), float(timeout))
    if adapter == "greenhouse":
        if not isinstance(data, dict) or not isinstance(data.get("jobs"), list):
            raise ConnectorError("Source JSON must contain a jobs array")
        jobs = data["jobs"]
        metadata = data.get("meta")
        if metadata is not None:
            if not isinstance(metadata, dict):
                raise ConnectorError("Source has invalid response metadata")
            if "total" in metadata:
                total = metadata["total"]
                if isinstance(total, bool) or not isinstance(total, int) or total != len(jobs):
                    raise ConnectorError("Source declared total does not match its returned records")
    else:
        if not isinstance(data, list):
            raise ConnectorError("Source JSON must be a postings array")
        jobs = data
    if len(jobs) > MAX_RECORDS:
        raise ConnectorError("Source response exceeds the record limit")
    records = {}
    for item in jobs:
        if not isinstance(item, dict):
            raise ConnectorError("Source contains a non-object job record")
        record = _normalise(item, source)
        old = records.get(record["id"])
        if old is not None and old != record:
            raise ConnectorError("Source contains conflicting duplicate job IDs")
        records[record["id"]] = record
    return [records[key] for key in sorted(records)]
