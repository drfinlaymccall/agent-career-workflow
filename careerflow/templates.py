"""Embedded templates: installed distributions do not depend on repository docs.

All demonstration content is wholly fictional and intentionally unrelated to any
real person's career. A private vault starts with questions, never sample claims.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import html
import re


DEFAULT_CONFIG = {
    "schema_version": 1,
    "mode": "private",
    "timezone": "UTC",
    "max_verification_age_days": 7,
    "sources": [],
}

PROFILE_FILES = {
    "Personal context.md": """# Personal context

Private interview notes. Leave unanswered questions explicitly unknown.

- What practical constraints affect location, travel, hours or work patterns?
- Which adjustments or accessibility needs should shape the search?
- Which personal details must never be shared with employers or external tools?
- What requires your explicit approval before use?

No answers have been supplied. Do not infer protected characteristics.
""",
    "Professional context.md": """# Professional context

- Which kinds of work do you want to continue, change or stop?
- What responsibilities have you actually held, and in what context?
- Which claims can a source or your explicit confirmation support?
- What must not be inferred from adjacent experience?

Capture bounded evidence in evidence/ before using a claim in an application.
""",
    "Master CV.md": """# Master CV — working source, not a finished application

## Experience

Interview for role, organisation, dates and bounded responsibilities. Unknown.

## Supported achievements

Link each proposed claim to an evidence record. Do not invent metrics or titles.

## Qualifications and skills

Ask for exact names and sources. Do not infer a qualification from experience.

## Review

Human confirmation required before any external use. No final CV exists yet.
""",
    "Role preferences.md": """# Role preferences

- Which role families and responsibilities are of interest?
- Which locations, work modes, remuneration and hours are acceptable?
- What eligibility, travel or right-to-work questions need checking?
- Which constraints are non-negotiable? Which are preferences?
- What does a sufficiently supported fit decision look like?

Unknown is not approval. Feedback expresses preferences, not employer decisions.
""",
    "Access decisions.md": """# Access decisions

Default: local files only. Nothing is sent, submitted or scheduled automatically.

- Which approved public ATS boards may the scan command contact?
- Who confirmed each board-to-employer mapping, and when?
- Which data may an explicitly approved agent or transport receive?
- Who may approve an application and report its external submission?
- Which actions require fresh human confirmation?

No credentials belong in config.json. Do not store tokens or passwords here.
""",
}

START_HERE = """# Start here

This is a private Markdown career-workflow vault. Markdown records are canonical;
output/ is disposable. Keep this vault separate from the public toolkit source.
Do not publish it. Local permissions do not replace full-disk encryption or access
controls on backups and synchronisation services.

## Interview first

Complete the five profile notes without inventing answers. Record bounded claims
in evidence/. Add public leads, verify the official employer source, assess
location and eligibility, and approve fit before making a role a candidate.

## What the labels mean

Verified is an operator/agent attestation, not automatic proof of availability or
board ownership. Refresh stale checks. An ATS listing alone does not establish
suitability. A date-only deadline has no known closing time.

Feedback is an immutable local preference log. It never changes an employer's
state. Preparing creates working scaffolds, not fabricated application prose.
Submit records an explicitly human-confirmed report of an external submission;
it does not submit anything and it does not infer employer receipt or outcome.

Dashboard/digest are local files. Copy-to-agent controls are not saved feedback.
No scan happens unless requested; no email is sent and no scheduling is active.
Sending requires a separately configured, approved agent transport.

## Record format

Use `---`, then one `key: <JSON value>` per line, another `---`, then Markdown.
Quoted strings, JSON booleans, null and JSON lists work; arbitrary YAML does not.
Record IDs must match filenames and use lowercase letters, digits and hyphens.
Keep existing human-authored bodies when changing metadata. Run validation after
manual edits and before acting on the dashboard.
"""

GITIGNORE = """# This vault contains private material; do not publish it.
output/
backups/
backup/
secrets/
.env
.env.*
*.key
*.pem
*.p12
*.bak
*.sqlite3
*.sqlite3-*
.vault.lock
.prepare-*/
.DS_Store
"""

DEMO_PROFILE_FILES = {
    "Personal context.md": """# SYNTHETIC DEMO — personal context

