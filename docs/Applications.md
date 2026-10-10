# Application workflow: evidence before prose, release before submission

An application pack is an argument built from verified facts for a specific official role. It is not a more impressive rewrite of an old letter. The candidate approves the argument, voice and release; the candidate performs submission. V1 creates writing scaffolds, not final DOCX/PDF exports or an automatic application.

Use the [prepare-application prompt](../prompts/prepare-application.md). Read only the approved private vault and sources necessary for this role.

## Stage A — establish the actual application brief

Resolve the exact role record and official identifier. Confirm that preparation is requested, not merely exploration. Recheck the live official listing and capture the complete source set in the private application area:

- full employer-controlled advert;
- all relevant linked position descriptions and person specifications;
- the actual assessed criteria and any stated weighting;
- the visible application form, required uploads, text fields, formats and limits;
- closing date, and time/timezone if explicitly stated;
- employer candidate-AI guidance, authenticity rules and assessment instructions;
- source URLs, retrieval dates, inaccessible material and conflicts.

A loading placeholder does not mean that a field is absent. A search snippet does not replace the position description. Inspect public form content read-only; do not create an account, accept terms, enter personal details or upload a file merely to investigate. If essential information is behind authentication, ask for approved read-only access or candidate-supplied instructions. Use secure account tooling, never credentials in chat.

Select the correct stream if a vacancy contains alternatives. Distinguish substantive requirements from administrative lines; do not infer weight from list order or a framework level unless the employer says so. Record discrepancies between advert, attachments and form rather than choosing whichever is easiest.

**Deliverable:** an application brief with exact questions, limits, source locators, AI-use boundaries and unresolved facts.

**Gate:** the source set is sufficient to assess and prepare the requested materials. If a consequential attachment, essential condition or AI rule is unresolved, pause that part of the work rather than claiming a complete brief.

## Stage B — evidence matrix and fit decision

Search the factual `profile/Master CV.md`, individual evidence records and approved original supporting material. Prior applications may reveal overlooked evidence, but every recovered claim must be traced back to a candidate confirmation or actual source. Do not assume the strongest evidence is whatever the last CV retained.

Build the matrix **before writing persuasive prose**:

| Field | What to record |
|---|---|
| Requirement ID and exact wording | Include source/page and essential/desirable/weighted status where known |
| Assessment route | CV, letter, question, interview or task, if the employer states it |
| Best direct evidence | Evidence ID, contribution, source locator and confirmed scope |
| Best transferable evidence | Why it is relevant and what does not transfer |
| Gap or unknown | What is not established and why it matters |
| Permitted claim / prohibited inference | Wording boundary for drafting and review |
| Strongest verified evidence omitted | What was not selected and the relevance, space or duplication reason |
| Candidate question | A focused question that could change the evidence decision |
| Placement | Where the selected evidence should appear in the pack |

The matrix grades **evidence strength**, not the candidate's worth. Do not convert a certificate into delivery experience, a team outcome into personal leadership, or a new practice sample into prior employment. Do not invent a metric where the action and scope are all that can be supported.

Classify material gaps:

1. **Not closable before the deadline:** eligibility, required time in practice or historical delivery that cannot be manufactured.
2. **Potentially closable through legitimate work:** a bounded new sample, practice or a missing source the candidate can supply. Estimate time and cost with assumptions, and get approval before undertaking or purchasing anything.
3. **Framing or evidence-retrieval issue:** relevant work exists but is poorly explained or not yet linked to its source.

A newly completed sample remains a new sample. A course recommendation remains a recommendation until the candidate enrols; enrolment is not completion.

**Deliverable:** a sourced matrix and a fit/relevance decision, with the strongest unused evidence and essential barriers visible privately.

**Gate:** the candidate approves continuing, confirms unresolved material facts or accepts that a gap remains. Official verification, practical location/eligibility and supported evidence references must support `current_candidate` before preparation begins. Interest does not waive the evidence gate.

## Stage C — initialise the pack without overwriting history

For an eligible `current_candidate`, use:

```text
python3 -m careerflow prepare VAULT ROLE_ID
```

This creates a no-overwrite application folder with an evidence matrix scaffold, CV/letter writing scaffolds, review guidance and a submission-record placeholder. It transitions the record to `preparing`. Linked evidence is listed, but the requirement-to-evidence assessment still needs review. It does not write a final application, export documents or submit externally. Inspect the returned folder and existing files before editing.

If an existing pack was paused and the role has returned to `current_candidate`, use `prepare VAULT ROLE_ID --resume` after renewed verification. This requires the complete scaffold, rechecks candidate eligibility and freshness, then changes only the role state. It does not overwrite the application files. If the role is already `preparing`, continue reviewing the existing pack without another preparation command. Do not delete files to force preparation through.

Keep three areas distinct in the pack, using the existing scaffold where applicable:

- **Evidence/private review:** source capture, matrix, questions, reviewer reports and decision notes.
- **Working material:** editable drafts, alternatives and candidate-authored notes.
- **Approved release:** only the exact files or paste-ready responses the candidate has approved.

The labels above describe a workflow; not every directory or export is generated by the CLI. Preserve previously submitted bytes and make later corrections as explicit versions or addenda.

## Stage D — draft in the candidate's voice

Ask for information a document cannot establish: genuine motivation, the candidate's own explanation of their contribution, what they learnt and how they want to sound. Never invent a personal connection to the employer.

Agree the allowed assistance mode:

- **Candidate-authored:** provide questions, an evidence menu and sentence/paragraph purposes; critique rather than writing sentences the rules require the candidate to compose.
- **Collaborative drafting:** propose sourced wording for candidate revision where employer rules and the candidate permit it.
- **Editing only:** improve supplied wording without adding new facts or replacing the candidate's reasoning.

