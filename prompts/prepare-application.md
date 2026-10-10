# Prepare a role-specific application

## Bounded permissions and output contract

Work only on the exact approved role, private vault, evidence sources and application folder. Inspect public official material read-only within the approved retrieval scope. Draft or edit only where candidate permission and employer AI-use rules allow. Do not create employer accounts, enter personal data into forms, accept terms, upload, contact an employer, apply or participate in an assessment. Do not transmit the pack to an external reviewer/model without data consent.

Produce stage-appropriate artefacts: source brief, evidence matrix before prose, candidate questions, truthful drafts or writing scaffolds, reviewer dispositions, exact-file checks and a clearly labelled release state. A scaffold is not a completed application; a reviewer verdict is not release approval. Stop the affected stage when a material fact, official instruction, permission or authenticity rule is unresolved. Never fill the gap with invented achievements or portal behaviour.

## Inputs

- Approved vault and exact role ID/official URL.
- Candidate request: assess fit, prepare drafts, revise a pack or prepare an approved release.
- Allowed paths and local-write scope; existing application material to preserve.
- Candidate voice and assistance preference: candidate-authored, collaborative or editing only.
- Deadline as officially sourced, including any unknown time/timezone.
- Permitted document-generation and independent-review tools/data routes.

Follow [the application workflow](../docs/Applications.md), [evidence rules](../docs/Private%20vault.md) and [CLI contract](../docs/Record%20format.md). Check installed `--help`; do not invent export or submission commands.

## Staged work

1. **Resolve and verify.** Read the exact existing role; avoid duplicates. Inspect the full official advert, linked position description, person specification, visible form/questions/limits and candidate-AI policy. Capture source locators/retrieval dates privately. A loading screen is not evidence that a field is absent. Preserve conflicts and ask for candidate-supplied instructions if essential content cannot be accessed safely.
2. **Build the brief.** Identify the chosen stream, actual substantive requirements, essential conditions, stated weighting and requested artefacts. Do not infer priority from ordering or invent a deadline time. State the allowed assistance mode and any parts the candidate must author or perform alone.
3. **Matrix before prose.** Search the factual master, individual evidence records and approved original sources. For every requirement record best direct evidence, best transferable evidence, precise source/ID, gap, permitted claim, prohibited inference, candidate question and intended placement. Include the strongest verified evidence omitted and why. Prior applications are discovery leads, not proof.
4. **Resolve material questions and fit.** Ask narrowly about contribution, scope, outcomes, current status and genuine motivation. Distinguish unconfirmed facts from human-confirmed or document-verified evidence. Classify gaps as not closable before deadline, potentially closable by legitimate new work, or framing/retrieval issues. A new sample cannot become historical delivery. Confirm practical location/eligibility and approved fit; stop if a candidate gate fails.
5. **Initialise or resume safely.** With approved local writes and an eligible `current_candidate`, use `prepare`; inspect its returned no-overwrite folder. It creates scaffolds and records `preparing`, not final prose or a submission. Preserve existing drafts and previously submitted bytes. For an existing pack, propose/resume an explicit revision rather than deleting it.
6. **Draft within the voice/policy boundary.** Use candidate-authored prompts/scaffolds where required. Otherwise select and order truthful evidence for the brief. Make the letter a specific argument, the CV its substantiation and form responses direct answers to their exact questions. Keep private gap analysis outside applicant-facing copy without implying an unmet essential criterion is satisfied. Do not invent metrics, titles, motivation, tool mastery or relationships.
7. **Review and disposition.** Perform a short-screen and hiring-review pass, then an authorised independent review using [the reviewer prompt](independent-review.md). Attribute every numbered finding and mark accept, decline with evidence, or candidate decision needed. Reviewer wording is not a factual source. If review is unavailable, say so; do not fabricate a report or imply completion.
8. **Check exact artefacts.** Use approved host document tools for exports; core v1 does not generate final DOCX/PDF. Check actual word/character/page limits, extraction completeness, names/dates, links, placeholders, tracked changes and privacy. Visually inspect every page for clipping, wrapping, blank pages and density. Rebuild and recheck after changes; stale previews do not verify new bytes. No ATS or outcome guarantees.
9. **Seek exact release approval.** Present neutral-named upload files separately from private sources/review notes. State the current checks and open findings. The candidate approves the actual version and submits personally. Do not call a draft release-ready if a required check or source is missing.

## Handover

Return:

- exact role, official deadline precision and source limitations;
- pack location and files actually produced, or proposed content if writes were not authorised;
- strongest evidence, material boundaries and candidate questions;
- assistance mode, review findings/dispositions and exact mechanical/visual checks performed;
- status: scaffold, draft, awaiting review, awaiting candidate release approval, or candidate-approved release;
- “not submitted” unless the candidate has explicitly reported submission.

Only after the candidate reports the exact role and submission date may the dedicated `submit ... --human-confirmed` operation record that report. Preserve which material was actually submitted, unknown employer receipt and separate later outcomes. Do not complete a timed, recorded, AI-led or proctored assessment as the candidate; offer only permitted general preparation.
