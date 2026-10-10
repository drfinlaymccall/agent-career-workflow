# Search methodology: bounded discovery, verified decisions

A useful search answers two different questions: **what work is worth exploring?** and **which specific vacancies merit a decision now?** Keep career hypotheses, employer targets and verified vacancies separate. A sparse shortlist is preferable to a busy dashboard built from unverified or impractical work.

## 1. Establish a source contract

Create a private human-readable decision record, for example `decisions/source-contract.md`, with `schema_version: 1`, `kind: "decision"` and `id: "source-contract"` in the [documented frontmatter format](Record%20format.md). This is an agreement for the candidate and host agent, not executable configuration. Record:

| Contract item | Required decision |
|---|---|
| Lanes | Core, adjacent and any explicitly authorised exploratory work |
| Constraints | Location, remote-work jurisdiction, hours, work rights, essential credentials, compensation conditions and exclusions |
| Evidence boundary | Which confirmed claims support each lane; material gaps |
| Source families | Relevant local/regional boards, public-purpose sources, specialist sources, direct employers/ATS and broad search |
| Direct coverage | Named approved employers, canonical careers routes and checking cadence |
| Query vocabulary | Responsibilities and synonyms as well as titles; exclusions used deliberately |
| Budget | Query, board/page, verification and elapsed-time limits; what rolls over |
| Verification | Official sources, required fields, conflict treatment, freshness and access-failure rules |
| Reporting | Coverage, discoveries, withheld leads, failures and decisions needing the candidate |
| Review trigger | A regular review or a change in circumstances, repeated low yield or source access |

Do not put unsupported keys into `config.json` and assume they will change programme behaviour. V1 configures only the public connectors and supported local settings; broad search and richer coverage notes are host-agent work.

### Diversify within a bounded budget

Choose source families appropriate to the candidate's actual market rather than hard-coding a country or a single board. An illustrative daily budget is four to eight distinct queries plus a small approved direct-board rotation; agree a smaller budget if needed. This is a method recommendation, not a CLI default.

Include a locally relevant general/professional locator, a purpose- or sector-relevant source, direct employer checks and vocabulary rotation. Search responsibility terms as well as familiar titles. Avoid demanding every preferred keyword in every query: over-constrained queries can hide adjacent work.

For a fictional community-operations search, query families might include service coordination, volunteer scheduling, programme administration and community engagement, qualified by the approved region. Do not put candidate names, private achievements, health details or personal contact information into public queries.

## 2. Use two discovery routes honestly

**Public connectors:** `python3 -m careerflow scan VAULT` reads configured Greenhouse or Lever boards. Every imported record is a lead. API publication does not establish practical eligibility, current fit or independent proof that the board belongs to the intended employer. The candidate must first approve the employer-to-board mapping.

**Host-agent discovery:** an approved search or browser tool can locate opportunities across the source contract. It must record actual queries, pages and access limits. Results can be normalised and imported with `import-leads`; an import cannot authorise a candidate or submission state. The repository does not supply a turnkey broad-web crawler.

Deduplicate by stable source/ATS ID and official destination. Cross-source duplicates may need explicit reconciliation: title and organisation alone can conflate separate vacancies. Preserve discovery provenance and the surviving record ID; do not silently rename IDs referenced by feedback or applications.

A successful connector scan is not evidence that all agreed source families were checked. A search snippet, indexed card or aggregator page is a locator, not proof of a live official vacancy.

## 3. Verify the individual official opportunity

For each retained lead, inspect the employer-controlled listing or an ATS listing linked from the employer's official careers route. Record URLs, retrieval time, what was inspected and unresolved facts in the role body. The operator's `verification_status` entry is an attestation, not a verification service provided by the CLI.

Check:

- the exact title, employer and requisition/ATS identifier;
- whether it is a named vacancy, talent pool, expression of interest, contractor registration or information page;
- current listing/closure evidence, not merely a successful HTTP response;
- location, work mode, remote-work jurisdiction, travel and employment fraction;
- work rights, required credentials/clearances and other essential eligibility;
- contract type, compensation where stated, and substantive responsibilities;
- closing date, time and timezone **only to the precision actually stated**;
- linked position description and visible application instructions;
- conflicts between advert, attachment, structured data and portal.

Unknown eligibility or practical location blocks promotion. Do not infer permission to work in a country from “remote”. Do not treat a listed benefit or compensation range as the candidate's confirmed preference. Where sources conflict, retain both and withhold the affected decision until resolved; a later machine-readable expiry is not evidence of an extension.

`closing_date` stores a date only. Keep any exact official time/timezone and its source in the role body. A date-only listing has **time unknown**; do not invent midnight or a precise remaining-hours countdown. The dashboard's near-deadline treatment is calendar-based in the configured timezone, not an exact 72-hour promise.

Use an aware timestamp for `last_verified`. Freshness is bounded by `max_verification_age_days` and should be reconsidered near submission. A previously verified page becoming inaccessible is stale or unresolved evidence, not proof of closure. Absence from one feed is not closure evidence.

