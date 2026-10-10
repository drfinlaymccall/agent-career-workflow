# Profile, evidence and candidate-controlled change

The profile describes the person and their preferences. The evidence registry establishes what may truthfully be claimed. They work together but are not interchangeable: enthusiasm is not competence; a constraint is not an achievement; a polished earlier application is not a new source.

## Canonical material

| Private location | Purpose | Not its purpose |
|---|---|---|
| `profile/Personal context.md` | Practical conditions and candidate-approved context | A required store of diagnoses, family details or identity documents |
| `profile/Professional context.md` | Direction, motivations, working preferences and voice | Proof of every achievement |
| `profile/Master CV.md` | Factual chronology, work, qualifications and supported accomplishments | A role-specific sales document |
| `profile/Role preferences.md` | Approved lanes, constraints, exclusions and exploration | A ranking model silently inferred from clicks |
| `profile/Access decisions.md` | Data scope, account decisions, approvals and revocation | Password or token storage |
| `evidence/<id>.md` | Individually attributable claim and its boundary | An unqualified endorsement of everything in a source |
| `decisions/` | Human-readable decisions, source contract and change review | A second authoritative JSON ledger |

These profile documents are ordinary Markdown. Every file in a record section, including `decisions/` and `employers/`, needs the base frontmatter described in [records and CLI](Record%20format.md); evidence records also need their evidence-specific fields. Keep method notes in the body rather than omitting the header. Do not retrofit undocumented fields or commands merely to make a proposed workflow seem automated.

## Source authority is claim-specific

Use the most appropriate source for the exact claim:

- A candidate's explicit statement can establish their preference or their own report of an action. Label it as candidate-confirmed; do not relabel it documentary verification.
- An original award record can support the qualification it actually states. It does not establish current work rights, professional registration or recent practice.
- A deliverable and its history may support a contribution. A folder name, account login or team outcome does not establish personal responsibility.
- An official employer page establishes what that employer publicly stated at retrieval time. It is not evidence of the candidate's proficiency or a guaranteed vacancy tomorrow.
- An older CV, application or generated summary can identify a question to investigate. Repetition across derived documents is not independent corroboration.

Preserve conflicting dates, titles or scope claims until resolved. Newer is not automatically more authoritative: a new draft can repeat an old error. Ask a narrow question where source inspection cannot settle a consequential point.

## Evidence record contract

The required metadata is `schema_version`, `kind`, `id`, `claim`, `source`, `status`, `boundary` and `synthetic`. The status vocabulary is:

| Value | Meaning | Safe use |
|---|---|---|
| `unconfirmed` | Not yet established | A question or lead; not proof in an application |
| `human_confirmed` | The candidate explicitly confirmed this claim | Use within the confirmed scope; retain the confirmation locator |
| `document_verified` | The named source was inspected and supports the claim | Use only what that source actually establishes |
| `synthetic` | Fictional teaching or test material | Demo vaults and public examples only |

A minimal **synthetic illustration**, not evidence for a real person:

```markdown
---
schema_version: 1
kind: "evidence"
id: "ev-ops-001"
claim: "Maintained a weekly volunteer rota for a community service."
source: "Fictional onboarding exercise; not a real work record."
status: "synthetic"
boundary: "Does not establish line management, safeguarding authority or a service outcome."
synthetic: true
---
# Weekly rota example — synthetic

Contribution: kept availability and shift assignments up to date.

Permitted wording: rota coordination in a fictional exercise.

Not established: team size, hours saved, budget responsibility or a paid role.
```

For real evidence, the body should record enough provenance to recheck the statement: approved private source path or public URL, page/section, who supplied it, when it was inspected or confirmed, the relevant extract where permitted, contribution, context and limits. These are documentation headings, not additional required schema fields. Do not copy whole sensitive documents when a locator and a short bounded note suffice.

### Calibrate the claim, not the person

Distinguish:

- observing a task from performing it;
- training or a new sample from prior professional delivery;
- contributing to a team from leading or owning the work;
- using a product from administering it;
- an appointment from work actually commenced;
- a completed output from an evaluated outcome;
- an estimate from a measured result;
- a credential from current eligibility or practical readiness.

Example: a confirmed rota-coordination claim may be transferable evidence for service administration. It does not become “led organisational workforce transformation”. If no result was measured, describe the action and scope; do not manufacture a percentage improvement.

## Build and maintain the factual Master CV