This is a wholly fictional operations/community-services persona, not a real
person. Preferred work pattern: daytime with occasional planned evening events.
Preferred area: Example district. Other personal details are deliberately absent.
Never use these preferences or claims in a real application.
""",
    "Professional context.md": """# SYNTHETIC DEMO — professional context

Fictional experience: coordinating volunteer rotas, community-space bookings and
supplier checklists at Example Community Operations Cooperative. Desired next
step: an operations coordinator post with practical service responsibilities.
No responsibility for regulated advice, clinical work or strategic budgets is
claimed. All evidence remains labelled synthetic, even when it looks plausible.
""",
    "Master CV.md": """# SYNTHETIC DEMO — master CV working source

## Fictional operations/community-services persona

Example Community Operations Cooperative — community operations assistant.
Fictional duties: maintaining a volunteer rota, tracking room bookings and logging
routine supplier follow-ups. No invented quantified improvements or seniority.

## Boundaries

This is not a real person's CV and is not suitable for external use. Claims map
to the synthetic evidence records. Qualifications and dates are not supplied.
""",
    "Role preferences.md": """# SYNTHETIC DEMO — role preferences

Interested in community operations, practical service coordination and volunteer
administration. Example district or a clearly specified hybrid arrangement.
Avoid roles requiring clinical credentials or unsupported budget accountability.
These are fictional preferences and carry no implication of real eligibility.
""",
    "Access decisions.md": """# SYNTHETIC DEMO — access decisions

