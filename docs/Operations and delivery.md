# Operations, scheduling and delivery acceptance contract

V1 runs on demand. `scan` reads configured public sources; `dashboard` and `digest` write local projections. None schedules itself or sends mail. The reusable [daily](../prompts/daily-scan.md) and [weekly](../prompts/weekly-review.md) prompts are platform-neutral task briefs, not installed automation.

A host scheduler or delivery transport can be integrated separately with explicit approval. Until that happens, describe the system as **manual, local and no-send**.

## The manual operating loop

For an approved vault and configured sources:

```text
python3 -m careerflow validate VAULT
python3 -m careerflow scan VAULT
python3 -m careerflow validate VAULT
python3 -m careerflow dashboard VAULT
python3 -m careerflow digest VAULT
```

Run the scan only when its network access is authorised. If there are no configured sources or all sources fail, it exits unsuccessfully; do not discard that result and describe an empty digest as a successful scan. Inspect the scan record even when only some sources fail. Rendering is local and does not independently verify listings.

Broad-search discovery, official verification, fit decisions and factual correction are additional host-agent tasks governed by the source contract. A connector-only run must be labelled connector-only. Existing statuses, feedback and submissions must survive imports and refreshes.

### Daily review surface

Keep the report short and actionable:

1. Current candidates needing attention, with verified deadline precision and any uncertainty.
2. Newly verified candidates and the decision required from the candidate.
3. Material source-backed changes to existing opportunities.
4. Human-confirmed submission or employer-evidence changes, separate from recommendations.
5. Sources actually checked, withheld leads, failures and coverage limits.

No new candidate is a valid result. Do not fill the report with weak matches. A source failure is not a no-result day, and an old projection is not a fresh scan. Count current candidates and submissions from the actual records/projection rules, not a remembered total.

### Weekly review surface

Review the canonical profile, feedback and dated scans rather than only the last dashboard. Compare source yield and missing coverage; revisit the separate employer watchlist; check stale candidates, active preparation, confirmed submissions and unresolved outcomes. Propose bounded changes to search vocabulary, lanes or evidence development. The candidate approves changed constraints, paid learning, account access and new recurring behaviour.

Keep the weekly pass distinct from the daily send. A manual deep search does not authorise a second digest or a replay of a send-capable daily job.

## Scheduling acceptance contract

Before enabling any host schedule, record and approve all of the following in a private decision note. These are integration requirements, not `config.json` fields or core CLI flags.

| Area | Required agreement and verification |
|---|---|
| Task identity | Exact prompt version, job identity, owner and purpose |
| Scope | Approved vault, readable paths, write operations, public sources, budgets and prohibitions |
| Runtime | Actual host/tool availability, working directory, interpreter and installed CLI interface |
| Cadence | Desired wall-clock time, days, IANA timezone, effective scheduler timezone and next run |
| DST | Whether cadence follows local wall time or a fixed UTC time; missing/repeated-hour behaviour |
| Overlap | One vault writer at a time; lock/timeout behaviour; do not bypass a busy lock |
| Run evidence | Durable run ID, start/end, actual scan/source outcomes, validation and output locations |
| Delivery | None/local by default, or exact approved account, target and transport |
| Failure policy | Where failures are recorded; whether a sanitised failure notice is authorised |
| Cost and exposure | Query/tool budget, provider data handling and retention |
| Control | How to pause, revoke access, change cadence and recover without duplicate sends |

Read the actual scheduler documentation and tool schema before configuring it. Do not invent scheduler commands or assume a cron expression carries a timezone. A host's default timezone can differ from the vault's display timezone. Read back the stored enabled state, prompt, target and next scheduled run after any change.

### Timezone and DST checks

Agree whether “09:00 daily” means 09:00 in the candidate's chosen zone throughout the year or a fixed UTC instant. Check the scheduler's behaviour around a daylight-saving transition, including nonexistent or repeated local times; use its preview/test facility if available. If it cannot provide the requested semantics, disclose that and agree a review or alternative. Never silently promise a year-round local time from a host-local cron expression.

The role `closing_date` is date-only. The near-deadline display uses calendar dates in the configured zone and must say when closing time is unknown. Any exact employer time belongs with its official source; operational scheduling does not resolve an ambiguous deadline.

## Delivery acceptance contract

Core v1 has no SMTP/send adapter. The repository helper `scripts/draft_email.py` creates an **unsent, plain-text `.eml` file**, not a delivery. From the repository checkout, its interface is:

```text
python3 scripts/draft_email.py DIGEST.md DRAFT.eml --sender ADDRESS --recipient ADDRESS --subject TEXT
```

Replace the metavariables with approved values and quote arguments where needed. Use `python3 scripts/draft_email.py --help` to check the installed script. The draft contains sender/recipient details and is private. This helper does not convert Markdown into HTML, authenticate an account, invoke a transport or prove that a mail client sent anything. Do not open/import it into a send-capable workflow automatically.

