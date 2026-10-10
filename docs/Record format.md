# Record format, lifecycle and CLI reference

This page describes the v1 contract. Run `python3 -m careerflow --help` and `python3 -m careerflow COMMAND --help` against the installed version before relying on an interface. The module uses Python 3.11+ and the standard library. The supported environment is Linux/macOS; use WSL for Windows rather than assuming native file-lock compatibility.

In examples, `VAULT`, `ROLE_ID`, `TEXT`, `QUERY` and filenames such as `PATCH.json` are metavariables, not literal values. Supply the approved path or value, quoting shell arguments where needed. No command here authorises an external send or application.

## Storage contract

Markdown records use one flat frontmatter mapping whose values are **JSON literals**:

```markdown
---
schema_version: 1
kind: "evidence"
id: "ev-ops-example"
claim: "Coordinated a fictional community-service rota."
source: "Synthetic documentation example."
status: "synthetic"
boundary: "Not evidence about a real candidate or a measured outcome."
synthetic: true
---
# Rota example

Private supporting detail or, here, clearly synthetic explanatory text.
```

Use double-quoted strings, `true`/`false`, `null`, numbers and JSON arrays/objects as appropriate. Dates and timestamps are quoted strings. This is not a general YAML parser: unquoted strings, duplicate keys, multiline YAML scalars, tags and executable constructors are not part of the format. Ordinary profile prose is not required to use record frontmatter.

All record IDs match `[a-z0-9][a-z0-9-]{0,79}`, match their filename stem exactly and are unique across the record sections. Preserve supplied identifiers exactly; reject a malformed identifier rather than normalising it into a different target. Evidence references must resolve. Role/feedback relationships use exact IDs.

Every `.md` file directly in `roles/`, `evidence/`, `feedback/`, `scans/`, `employers/` or `decisions/` must have valid record frontmatter. Plain prose without that header belongs in an approved profile or application note, not a record section. Employer and decision records need `schema_version: 1`, `kind: "employer"` or `kind: "decision"`, and their exact `id`; the method-specific headings go in the Markdown body. For example, `decisions/source-contract.md` can begin:

```markdown
---
schema_version: 1
kind: "decision"
id: "source-contract"
---
# Source contract — documentation template

Status: proposed. No candidate approval or network permission is implied.

Record the approved lanes, constraints, sources, budgets and decisions here.
```

Keep broad host-agent coverage reviews as `kind: "decision"` notes with their own IDs in `decisions/`, linked to any connector scan. `scans/` contains the connector-generated schema with actual per-source counts and outcomes; do not place arbitrary prose, guessed counts or a fictitious broad-search adapter there.

Core storage writes are atomic, use restrictive record permissions and cooperate through a vault lock. Symlinks and traversal in record paths are rejected. Metadata updates must preserve human-authored bodies. External editors are not automatically lock participants.

### Private vault layout

| Location | Meaning |
|---|---|
| `.private-vault` | Private-vault marker; not an access control |
| `config.json` | Supported settings, no credentials |
| `00-start-here.md` | Generated private-vault entry point |
| `profile/` | Personal context, professional context, factual master, preferences and access decisions |
| `evidence/` | Individual evidence records |
| `roles/` | Vacancy lifecycle records, including retained historical/withheld items |
| `employers/` | Separate employer-watchlist material |
| `applications/` | Role-specific working packs and historical submission material |
| `feedback/` | Immutable, attributable feedback events |
| `scans/` | Dated, structured connector scan records; host coverage reviews belong in `decisions/` |
| `decisions/` | Human-readable approvals, source contracts and change decisions |
| `output/` | Disposable private dashboard, digest and search index |

The prose headings suggested for watchlists, source contracts and extended coverage reviews are methodology, not extra machine-validated fields; their files still need the base record header described above. Preserve the generated schema for connector scans. Keep backups and secrets outside any public or indexed export; do not assume arbitrary metadata creates a new feature.

## Configuration

The core fields are `schema_version: 1`, `mode` (`private` or `demo`), `timezone` (initially `UTC`), `max_verification_age_days` (initially `7`) and `sources` (initially empty). A source entry has `adapter` (`greenhouse` or `lever`), `board` (approved slug) and `organisation` (display name).