## 4. Make a fit decision before a recommendation

Construct a short fit note:

| Question | Record |
|---|---|
| Is the role practical? | Location, work mode, eligibility and essential constraints, with sources |
| What directly matches? | Specific confirmed evidence IDs and their relevance |
| What transfers? | Adjacent evidence and the change in context or responsibility |
| What is missing? | Material credentials, scope, tools or delivery evidence not established |
| Why would the candidate want it? | Candidate-stated motivation, not an inferred personality trait |
| What is the decision? | Withhold, retain as intelligence, decline, or seek/record approved fit |

Do not rank away an essential barrier with enough minor keyword matches. A human interest signal does not validate qualifications. Conversely, a missing exact title need not invalidate genuinely transferable work if the gap and hiring requirement are clear.

Promote to `current_candidate` only after official verification, known practical location and eligibility, supported evidence references and an approved fit decision. `preparing` also meets those gates. The human approval may be a specific decision or a clearly documented standing rule approved during onboarding; do not invent either. An exploratory option may remain `market_intelligence` until the candidate chooses to assess it fully.

The complete state vocabulary and CLI boundaries are in [records and CLI](Record%20format.md). Separate `submitted` and `outcome_known` from recommendation states. Preparation, enthusiasm and a downloaded form are not submissions.

## 5. Keep the employer watchlist separate

An attractive organisation without a named vacancy belongs in `employers/`, not a fabricated role record. Use the base record header (`schema_version: 1`, `kind: "employer"`, exact unique `id`) and a matching filename; keep watchlist details in the body. A watchlist note should contain:

- official organisation and careers URLs, retrieval date and recruitment route;
- structural relevance to approved lanes, with no implied role fit;
- named vacancy, expression-of-interest route, no vacancy found, or incomplete check;
- unresolved location/work-mode questions and next check;
- candidate priority, reason and any authorised follow-up scope.

A structural comparator is not a vacancy. A careers page inviting CVs is an expression-of-interest route, not permission to send one. Outreach, account registration and uploads require a new explicit approval and are not performed by v1.

## 6. Record the funnel and its limits

Each scan should leave enough evidence to distinguish effort from results:

1. Planned sources and queries; sources actually attempted and completed.
2. Pages or rows inspected, filters/pagination boundaries and truncated coverage.
3. Raw leads, deduplicated leads and duplicates.
4. Individual official pages checked, unresolved pages and access failures.
5. Verified roles, fit decisions, candidate promotions and withheld reasons.
6. Changes to existing records, without overwriting historical scan statements.

The CLI records connector scan results and errors in `scans/`. Host-agent broad-search coverage belongs in a separate `kind: "decision"` record in `decisions/`, linked to the connector scan where applicable; it must not masquerade as a supported connector scan. Do not claim the CLI measured query or verification counts it did not collect. Calculate totals from records rather than estimating from prose.

Distinguish these run outcomes:

- **Completed, no new candidates:** the agreed checks completed but produced no new qualifying decisions.
- **Partial:** some sources succeeded; named failures or incomplete enumeration remain.
- **Failed:** the scan could not perform meaningful retrieval, including all configured connectors failing.
- **Not configured:** no sources were set; this is not a successful empty market scan.
- **Not run:** the report is a preview or stale projection, not a fresh check.

## 7. Learn from feedback without overfitting

Feedback actions are `strong_fit`, `hide`, `restore` and `note`. Keep the exact role ID, the candidate's reason and an event ID when available. A hide reason is mandatory. Record a scoped event through `feedback`; dashboard controls alone copy a prompt and are **not saved feedback**.

Separate three signals:

- **Preference:** what the candidate says attracts or deters them.
- **Action:** a human-confirmed submission is demonstrated interest in that application, not every feature of its advert.
- **Employer outcome:** a rejection, invitation or offer only when evidenced; its cause remains unknown unless communicated.

One dismissal should not exclude an entire sector. One stretch application should not redefine the core lane. A silent employer or rejection is not evidence of why the application did not progress. Preserve later explicit constraints over inferred patterns.

At weekly review, propose a small change with its supporting events, contrary examples and a review date. Keep some approved exploration so discovery does not collapse into a single familiar title. The candidate approves changes to constraints and source coverage. V1 does not implement an automatically trained ranking model; the learning is a reviewable human-agent process.

## Completion gate

A scan is ready for review when records validate, current candidates pass the evidence gate, submitted items remain separate, counts reconcile with the actual projection, and the report names coverage limits and failures. A date-stamped dashboard is not proof that its underlying listings were rechecked.

The daily output should be small: decisions needing attention, new verified candidates, material changes, and a coverage/failure note. The weekly output should reassess lanes, source yield, watchlist priorities, evidence gaps and proposed preference changes. Neither output automatically applies, contacts an employer, buys training or enables a schedule.
