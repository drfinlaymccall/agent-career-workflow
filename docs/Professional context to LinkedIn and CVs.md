# Build your professional context with AI, then use it for LinkedIn and CVs

A useful professional context explains what you do, what you can demonstrate, how you work and where you want to go. Build it once as a private, maintained record. Use AI to question, organise and adapt that record into a public profile and applications.

This guide takes you from scattered documents to a checked LinkedIn profile and a reusable CV process. It works with a conversational AI assistant and a text editor. The repository's private-vault toolkit is optional. The example below is entirely fictional, not an anonymised client account.

## 1. Start with a small private record

Begin with your current CV, a copy of your LinkedIn wording, qualification records and two or three examples of work you can discuss. You do not need a complete archive before starting.

Keep personal records outside this public repository. Give your assistant access only to material appropriate for the service and account you are using. For employer or client work, use an approved environment or prepare a permitted summary. Removing a name alone may not make a distinctive project anonymous.

Use the existing [private vault layout](Private%20vault.md):

| File or folder | What to record |
|---|---|
| `profile/Professional context.md` | Professional identity, specialism, working approach, interests and writing voice |
| `profile/Master CV.md` | Factual chronology, qualifications and supported contributions |
| `evidence/` | A short, sourced record for each substantial example |
| `profile/Role preferences.md` | Types of work you want, constraints and directions to explore |
| `profile/Access decisions.md` | What the assistant may read, store, disclose and change |
| `applications/` | Tailored drafts and retained final application versions |

Start with these headings in `Professional context.md`:

```markdown
# Professional context

Last reviewed: [date]

## Current identity and specialism
[What work defines your practice? What distinctive perspective do you bring?]

## Demonstrated strengths
[Each strength linked to an evidence ID or a source to check.]

## How I work
[Your contribution, judgement, collaboration and checking practices.]

## Direction
[Work you want to pursue; distinguish interests from experience.]

## Voice
[Register, spelling convention, useful examples of your own writing.]

## Boundaries and open questions
[Claims not established, conflicting facts and disclosure limits.]
```

This file gives the assistant orientation. The Master CV and evidence records supply the factual basis for claims. Keep private practical constraints in personal context or role preferences; they need not appear in public copy.

## 2. Use AI as an interviewer

Ask the assistant to read your approved sources before asking questions. Then work through one example at a time. Concrete questions produce more useful material than a request to list your strengths.

Copy and adapt this prompt:

```text
Help me build a professional context for LinkedIn and future CVs.
Read only the files I have authorised. First summarise what they establish
and identify contradictions. Do not treat an earlier CV or AI draft as
independent proof of a claim.

Interview me about one work example at a time. Establish:
1. The problem, audience and constraints.
2. What I personally did and what others did.
3. The methods and tools used, including any AI assistance.
4. What was completed or observed.
5. How the work was checked, by whom and against what.
6. What remains unknown and what may be disclosed.

Ask only questions the available records cannot answer. Separate my
recollections from inspected documentary evidence. Return proposed
context and evidence entries for my review before saving them.
```

If your answer is “I improved the process”, expect a follow-up: what changed, what did you observe and what record supports it? If no effect was measured, describe the completed work. An honest account of a modest contribution is useful evidence.

Include teaching, volunteering, research, independent work and personal projects where relevant. Label their setting accurately. A personal experiment can demonstrate a method without establishing professional delivery at organisational scale.

## 3. Turn examples into bounded evidence

For each example, record the problem, your contribution, the working result and the checking method. Add a source locator and the limit of the claim. A source locator should let you find the relevant page, passage, file version or dated confirmation again.

If you use this toolkit, follow the [record format](Record%20format.md). Each evidence file needs its required frontmatter. The following is a fictional illustration named `ev-library-guide.md`; do not relabel it as your own experience.