See [integrations](Integrations.md) before adding a source. No credentials, arbitrary endpoint URLs, scheduler settings or shell expressions belong in the source list. Unknown additional configuration must never be used to execute code. Markdown remains canonical; `output/search.sqlite3` is derived.

## Role fields

Every role has `schema_version: 1`, `kind: "role"` and a valid `id`, plus:

| Fields | Type / vocabulary |
|---|---|
| `title`, `organisation` | Strings |
| `status` | One lifecycle state below |
| `official_url` | URL string or `null`; public safe source link when verified |
| `source_type` | `official_ats`, `employer`, `aggregator`, `synthetic` |
| `verification_status` | `unverified`, `verified`, `stale`, `closed`, `synthetic` |
| `last_verified` | Timezone-aware ISO timestamp or `null` |
| `closing_date` | ISO date or `null`; no invented time |
| `location`, `work_mode`, `eligibility` | Strings; retain unknowns honestly |
| `match_reasons`, `gaps`, `evidence_ids` | Lists of strings |
| `fit_decision` | `pending` or `approved` |
| `human_interest` | Boolean; not verification or submission |
| `submitted_at` | ISO date or `null` |
| `submission_note`, `outcome_note` | Strings; no inferred receipt/outcome |
| `synthetic` | Boolean |

Source provenance, inspected extracts, exact deadline time if actually stated, conflicts and claim boundaries belong in the Markdown body. Setting `verification_status` is an operator attestation: the software does not inspect a web page to prove that the attestation is true.

## Lifecycle and recommendation rules

| State | Meaning |
|---|---|
| `lead` | Discovered/imported; not yet officially verified |
| `verified` | Official-source check recorded; fit not necessarily approved |
| `current_candidate` | Verified, practical and supported option with approved fit |
| `preparing` | An approved candidate is undergoing application preparation |
| `submitted` | The candidate explicitly confirmed submitting, with date and note |
| `outcome_known` | A later outcome is evidenced; historical submission remains established |
| `withheld_unverified` | A lead cannot yet meet verification requirements |
| `market_intelligence` | Useful context or exploration, not a current recommendation |
| `declined` | Candidate-side decision not to pursue; not an employer rejection |
| `closed` | Source-backed closure |
| `expired` | Recorded deadline has passed; do not infer employer actions |

`current_candidate` and `preparing` require official verification, known practical location/eligibility, an approved fit decision, supported evidence IDs and `last_verified`. Demo-mode synthetic roles are exempt only as labelled demonstrations; they cannot supply real candidate evidence.

The renderer's current lane includes `current_candidate` and `preparing`, subject to feedback hiding, expiry and verification freshness. A stale or expired candidate can be excluded from the current lane and counted as needing recheck **without mutating its stored status**. Hidden roles are not recommended. The submitted/outcome tracker is separate. Reconcile counts from these rules rather than counting all `roles/` files as recommendations.

A date-only deadline displays its date and unknown time. The renderer flags deadlines within three calendar days relative to the configured timezone; that is not a precise 72-hour guarantee. A listing can close earlier or change, so recheck the official source before candidate action.

## Evidence and feedback

Evidence requires `schema_version: 1`, `kind: "evidence"`, `id`, `claim`, `source`, `status`, `boundary` and `synthetic`. Status is `unconfirmed`, `human_confirmed`, `document_verified` or `synthetic`. See [evidence management](Private%20vault.md) for source authority and safe wording.

Feedback requires `schema_version: 1`, `kind: "feedback"`, `id`, `role_id`, `action`, `reason` and `recorded_at`. Actions are:

- `strong_fit`: expressed interest, not confirmed proficiency;
- `hide`: remove from recommendation views; a reason is mandatory;
- `restore`: reverse hiding, not reverify a vacancy;
- `note`: other attributed feedback, not an automatic preference rule.

Feedback records are immutable; event IDs make exact retries idempotent and conflicting reuse an error. Role IDs must exist. Hide/restore order follows `recorded_at` and ID. Feedback cannot mutate employer facts or submission state. Dashboard buttons produce copy-to-agent prompts labelled **NOT SAVED**; there is no hidden write endpoint.