A host transport needs separate approval specifying:

- exact sender/account and recipient/channel; never infer a target from a display name;
- one-off test versus standing recurring permission;
- what data may be included, what must be redacted and whether failure notices are allowed;
- one delivery route, maximum frequency and duplicate-prevention strategy;
- transport success response, message identifier and available read-back evidence;
- how ambiguous send status will be resolved without blindly resending;
- storage and retention for local reports and delivery evidence.

Send the completed sanitised digest, not raw CVs, correspondence, credentials, detailed private evidence or diagnostic logs. The HTML digest is a local projection; a transport that expects HTML must receive rendered HTML, not raw Markdown with a MIME label. Check the real transport contract and use structured arguments rather than shell interpolation of report text.

### One-send procedure

This is a conservative operating contract, not an exactly-once guarantee supplied by the repository:

1. Validate canonical records and generate the final local report. Record a durable run key, output identity and delivery target before dispatch.
2. Check for existing delivery evidence for that run/target. If present, do not send again. If a prior attempt is unresolved, stop for reconciliation.
3. Inspect the sanitised preview and confirm the approved scope. A test has a prominent test label and needs its own approval.
4. Invoke the approved transport once. Use provider idempotency only if the real API supports it; do not invent a parameter.
5. Save the actual status and message identifier immediately. Read back the exact sent item/target through the provider where available. Distinguish accepted by transport, verified in sent history and recipient delivery/read evidence.
6. Report the observed result. Do not say “delivered” from a scheduler exit code or a local draft. Do not send a second copy to repair formatting, attach a message ID or update the delivery line.

The dispatch copy is written before the send; it must not pre-claim its own successful delivery. Put the eventual send outcome in the local run/transport record and the host's completion report.

### Ambiguous send: stop, inspect, do not retry

A timeout, worker crash or parser failure after dispatch may occur after the provider accepted the message. Do not replay a send-capable job or try another account to discover what happened. Inspect durable run evidence, the actual helper response schema and the provider's sent history using the run's identifier and target. If the transport offers no reliable read-back, report the uncertainty and ask the candidate before any fresh attempt.

A failure known to have happened before dispatch is different from an unknown post-dispatch result. Record that distinction. A human-approved resend should refer to the unresolved attempt and its duplicate risk; it is not an automatic recovery step.

## Run outcomes and user-facing wording

These are reporting categories, not new role lifecycle values:

| Observation | Honest report |
|---|---|
| All agreed checks completed, no qualifying changes | Completed; no new candidates in the checked sources |
| Some checks succeeded, others failed | Partial; name the missing coverage |
| All connector sources failed | Failed; no fresh connector coverage established |
| No configured connector source | Not configured; no connector scan completed |
| Dashboard/digest rendered without a scan | Local projection; freshness follows existing records |
| Local files generated, no transport enabled | Prepared locally; not sent |
| Transport accepted, read-back unavailable | Accepted by transport; further delivery evidence unavailable |
| Send outcome uncertain | Ambiguous; no retry performed |
| Schedule saved/enabled, never observed running | Configured; first run unverified |
| Scheduler reports success but transport failed | Task execution and delivery differ; report both |

## Acceptance test before calling automation active

Use synthetic content or an approved minimally revealing preview. Do not run a real send-capable recurring job merely to test its prompt.

- **Configuration read-back:** verify the actual job, prompt, timezone, enabled state, exact working directory and delivery target.
- **No-send execution:** run the task without dispatch and inspect records, validation, projection counts, source failures and privacy.
- **Failure exercise:** verify handling of no sources, one failed source and all failed sources without inventing a successful scan. Unit fixtures are not live-source tests.
- **Duplicate control:** demonstrate that an already recorded or ambiguous delivery attempt will not be sent again. Review crash windows explicitly.
- **Optional single send:** only with explicit test approval; inspect the exact result and read-back evidence, then stop.
- **First scheduled run:** observe it separately. Saved configuration and a manual rehearsal do not prove the scheduler executed or delivery succeeded.

Report the status of each gate separately. Scheduling may be configured but not yet exercised; delivery may remain off while the local workflow is fully useful.

## Recovery and maintenance

Preserve failed/partial scan history. Do not overwrite old notes to imply broader coverage than was obtained. Recheck stale official pages before promotion or release; keep closure and expiry evidence distinct from access failures. Rebuild derived views after approved canonical changes, not as a substitute for resolving validation errors.

Pause writers before manual record maintenance, preserve approved private backups, and use the shared lock for supported writes. If consent is revoked, pause the external route, read back the disabled state, remove credentials through the secure account mechanism and document any remote copies still needing deletion. A local change does not prove remote revocation or erasure.
