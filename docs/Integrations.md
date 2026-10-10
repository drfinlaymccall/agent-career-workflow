# Integrations and data decisions

Start with Markdown and the smallest useful access boundary. A database, note application, connected account or hosted model is an optional trade-off, not an onboarding requirement. Record explicit informed consent before moving personal material to another service.

## What v1 provides, and what it does not

| Capability | Status | Boundary |
|---|---|---|
| Markdown profile and record files | Included; canonical | Private vault outside the public clone |
| Local dashboard and digest | Included; derived files | Generation does not host or deliver them |
| Plain-text `.eml` draft | Repository helper, `scripts/draft_email.py` | Unsent private file; no authentication, network or transport |
| Greenhouse and Lever public-board reads | Included; configured boards only | No credentials; all imported vacancies remain unverified leads |
| Broad web search and official-page inspection | Host-agent workflow | Requires an approved search/browser tool and a bounded source contract |
| Local SQLite index and search | Included; rebuildable | Not a second factual ledger, remote database or vector store |
| Obsidian | Optional editor | No dedicated plugin or sync integration is supplied |
| Gbrain, vector search or cloud search | Not implemented in v1 | Design options only; separate integration and consent required |
| Email/calendar/cloud-drive account access | Not implemented in core | Any host integration requires its own least-privilege approval |
| Scheduler and automatic digest sending | Not implemented in core | Prompts alone do not activate either |
| DOCX/PDF application export | Not implemented in core | Host document tools and independent checks are required |
| Automatic applying or assessment participation | Deliberately excluded | Remains the candidate's action |

Check `python3 -m careerflow --help` and the relevant subcommand's `--help` for the installed interface. Do not guess flags for optional tools or treat a proposed integration as available.

## The data stack

### Markdown first

A private vault contains `profile/`, `evidence/`, `roles/`, `employers/`, `applications/`, `feedback/`, `scans/` and `decisions/`. `output/` holds projections. `config.json` is supported configuration, not an alternative ledger. Keep credentials in a secure account store, not in Markdown or configuration.

Use readable source locators and portable Markdown links. Record-level frontmatter is a deliberately narrow JSON-valued subset, not arbitrary YAML. Every Markdown file directly in a record section, including `decisions/` and `employers/`, requires the appropriate base header; see [record format](Record%20format.md). Plain profile/application notes may remain prose-only. An editor that rewrites quotes, booleans or arrays into another dialect can make a record invalid; run validation after approved edits.

Keep one canonical vault. Do not create two writable “master” copies in a note app and a database. If synchronising private files is approved, specify which side is authoritative, how conflicts pause writes and how deletions propagate. A successful local save does not establish that another device received it.

### Optional Obsidian

Obsidian can open the chosen private folder for local reading and editing. It is not required by the CLI. Preserve the documented frontmatter exactly. Avoid simultaneous edits by the app, host agent and CLI; external editors do not automatically participate in the vault lock.

Decide separately whether to allow plugins, sync and publish features. A local vault is not permission to send its contents through a plugin or enable public publication. Review plugin permissions, provider data handling and backup behaviour before access. Do not treat an Obsidian workspace file as authoritative career evidence.

### Included local SQLite index

```text
python3 -m careerflow index VAULT
python3 -m careerflow search VAULT QUERY
```

The index lives at `output/search.sqlite3`. It is derived from approved vault content and can be rebuilt. Search returns locators/snippets to inspect; a retrieved snippet is not a new fact or proof that a claim is current. After factual changes or deletion, rebuild the index so stale text is not reused.

The index excludes generated output and prohibited secret/system locations according to the implementation. This exclusion is not a licence to place secrets in ordinary evidence files. Indexed profile and application text is still personal data. Keep the index private, and do not publish it because it is “only a cache”.

### Optional Gbrain, vector or cloud retrieval

V1 does not implement these routes. Before choosing one, identify the actual requirement that local search cannot meet. Any future adapter should:

- keep Markdown canonical and return source paths, record IDs and version/retrieval information;
- treat embeddings, extracted chunks and summaries as sensitive derived data;
- permit a narrow allowlist rather than ingesting the entire home directory or vault by default;
- document provider/model, storage region where known, retention, training use, subprocessors and deletion limitations;
- handle corrections, revocation and deletion without silently retaining a stale authoritative copy;
- have a no-write/no-upload preview, failure reporting and a way to rebuild or remove the index;
- provide a consent and access-revocation record before the first transfer.

