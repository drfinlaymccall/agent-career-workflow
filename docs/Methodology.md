# Methodology and staged onboarding

This workflow helps a candidate develop an evidence-based career direction, find plausible work and prepare truthful applications. The candidate owns preferences, factual corrections, release decisions and submission. The agent organises and checks; it does not decide what the candidate must want.

Start with an empty private vault **outside the public repository**. The public clone contains tools and synthetic examples, not a place to store a real CV. Markdown is the source of truth; dashboards, digests and the local search index are rebuildable views. A host agent may send text to its model provider even when the files are local: agree that data boundary before reading personal material.

## Reading and prompt map

| Need | Method | Reusable prompt |
|---|---|---|
| Initial interview and staged approval | This guide | [Onboarding](../prompts/onboarding.md) |
| Facts, evidence and corrections | [Profile and evidence](Private%20vault.md) | [Update profile](../prompts/update-profile.md) |
| Career lanes and opportunity discovery | [Search methodology](Search%20and%20discovery.md) | [Daily scan](../prompts/daily-scan.md), [weekly review](../prompts/weekly-review.md) |
| A role-specific application | [Application workflow](Applications.md) | [Prepare application](../prompts/prepare-application.md), [independent review](../prompts/independent-review.md) |
| Storage, accounts and optional tools | [Integrations and data](Integrations.md) | Use the access interview below |
| Recurring runs and optional delivery | [Operations and delivery](Operations%20and%20delivery.md) | Daily and weekly prompts are not schedules |
| Privacy, hostile content and publication | [Security and publication](Privacy%20and%20approvals.md) | Applies to every prompt |
| Record format and actual commands | [Records and CLI](Record%20format.md) | Check installed `--help` before use |

## Stage 0 — permission and a private workspace

Ask:

- Where may working material live? Which exact folders and documents may the agent read? Which may it edit?
- Will a hosted model process these documents? Is redaction or a local-only approach required?
- What must never enter a model prompt, search query, digest or application? Are there confidentiality obligations or third-party details?
- Is this an interview only, a proposed plan, or permission to initialise a vault? May public-web retrieval begin now, later, or not at all?
- Should working drafts remain local? Who may receive an eventual digest, and through which approved route? No sending is the default.

Deliverable: an access decision in `profile/Access decisions.md` naming allowed paths, data classes, operations, prohibited actions and unresolved choices. Record approval in the candidate's terms; do not treat silence as consent.

**Gate:** the candidate approves a private location and an initial read/write boundary. Use `python3 -m careerflow init VAULT` only after that approval. Replace `VAULT` with the chosen path; do not initialise inside the clone. `--demo` is for fictional rehearsal, not an easier route around missing real evidence.

## Stage 1 — personal and professional context

Interview in short groups. Let the candidate skip questions, correct the summary and distinguish a firm constraint from a tentative preference. Do not demand medical, family, financial or identity documents merely to understand working conditions.

### Personal context questions

- What would make the next year of work more workable or worthwhile?
- What location, commute, remote-work jurisdiction and travel arrangements are practical?
- What hours, work fraction, contract duration and start date are possible? Which are non-negotiable?
- Is there a compensation floor or range to use in screening? Is it base pay or total remuneration, in which currency and period? An answer may remain private or unknown.
- Are there scheduling or accessibility needs to reflect in search constraints without recording their underlying cause?
- What workload, values or types of work should be excluded? What could be explored cautiously?

### Professional context questions

- What work have you actually done, and what parts do you want more or less of?
- Which responsibilities were yours, shared, supervised or observed? What was the scale, and how is it known?
- Which recent deliverables best demonstrate your contribution? What may be described publicly?
- Which qualifications, clearances and work rights are relevant? What is confirmed, time-limited or still unknown?
- What tools have you used in real work, in training, in a personal sample or only encountered?
- What motivates a change? What language sounds like you, and what would you never say about yourself?

Deliverables: `profile/Personal context.md` and `profile/Professional context.md`, with candidate-confirmed statements separated from questions. Record practical restrictions rather than unnecessary sensitive explanations. A candidate can approve a limited search with some fields unknown; unknown eligibility must still block a role's promotion where it matters.

**Gate:** the candidate approves the context summary and its permitted uses. No assumption about personality, health, financial urgency or willingness to relocate is promoted into a fact.

## Stage 2 — establish a factual foundation

Request the current CV and a small set of candidate-selected supporting sources. Do not crawl an entire home directory, cloud drive or message history.

Ask:

- Which record is current for job titles, dates, credentials and responsibilities?
- Which achievements can you substantiate? What did you personally do, rather than the whole team?
- Are metrics measured, estimated, remembered or unavailable? What source establishes the denominator and period?
- Which old CV statements need correction? Which valuable examples disappeared during earlier tailoring?
- Which work is confidential? Can a bounded generic description be used, or should it be excluded?

Deliverables:

1. `profile/Master CV.md`: a factual, reusable record rather than a persuasive application for one role.
2. Individual Markdown files in `evidence/`: claim, source, confirmation status and the boundary of what the claim proves.
3. A short unresolved-facts list, with questions that would materially affect screening or application wording.

See [profile and evidence](Private%20vault.md) for provenance and change review. Older applications are leads to facts, not independent proof. The agent may improve structure; it may not invent dates, responsibility, tool proficiency or results.

**Gate:** the candidate confirms the master and claim boundaries sufficiently for the proposed search. Unresolved items remain visibly unconfirmed and are not used as established qualifications.

## Stage 3 — explore role lanes against constraints

Offer a small set of distinct hypotheses, not a long list of job titles:

- **Core lane:** directly evidenced work under acceptable conditions.
- **Adjacent lane:** credible transferable work with named capability or context gaps.
- **Exploratory lane:** a different work pattern or larger pivot, considered only with permission.

For a fictional operations/community-services candidate, these might be service coordination, adjacent programme administration, and a separately authorised part-time community-support exploration. These are illustrations, not recommendations for the real candidate.

For each lane ask: What attracts you? Which duties would you dislike? What evidence supports entry now? Which conditions would rule it out? What would you be willing to learn, and at what cost? Is this a genuine option or only useful market intelligence?

Deliverable: `profile/Role preferences.md` with lane definitions, essential constraints, preferences, exclusions, vocabulary and review triggers. Keep direct evidence, transferable evidence and gaps distinct. A course recommendation must address a recurring verified requirement, not simply sound marketable.

**Gate:** the candidate approves the lanes and exploration budget. A stretch option does not silently widen the core search or weaken work-rights, location or essential-credential gates.

## Stage 4 — choose sources and data integrations

Explain the options before connecting anything:

- Plain Markdown works without a note application, database service or account.
- Obsidian can be an optional local editor; its plugins and sync are separate decisions.
- The included SQLite index is a disposable local search aid, not a second authoritative ledger.
- Public Greenhouse and Lever connectors import leads from explicitly approved boards. They are not a whole-market search engine.
- Broad discovery uses the host agent's approved search/retrieval tools. Optional Gbrain, vector databases and cloud search are not implemented in v1.
- Account linkage, cloud upload, scheduling and delivery each need a separate scope decision. None follows from accepting this repository.

Ask which source families fairly represent the target market, which employers warrant direct checks, and what query/time budget is acceptable. Agree official verification rules, freshness, deadline handling and how unavailable sources will be reported. Put the human-readable source contract in a private decision note; only supported connector settings belong in `config.json`.

Deliverables: a source contract, an access decision for each proposed integration, and a separate employer watchlist for organisations without a verified vacancy. See [integrations](Integrations.md) and [methodology](Search%20and%20discovery.md).

**Gate:** named sources and board mappings are approved. No private data is uploaded or account connected by implication.

## Stage 5 — rehearse once, then approve an operating mode

Run a bounded, no-send rehearsal. Inspect a lead, a rejected or withheld lead, the reason for any recommendation, a dashboard and a digest. If there are no real candidates, keep the lane empty; use a separately labelled demo vault to demonstrate controls rather than fabricating availability.

Ask: Does the rationale match your priorities? Are any gaps concealed? Is any detail too private for the proposed digest? Does the workload fit your week? What should a failed scan look like?

Deliverables: validated records, a dated coverage note, local previews and a short correction list. Dashboard feedback buttons copy an agent prompt; **copying is not saving**. Demonstrate a confirmed feedback write separately if authorised.

**Gate:** the candidate accepts the preview and remaining coverage limits. A local rehearsal does not activate a schedule or send a message. If recurring execution is wanted, follow the separate [scheduling and delivery acceptance contract](Operations%20and%20delivery.md).

## Completion and handover

Onboarding is complete when the candidate has approved the access boundary, context summary, factual foundation, role lanes and source contract, and has seen a no-send rehearsal. Optional integrations can remain declined. Record unresolved facts, the next human decision and the date or event that should trigger review.

A useful handover says: **what is ready, what is not enabled, which facts remain unknown, and what needs the candidate next**. It does not claim that suitable work, interviews, applicant-tracking-system acceptance or an offer will follow.