No sources are configured; demo generation uses no network. No contact details,
credentials or delivery destinations exist. Every organisation and career claim
is invented. This vault must stay in demo mode. Do not relabel synthetic records
as verified evidence or copy them into a private career vault.
""",
}


def demo_evidence() -> list[dict]:
    return [
        {
            "schema_version": 1, "kind": "evidence", "id": "demo-evidence-rota",
            "claim": "Maintained a fictional volunteer rota and noted cover gaps.",
            "source": "Wholly fictional demonstration scenario",
            "status": "synthetic", "boundary": "No recruitment authority or quantified impact claimed.",
            "synthetic": True,
        },
        {
            "schema_version": 1, "kind": "evidence", "id": "demo-evidence-bookings",
            "claim": "Coordinated fictional community-space bookings and handover notes.",
            "source": "Wholly fictional demonstration scenario",
            "status": "synthetic", "boundary": "No safeguarding, clinical or regulated-service credential claimed.",
            "synthetic": True,
        },
        {
            "schema_version": 1, "kind": "evidence", "id": "demo-evidence-suppliers",
            "claim": "Tracked routine fictional supplier follow-ups against a checklist.",
            "source": "Wholly fictional demonstration scenario",
            "status": "synthetic", "boundary": "No budget ownership, procurement authority or savings figure claimed.",
            "synthetic": True,
        },
    ]


def demo_roles(now: datetime) -> list[dict]:
    specs = [
        ("demo-community-ops", "Community operations coordinator", "current_candidate"),
        ("demo-events-ops", "Community events coordinator", "current_candidate"),
        ("demo-service-ops", "Service operations assistant", "preparing"),
        ("demo-facilities-ops", "Community facilities administrator", "submitted"),
        ("demo-outreach-ops", "Outreach logistics coordinator", "withheld_unverified"),
        ("demo-bookings-ops", "Venue bookings coordinator", "closed"),
        ("demo-volunteer-ops", "Volunteer services administrator", "outcome_known"),
        ("demo-neighbourhood-ops", "Neighbourhood support coordinator", "lead"),
    ]
    roles = []
    for index, (identifier, title, status) in enumerate(specs):
        gated = status in ("current_candidate", "preparing")
        submitted = status in ("submitted", "outcome_known")
        roles.append({
            "schema_version": 1, "kind": "role", "id": identifier,
            "title": f"SYNTHETIC: {title}",
            "organisation": "Example Community Operations Cooperative (fictional)",
            "status": status, "official_url": None, "source_type": "synthetic",
            "verification_status": "synthetic", "last_verified": now.isoformat(),
            "closing_date": (now.date() + timedelta(days=2 if index == 0 else 12)).isoformat() if gated else None,
            "location": "Example district (fictional)", "work_mode": "On site (fictional)",
            "eligibility": "Fictional demo eligibility only" if status != "withheld_unverified" else "unknown",
            "match_reasons": ["Fictional rota and service coordination experience"],
            "gaps": ["Demo only: no real employer verification or availability"],
            "evidence_ids": ["demo-evidence-rota", "demo-evidence-bookings"],
            "fit_decision": "approved" if gated else "pending", "human_interest": gated,
            "submitted_at": (now.date() - timedelta(days=5)).isoformat() if submitted else None,
            "submission_note": "Fictional human-confirmed report of an external submission; no real submission occurred." if submitted else "",
            "outcome_note": "Fictional outcome: the example process ended without an offer." if status == "outcome_known" else "",
            "synthetic": True,
        })
    return roles


def demo_feedback(now: datetime) -> list[dict]:
    return [
        {"schema_version": 1, "kind": "feedback", "id": "demo-feedback-strong", "role_id": "demo-community-ops", "action": "strong_fit", "reason": "Fictional preference for practical community operations", "recorded_at": now.isoformat()},
        {"schema_version": 1, "kind": "feedback", "id": "demo-feedback-hide", "role_id": "demo-events-ops", "action": "hide", "reason": "Fictional preference against frequent evening events", "recorded_at": now.isoformat()},
        {"schema_version": 1, "kind": "feedback", "id": "demo-feedback-note", "role_id": "demo-facilities-ops", "action": "note", "reason": "Synthetic submission tracker example; employer receipt remains unknown", "recorded_at": now.isoformat()},
    ]


def _cell(value: str) -> str:
    escaped = html.escape(value, quote=True).replace("\r", " ").replace("\n", " ")
    return re.sub(r"([\\`*_{}\[\]()#+!|>~])", r"\\\1", escaped)


def application_files(role: dict, evidence: list[dict]) -> dict[str, str]:
    banner = "**SYNTHETIC DEMO — never use in a real application.**\n\n" if role["synthetic"] else ""
    heading = f"# {_cell(role['title'])}\n\n{banner}Role ID: `{role['id']}`\n\n"
    matrix = heading + "## Evidence matrix — bounded source material, not approved prose\n\n"
    matrix += "| Evidence ID | Supported claim | Source/status | Boundary | Relevance to check |\n|---|---|---|---|---|\n"
    for item in evidence:
        matrix += f"| `{item['id']}` | {_cell(item['claim'])} | {_cell(item['source'])} ({item['status']}) | {_cell(item['boundary'])} | Human review required |\n"
    matrix += "\n## Unresolved requirements\n\nCheck each requirement against the official source. Mark unsupported requirements\nunknown; do not bridge evidence gaps with invented claims.\n"
    return {
        "Evidence matrix.md": matrix,
        "CV working draft.md": heading + "## CV writing scaffold — unfinished\n\n- Select only relevant, bounded evidence from the matrix.\n- Confirm exact roles, dates, qualifications and responsibility levels.\n- Write proposed bullets here after reviewing the sources.\n- Do not invent metrics, job titles, impact or qualifications.\n\nNo final CV or export has been produced. Human review required.\n",
        "Letter working draft.md": heading + "## Letter writing scaffold — unfinished\n\n1. Confirm the role and organisation against the official source.\n2. Ask the person why this work genuinely interests them.\n3. Select supported examples and state their boundaries.\n4. Address gaps honestly; ask rather than fabricate.\n5. Review tone and every factual claim before producing a final draft.\n\nNo application prose has been generated or sent.\n",
        "Review guide.md": heading + "## Human review gate\n\n- [ ] Official employer/source and current availability rechecked.\n- [ ] Date-only deadline checked; closing time is unknown unless sourced.\n- [ ] Location, work mode and eligibility confirmed.\n- [ ] Every claim has a source and does not exceed its boundary.\n- [ ] Unsupported requirements and other gaps remain explicit.\n- [ ] Personal data and external sharing approved.\n- [ ] Person reviewed and approved the final material.\n- [ ] Any external submission is separately human-confirmed.\n\nThese checkboxes do not submit or send anything. Verification labels are operator\nattestations, not an independent guarantee. Employer receipt/outcome is unknown.\n",
        "Submission record.md": heading + "## Submission placeholder — NOT SUBMITTED\n\nPreparing this folder is not evidence of submission. No application was sent by\nthe toolkit. If the person later reports submitting externally, record the exact\ndate and explicit confirmation with the submit command. Employer receipt and\noutcome remain unknown until separately evidenced.\n\nCanonical lifecycle status is in roles/; this is an editable working note.\n",
    }