Do not fabricate an endpoint, schema or capability for a service. Consult its current documentation and installed tool schema when implementing. A name in this guide is not an integration commitment.

## Public-source connector setup

Only the `greenhouse` and `lever` adapters are part of the v1 source contract. Their read endpoints are:

```text
https://boards-api.greenhouse.io/v1/boards/<slug>/jobs?content=true
https://api.lever.co/v0/postings/<slug>?mode=json
```

These are public listing endpoints, **not application submission APIs**. No account, API key or password is needed for the supported reads. The adapter restricts board slugs and endpoints, bounds responses and timeouts, validates JSON shape and rejects arbitrary URLs/redirects. Listing text remains untrusted content.

Before configuring a board:

1. Start at the intended employer's official careers page.
2. Follow its public board link and identify the exact board slug and provider.
3. Record the employer-to-board mapping and candidate approval. A similar name is insufficient.
4. Add only the supported configuration fields. Do not paste full URLs, shell commands or credentials into `board`.
5. Run a bounded scan with network permission, inspect the per-source outcome and verify imported lead records.

Illustrative configuration, using a **fictional, non-working board name**. Do not run it as if it represented a real organisation:

```json
{
  "schema_version": 1,
  "mode": "private",
  "timezone": "UTC",
  "max_verification_age_days": 7,
  "sources": [
    {
      "adapter": "greenhouse",
      "board": "example-community-services",
      "organisation": "Example Community Services (fictional)"
    }
  ]
}
```

Keep actual approved sources in the private vault. Set the timezone deliberately; `UTC` is the initial default, not an inferred candidate location. Unknown configuration keys are not executable instructions or evidence that a feature exists.

`scan` preserves existing status and human-authored content. It does not silently refresh approved facts on an existing role from an API response. Inspect material changes through the official-verification workflow. A disappearance from the response does not authorise closure.

## Host-agent broad discovery

The host supplies search and read tools; the repository supplies the method, records and local views. Authorise source families, queries, time/page budgets and data use. Search with role and region terms, not the candidate's private source text. Move promptly from a locator to official individual verification.

If using `import-leads`, provide a list of normalised role objects in a JSON file using the supported record schema. The importer forces unverified-lead treatment even if the input requests a privileged status. Inspect errors and validate the vault after import. It is not a verification bypass or a way to import confirmations of submission.

A tool outage should produce a coverage gap, not a fabricated search result. Public ATS reads do not replace a diversified search plan.

## Account-linkage interview and consent record

For each proposed integration, write a private decision with these fields in ordinary Markdown:

- **Purpose:** the concrete task and why local/manual work is insufficient.
- **Provider and route:** which account, model/tool and destination will handle data; record a safe label, not a secret.
- **Data:** exact folders/records or data categories, excluded material and redaction plan.
- **Permissions:** read, draft, write, upload or send; required scopes and any unavoidable excess permission.
- **Retention:** local/remote copies, logs, backups, training use where documented and unresolved provider terms.
- **Duration:** one-off or recurring, expiry/review trigger and revocation steps.
- **Verification:** a minimal read-only or no-send test and what would count as success.
- **Consent:** candidate decision, date, limitations and any declined capability.

Examples of narrower choices: a candidate-selected document instead of full-drive access; one dedicated calendar instead of all calendars; approved send-only delivery instead of mailbox reading. Actual services may not offer these scopes. Disclose the mismatch and ask whether to proceed rather than pretending least privilege was achieved.

Do not ask the candidate to paste passwords, verification codes, API keys or sensitive identity numbers into a chat. Use the host's secure authorisation mechanism. If no safe mechanism exists, stop that integration; manual transfer of an approved redacted document may be sufficient.

## Acceptance gates

An integration is **proposed** until its data flow and permissions are approved. It is **configured** only when the actual settings have been read back. It is **verified** only after the agreed bounded test succeeds on the exact target. A local index build is not proof of remote sync; authentication is not proof of email delivery; a saved prompt is not proof of a running schedule.

Record what was enabled and what remains off. The default useful system needs no cloud database, account linkage, automatic delivery or background service.