Keep exact historical titles, dates and credentials. Mark unknowns in private notes rather than repairing them silently. Separate paid work, volunteering, learning and personal samples where that distinction matters. Preserve valuable evidence even when it is omitted from one targeted CV.

For each substantive entry, link the relevant evidence IDs and use wording no stronger than their boundaries. If the master and registry disagree, flag the discrepancy instead of choosing the more impressive version. A new candidate-confirmed fact can update both, with provenance; it must not silently alter a previously submitted application.

Do not store unnecessary full addresses, identity numbers or third-party contacts in the master. Referee nomination, consent, approved contact details and permission to release those details are separate questions.

## Chat-based CRUD: proposal first, exact changes second

The [update-profile prompt](../prompts/update-profile.md) turns a conversation into a controlled change request. It is a host-agent workflow, **not a general CRUD API implemented by the CLI**.

| Request | Agent's first deliverable | Approval and effect |
|---|---|---|
| **Read** | A scoped answer with source locators and unknowns | Read only the approved files; no incidental cloud search |
| **Create** | Proposed new entry, evidence status, source and boundary | Candidate approves storage and wording before creation |
| **Update** | Old/new diff and affected records | Change only the approved fields; preserve unrelated prose |
| **Correct** | Exact disputed statement, correction basis and downstream impact | Correct the canonical facts; retain an appropriate private correction trail |
| **Supersede** | New statement, reason, effective context and link to the earlier version | Preserve the old version as historical, not current evidence |
| **Delete** | Exact targets, references, derivatives, backups and retention consequences | Require explicit deletion confirmation; do not interpret “hide” as erasure |

Requests such as “make this sound more senior” authorise editing, not promotion of responsibility. “I used that system” needs a scope question before it becomes a tool-proficiency claim. A malformed date or identifier stays literal in the change review until the candidate resolves it.

### Safe change sequence

1. Resolve the exact target and read its current version. Check for concurrent edits, a linked submitted application and references from roles or evidence matrices.
2. Separate fact, preference and proposed wording. Name the source and confirmation status for each factual addition; use `unconfirmed` if unresolved.
3. Show a minimal diff, conflicts, affected derivatives and the proposed backup/retention treatment. Seek explicit approval for new sensitive data, material fact changes, deletion and any scope expansion.
4. Take an approved private backup or version snapshot outside the public clone. Keep permissions restrictive. A backup is sensitive data, not an excuse to retain everything indefinitely.
5. For supported role/feedback operations, use the CLI. For other structured record edits, use trusted maintenance tooling that participates in the same vault lock, preserves bodies, validates before replacement and can roll back. V1 has no profile, evidence-delete or outcome-update command. If the host cannot safely implement that protocol, stop at the approved diff for an operator; do not invent a command or race a live scan. Ordinary profile prose can be edited with an approved private editor while other writers are stopped.
6. Check the saved result, exact IDs, references and validation result. Regenerate affected derived views only within the approved scope. Report precisely which files changed and which did not.

The `validate` command checks supported structured records. It is not a semantic fact checker, a complete deletion audit or proof that every prose link resolves. Those checks remain part of the review.

### Conflicts and history

If candidate and document accounts differ, preserve both with dates and ask what can truthfully be stated. A factual correction and a preference change have different effects: correcting a credential may invalidate application wording; changing desired hours need not rewrite historical roles.

For supersession, put the relationship and current/historical status in the Markdown body or decision note; do not invent a new evidence-status enum. Review dependent role `evidence_ids` so stale claims are not silently reused. Do not overwrite submitted files to make them appear consistent with knowledge acquired later. Add a dated correction/addendum and let the candidate decide whether any external correction is appropriate.

## Deletion is wider than removing a Markdown file

Before deleting a referenced evidence record, remove or replace the references with approval and reassess any affected candidate gate. Do not leave an orphaned ID or erase historical submission evidence casually. For immutable feedback, append a permitted correcting event where possible; a wrong-role event needs deliberate maintenance, not mutation disguised as a second event.

List all affected copies: profile and record files, local index, dashboard, digest, application drafts, backups, sync history and any approved remote destination. Rebuild disposable projections after canonical deletion. State which copies were actually removed, which are retained under an agreed policy and which require provider or human action. A local delete does not prove deletion from a model provider, mailbox, remote backup or version history. Do not promise secure erasure from storage media.

**Completion gate:** the candidate-approved change has an attributable source, an accurate diff, no broken required references and a verified saved result. Any external or historical consequence is explicit rather than silently “fixed”.