If the employer prohibits AI assistance for the material, stop the prohibited assistance. An unclear policy does not authorise assistance during a controlled assessment; seek clarification or keep work to clearly permitted general preparation. Record the policy source and the chosen mode.

For a CV, select and order truthful evidence for the role. Keep historical titles exact; a target title is not a title already held. For a letter, lead with a role-specific reason and the strongest relevant evidence, not generic enthusiasm. For a form answer, address the literal question in the requested format, without a letter's salutation or sign-off. Behavioural questions need an actual example; broad suitability questions may need a concise synthesis.

Every prominent paragraph or bullet should serve a requirement. Use the employer's terminology only where the underlying evidence supports it. Do not keyword-stuff or claim to beat an applicant-tracking system. Prefer legible structure and extractable text, while acknowledging that compatibility depends on the particular portal.

Keep gaps and uncertainty in the private matrix unless the question requires disclosure or the candidate chooses a brief accurate explanation. Omitting an unnecessary apology is legitimate; implying that an essential criterion is met when it is not is not. Ask the candidate to approve the argument and voice before calling the draft representative of them.

**Deliverable:** role-specific drafts or a candidate-authored scaffold, with unresolved facts excluded from asserted claims.

**Gate:** the draft answers the actual brief, every material claim has a source and the candidate approves the assistance mode and voice.

## Stage E — review independently and disposition every finding

First read the actual pack as a brief screener, then as a hiring reviewer:

- Is the leading substantive requirement visible early?
- Does the CV substantiate the letter and each form response?
- Is strong relevant evidence buried or unnecessarily omitted?
- Which claims exceed their sources? Which phrases advertise avoidable gaps?
- What is the single most useful truthful improvement?

Then use the [independent-review prompt](../prompts/independent-review.md) with a separate reviewer, fresh context or another human, within the approved data boundary. “Independent” describes separation from drafting, not a guaranteed impartial hiring judgement. If that review route is unavailable or would violate data consent, record the limitation and seek the candidate's decision; do not invent a completed review.

Ask for numbered, source-located findings. Save a disposition for every finding:

| Finding | Decision | Basis | Action / unresolved question |
|---|---|---|---|
| Stable finding ID | Accept; decline with evidence; candidate decision needed | Exact source or reason | Changed file/section or outstanding question |

Reviewer suggestions are not evidence for new achievements. Rebuild and recheck accepted changes. A reviewer “ready” verdict is not candidate release approval, employer endorsement or a predicted interview outcome. Keep open findings in the review guide, not hidden in applicant-facing text.

**Gate:** every finding has a disposition; essential factual or instruction failures are resolved. Unresolved matters are expressly put to the candidate rather than silently accepted.

## Stage F — mechanical and visual artefact checks

The host's document tools or the candidate produce final formats; v1 does not supply a DOCX/PDF export pipeline. Verify the **exact output files**, not only their Markdown source. Record which tool/version and files were checked where useful.

Mechanical checks:

- requested file types, names, sizes, page/word/character limits and actual portal constraints;
- exact job title, organisation, candidate details and consistent dates across documents;
- no placeholders, internal comments, tracked changes, unsupported claims or private review material;
- non-empty extractable text on every intended page, sensible reading order, supported characters and no missing paragraphs after conversion;
- working hyperlinks with the approved destinations, not just blue text;
- only necessary contact details and approved referee information;
- intended letter date, if used, confirmed for release rather than inferred from build time;
- required declarations and any AI-use acknowledgement answered truthfully by the candidate.

Visual checks:

- inspect every page at ordinary reading size, not just a contact sheet;
- check clipping, overflow, blank pages, bullets and wrapped continuation lines;
- check margins, page balance, typography, contrast and density;
- compare PDF and editable source after every relevant change;
- regenerate previews after rebuilding so stale images cannot certify new files.

Use a simple one-column option where appropriate for a portal, but do not label it universally “ATS-safe”. Mechanical success does not establish role fit; a visually attractive document does not establish factuality.

**Gate:** the recorded checks passed on the current bytes and the candidate has seen the actual release material. If a format cannot be generated or inspected, label the pack a draft and name the blocker.

## Stage G — approve release, then hand submission to the candidate

Prepare a short review guide: verified deadline and unknowns, exact release files, positioning, key evidence boundaries, review/disposition status, checks performed and direct questions. Keep private evidence and review files out of the upload set. Use neutral applicant-facing filenames and remove draft markers from approved release documents.

Ask the candidate to approve this exact version. A prepared or approved pack remains `preparing` until the candidate reports submission. No automatic applying, upload, account creation, outreach or acceptance of employer terms occurs.

A timed test, recorded interview, AI-led interview or proctored task is a separate authenticity and privacy boundary. The agent may help with permitted general practice using dummy data; it must not impersonate the candidate, provide covert live answers, accept recording/data-processing terms or complete an assessed task on their behalf. The candidate reads the official assessment/privacy notice and participates personally.

## Stage H — record what actually happened

After the candidate explicitly confirms submitting the role, record the actual date and their statement using `submit` with `--human-confirmed`; see [the CLI contract](Record%20format.md). That command records a report, not an external submission.

Record the materials actually used and any portal constraint separately from the prepared pack. A retained letter does not prove it was uploaded. A human report is not employer receipt; receipt is not review; review is not an interview or outcome. Unknown receipt and outcome remain unknown. Later outcomes need their own evidence and preserved historical submission information; v1 has no general outcome-update CLI command.

**Completion:** the pack has an attributable evidence basis, candidate-approved voice, reviewer dispositions, current mechanical/visual checks and an explicit release state. Submission and employer outcomes are separate, evidence-backed events, never inferred from preparation effort.