## Command reference

| Command | Effect and limits |
|---|---|
| `python3 -m careerflow init VAULT` | Initialise an empty private vault and profile scaffolds; refuses an already initialised vault |
| `python3 -m careerflow init VAULT --demo` | Create a wholly fictional demo, with clearly synthetic roles/evidence |
| `python3 -m careerflow validate VAULT` | Check supported records, counts, references and gates; errors cause nonzero exit |
| `python3 -m careerflow scan VAULT` | Read configured public boards and import leads; record per-source results; no sources/all sources failed are unsuccessful |
| `python3 -m careerflow import-leads VAULT INPUT.json` | Import a list of normalised roles as unverified leads regardless of requested privileged state |
| `python3 -m careerflow update-role VAULT ROLE_ID --patch PATCH.json` | Patch allowed verification/fit/candidate fields; no ID, submission or outcome changes; validation precedes mutation |
| `python3 -m careerflow feedback VAULT ROLE_ID ACTION --reason TEXT --event-id ID` | Persist and check one feedback event; `--event-id` is optional but useful for retry identity |
| `python3 -m careerflow prepare VAULT ROLE_ID` | Create no-overwrite writing/review scaffolds and move `current_candidate` to `preparing` |
| `python3 -m careerflow prepare VAULT ROLE_ID --resume` | Resume a complete existing scaffold after renewed candidate/freshness checks; leave every application file unchanged |
| `python3 -m careerflow submit VAULT ROLE_ID --date YYYY-MM-DD --confirmation TEXT --human-confirmed` | Record the candidate's report from `preparing`; never submit to an employer |
| `python3 -m careerflow dashboard VAULT` | Validate, then write `output/dashboard.html`; no network or hosting |
| `python3 -m careerflow digest VAULT` | Validate, then write `output/digest.md` and `output/digest.html`; no sending |
| `python3 -m careerflow index VAULT` | Build/rebuild the local SQLite projection |
| `python3 -m careerflow search VAULT QUERY` | Search the local projection for paths/snippets; inspect sources before use |

Check subcommand help for the installed invocation. `update-role` validates supported patch fields and rejects unsupported ones; preserve the error and stop rather than bypassing it. Do not invent `promote`, `apply`, `send`, `schedule`, `delete-evidence`, `connect-account` or `record-outcome` commands. Core v1 has no general profile/evidence CRUD or outcome-update command. Such changes need a candidate-approved diff and safe operator maintenance as described in [profile and evidence](Private%20vault.md), not a bypass of validation or locking.

### Safe role-update pattern

1. Read the exact role and supporting evidence; inspect the official source if verifying it.
2. Write a JSON patch containing only the supported fields needed for the approved decision. Do not insert a submission report into `outcome_note` or make `human_interest` stand for fit approval.
3. Use `update-role`, inspect the result and run validation. Preserve the source/provenance note through approved body editing if needed.
4. Rebuild affected projections within scope. A rejected patch is a blocker to fix, not a reason to edit the SQLite index.

### Human-confirmed submission pattern

Ask for the actual submitted role, date and confirmation if missing. Do not use today's date as a guess. The supplied confirmation is the candidate's report; the `--human-confirmed` flag must reflect a real statement. A generic portal screenshot may need candidate confirmation of role attribution.

After recording, inspect the role and tracker. Preserve unknown employer receipt and outcome, and distinguish actual uploaded material from the prepared pack. An outcome later requires separate evidence and retained submission history. Do not delete submitted material or rewrite its bytes as part of a routine refresh.

## Verification boundary

`validate` is structural and rule-based, not a factual truth oracle. Connector fixtures are not live integration tests. A rendered page is not proof of source freshness, correct fit, active scheduling, completed review or delivery. A successful `submit` command proves only that a human report was recorded.

For repository development, the canonical test command is:

```text
python3 -m unittest discover -s tests -v
```

For an operator, verification also means inspecting exact records and output, reconciling counts, checking source provenance and confirming approvals. If the installed command differs from this contract, stop and consult its help or report the mismatch; do not fabricate output or silently use an unsupported alternative.