```markdown
---
schema_version: 1
kind: "evidence"
id: "ev-library-guide"
claim: "Created and trialled an illustrated catalogue guide with two volunteers."
source: "Entirely fictional example for this guide."
status: "synthetic"
boundary: "One trial; no evidence of continued use or reduced support demand."
synthetic: true
---
# Catalogue guide trial: fictional example

Problem: New library volunteers found the catalogue instructions difficult
to follow during induction.

Contribution: I interviewed the coordinator, rewrote the instructions and
created an illustrated guide. AI suggested alternative wording. I checked
each instruction against the catalogue and selected the final wording.

Working result: Two volunteers each completed three sample searches using
the guide during a trial. I revised one ambiguous instruction afterwards.

Checking method: I observed each search and compared the returned record
with the expected result. The coordinator reviewed the revised guide.

Not established: Continued use, accessibility for other users, fewer
support requests or time savings.

Disclosure: Fictional teaching material only.
```

For your own records, use `unconfirmed`, `human_confirmed` or `document_verified` as appropriate, with `synthetic: false`. Replace the example with your own evidence and provenance. A document-verified status applies to the claim its source supports, not to every statement you might derive from the project. Verification status and permission to publish are separate decisions.

Use these distinctions when reviewing proposed wording:

| Evidence available | Wording it can support | Further evidence needed |
|---|---|---|
| A working deliverable and inspected test | Built and checked a specified resource | Sustained use or broader effectiveness |
| One person's observed use | Supported individual adoption | Team or organisation-wide adoption |
| A published course | Designed and published a course | Participation, learning or workplace outcomes |
| AI-assisted implementation | Specified requirements, directed implementation and reviewed results, where documented | Independent engineering expertise |
| A contextual self-assessment | A development priority or hypothesis to examine | Certified proficiency or externally assessed competence |
| A measured change | The specific result, period and measurement method | Attribution to your work if other factors contributed |

Do not turn an intended benefit into a result. “Designed to reduce repeated questions” and “reduced repeated questions” require different evidence. A second AI model agreeing with a draft is not independent verification of your history.

## 4. Establish your professional identity

Ask the assistant to identify recurring contributions across your evidence. Which problems do you repeatedly address? What perspective or method connects the work? Which direction do you want to develop?

Write a short positioning statement that remains meaningful beyond one vacancy:

> I am a [professional identity] specialising in [distinctive area]. I help [audience] with [problem] through [supported methods]. My work includes [two or three evidence-backed areas].

Use the pattern as a thinking aid, then write it naturally in your own voice. Avoid a catalogue of tools or job titles you hope to acquire. Keep future interests explicit: “I am seeking opportunities to…” is different from claiming experience you have not yet gained.

For the fictional library example, “Volunteer learning coordinator with experience developing practical induction resources” is supported. “Led digital transformation across library services” is not.

## 5. Audit and populate LinkedIn

Inspect the actual profile before drafting replacements. Read each relevant section, including expanded descriptions and linked items. If you cannot give the assistant browser access, copy the current wording yourself. An old export may differ from what is live.

Save a dated private copy of the original wording. Ask for a short prioritised audit and exact replacement text, with the supporting evidence IDs alongside the draft. Fix incorrect facts and unsupported claims first, then improve positioning and examples.

| Section | What to do with your context |
|---|---|
| Headline | State your professional identity, specialism and a few supported areas of practice |
| About | Explain your approach, show selected examples and identify the work you want to pursue |
| Experience | Preserve accurate titles, dates and employment types; distinguish your contribution from the team's work |
| Education | Record degrees, institutions and verified dates; distinguish completion from conferment where relevant |
| Licences and Certifications | Record credentials and correct issuers without duplicating them in Education or inventing dates |
| Skills | Select skills you can explain through evidence; avoid turning self-ratings into proficiency claims |
| Projects | Give enough detail to show the problem, contribution, result and checking method |
| Featured | Link to a small selection of relevant, accessible work you have permission to share |

For the fictional example, a project description could read:

> Developed an illustrated catalogue guide for volunteer induction, using coordinator interviews to identify unclear instructions. Used AI to explore wording and checked each instruction against the catalogue. In a trial, two volunteers each completed three sample searches; observation identified one instruction to revise. Continued use and effects on support demand were not evaluated.

Copy and adapt this prompt:

```text
Compare my current LinkedIn profile with my approved professional context,
Master CV and evidence records. Preserve accurate material and my voice.

Return a prioritised audit and exact proposed text for each changed section.
For each substantive claim, give its evidence ID and any unresolved limit.
Keep my broader professional identity visible. Do not reshape the whole
profile around one vacancy. Separate verified results from intended benefits.

Do not name clients, disclose internal work or link restricted material
without recorded permission. Verify public links before proposing them.
Flag duplicate qualifications, conflicting dates and unsupported scope.
Do not invent missing facts or delete existing entries without approval.

This request is for an audit and drafts. Wait for my approval of the exact
changes before editing the live profile.
```

When you authorise implementation, specify the sections and approved text. Check available notification controls and dismiss prompts to share an update. Treat posting, messaging contacts, requesting recommendations and changing account visibility as separate actions. Re-read each saved field and inspect recent activity for unintended announcements. A notification setting alone is not proof that nothing was broadcast.

Record what was actually saved, with the old wording, new wording, evidence sources and any unresolved gaps. A click on Save is not sufficient verification.

## 6. Derive each CV from the same evidence

Keep the Master CV broad and factual. For an application, select and order evidence against the employer's requirements. Change emphasis and explanation while preserving dates, responsibility and claim boundaries.

Before drafting, make a simple matrix:

| Requirement | Evidence | Relevance | Limit |
|---|---|---|---|
| Develop induction materials | Fictional catalogue-guide trial | Direct evidence of resource development | Small trial only |
| Evaluate learning | Observed sample searches | Transferable evidence of task checking | No assessment of retention or later practice |
| Lead service-wide implementation | None established | Gap | Do not claim this experience |

Then give the assistant this prompt:

```text
Use my approved Master CV and evidence records to prepare a CV for the
attached role. First read the application requirements and any stated
rules about AI use. Build a requirement-to-evidence matrix, separating
direct evidence, transferable evidence and gaps.

Draft within the requested length and format. Use the employer's terminology
only where it accurately describes my work. Preserve historical titles,
dates, contribution boundaries and qualification wording. Do not convert
interests into experience or add unsupported metrics.

Keep evidence IDs and unresolved questions in a private review copy.
Return a clean candidate-facing draft separately. Do not submit it.
```

A concise CV bullet for the fictional example could be:

> Created an illustrated catalogue guide and trialled it with two volunteers, observing three searches each and revising an ambiguous instruction before coordinator review.

It states the contribution and the observed result without implying a measured service improvement. Not every private caveat needs to appear in the CV, but removing a caveat must not make the remaining sentence misleading.

Check the final exported document, not only its source text. Read dates, headings, page breaks and links. Check that text can be selected and copied in a sensible order. Keep a dated copy of the exact version submitted and record submission only when it actually happens. See [application preparation](Applications.md) for the full workflow.

## 7. Keep the record useful over time

After a project milestone or application, capture what changed while the details are available. Add new observations, feedback and source locators. Mark intentions as intentions until evidence changes their status.

```text
Review this new information against my existing professional context and
evidence. Identify which claims it confirms, changes or leaves unresolved.
Show the proposed source-record changes and affected LinkedIn/CV wording.
Preserve earlier submitted versions. Do not treat an interview invitation
or rejection as proof that a particular sentence caused the outcome.
```

Update the authoritative record first, then revise relevant drafts and public sections within the approved scope. Use the [update-profile prompt](../prompts/update-profile.md) for controlled changes. Do not let each new application become a competing source of truth.

Review your context before a substantial application and whenever your role, qualifications or project evidence changes. A useful review asks: what can I now demonstrate, what is no longer current, and what question would improve the next example? You do not need to rewrite the whole portfolio each time.

## Completion check

You have a usable foundation when you can trace each substantial claim to an appropriate source, explain your own contribution and checking method, and identify what remains unknown. Your LinkedIn profile should present a coherent professional identity. Each CV should select relevant evidence from that same record.

Before release, confirm that the text sounds like you, the facts remain within their evidence, links work, disclosure is authorised and the saved or exported version matches what you approved. Keep the public toolkit and your private career records separate throughout.
