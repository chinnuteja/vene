# Bring Vene — technical implementation plan, Phases 9–12

Created: 16 October 2026. Continues IMPLEMENTATION_PLAN.md (Phases 1–8).

This is the runbook for the next product step. Read BUILD_STATUS.md for actual progress. This plan describes work to do; unchecked tests and browser checks are not completed work. The rules, invariants, reuse policy, browser protocol and evidence format in IMPLEMENTATION_PLAN.md continue to apply unless this document explicitly extends them.

Company boundaries: VENE_COMPANY_CONTEXT.md. Earlier ranking of alternatives: VENE_FOUNDER_VERDICT_2026-10-11.md and VENE_GLOBAL_CHALLENGE_2026-10-11.md.

## Why these four phases

Phases 1–8 built a trustworthy visit companion: scoped preparation, real multiparty media, grounded understanding, permissioned speech and one sandbox errand (a lab booking). The earlier research correctly warned that "help during the visit" alone is crowded. Visit summarizers and note-takers already exist.

What Vene sells is follow-through: appointments, referrals, refills, coverage, paperwork and family coordination, executed with patient approval while clinicians keep clinical decisions. These phases make the visit the moment that work starts, rather than a conversation the patient must remember and act on later.

Supporting evidence for the problem, not for our solution's effect:

- Patients forget 40–80% of medical information immediately, and almost half of what is remembered is incorrect ([Kessels 2003](https://pmc.ncbi.nlm.nih.gov/articles/PMC539473/)).
- In one large health system, only 34.8% of primary-care referral scheduling attempts produced a documented completed specialist appointment; missing documentation explains part of the gap ([J Gen Intern Med](https://pubmed.ncbi.nlm.nih.gov/29532299/)).
- Orders placed during telehealth visits were completed on time 42.6% of the time versus 58.4% in person ([JAMA Network Open](https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2811870)).

The product sentence for this round: **by the time the patient reaches the car, everything the clinician asked for is already moving, and anything that would have blocked it was raised while the clinician was still in the room.**

| Phase | Product outcome | Why it matters for Vene |
|---|---|---|
| 9 | Walk-out follow-through: several errand types executed from one visit with a live checklist | Directly extends Vene's advertised errands; the most visible result |
| 10 | In-room obstacle catch: scheduling, coverage and pharmacy problems raised while the clinician can still resolve them | The blueprint's flagship, widened to coverage and pharmacy, which Vene already handles |
| 11 | Preparation drafted from open loops in Vene's memory | Uses memory Vene already holds; removes patient homework |
| 12 | Phone on the table and dial-in participation | Fits the in-person and telephone visits most patients actually have; "the doctor needs no account" |

Do not reopen idea selection. Do not merge these into one oversized demonstration step; each phase has its own gates.

## Delivery target and execution rules

Deliver, on the same codebase and domain services, a visit in which:

1. Maria opens preparation and finds an agenda Vene drafted from her real open loops. She keeps or drops items and approves with one deliberate action.
2. During the visit, as the clinician orders a lab, imaging, a referral and a prescription change, Vene checks each one against the relevant sandbox institution. It privately cues Maria about any real obstacle, such as prior authorization being required, a drug not on the formulary or no slot in the requested window. With agreement, it raises the obstacle aloud while the clinician can resolve it.
3. At the end, Maria reviews one "before you leave" list and approves the ready errands. Each errand dispatches independently, and the checklist fills in from actual sandbox receipts. Her family member receives a scoped ride request and answers it.
4. The same flow works with one patient phone on the table, and with a participant who dials in.

Execution rules, unchanged from Phases 1–8:

- Implement, run meaningful tests, start the local app, inspect it in a browser, fix observed failures, then record evidence in BUILD_STATUS.md and docs/qa/phase-NN.md.
- The fixture and live configurations use the same domain services. Never turn a failing live integration into a scripted success.
- Every institution in this plan is a clearly labelled local sandbox. No real clinic, pharmacy, health plan, telephone number or patient is contacted. No deployment.
- Continue independent work when a credential gate is unavailable, and record that gate as unverified.
- Do not claim clinical, production or regulatory readiness.

## Groundwork before Phase 9: portable runtime

Phases 1–8 were verified on Windows only. The launchers hard-code `.venv/Scripts/python.exe`, `livekit-server.exe` and PowerShell. Development now also happens in a Linux cloud container, and founders typically use macOS.

**Build**

1. Resolve the virtual-environment interpreter per platform in dev.mjs, contracts.mjs, browser-check.mjs and every spawn site: `.venv/Scripts/python.exe` on Windows, `.venv/bin/python` elsewhere.
2. Pin official LiveKit server archives for Linux x64 and macOS arm64/x64 in infra/livekit-binary.json with SHA-256, and extend setup to install the platform's binary under .local/tools.
3. Add `scripts/setup.sh`, `scripts/dev.sh`, `scripts/check.sh` and `scripts/stop.sh` (or a single Node entry point invoked by thin wrappers) with the same flags and the same owned-process rules as the PowerShell scripts. Use a system or project-local Postgres; never stop an unrelated server.
4. Make the Playwright configuration accept an explicit Chromium executable path when the pinned browser revision is unavailable.
5. Stop the browser suites from overwriting committed QA evidence. Write run outputs under .local, and promote selected evidence to docs/qa explicitly.

**Tests**

- On Linux: full backend suite against Postgres, contract drift, typecheck, production build and the complete deterministic browser suite including media.
- Windows behavior is unchanged: the existing scripts/check.ps1 -All still passes. If no Windows host is available in a session, record that as unverified.

**Exit evidence**

docs/qa/groundwork-portable.md records the platform, versions, commands and results. Unrun platforms are listed as open.

## Technical decisions added in this round

| Area | Decision |
|---|---|
| Errand model | One errand registry. Each kind declares its institution, eligibility, prerequisites, lookup, commit and receipt validation. Every kind reuses the existing scope → fingerprint → approval digest → outbox → lease → reconcile pipeline. No second execution system. |
| Sandbox institutions | The existing sandbox office process hosts separate institutions with separate state, tokens and request-ID spaces: lab, imaging center, specialist intake, pharmacy and health plan. Each response carries `sandbox: true` and the institution name. |
| Obstacles | Deterministic records derived from institution responses. The model never produces an obstacle, coverage fact or availability. Templates phrase cues; the model is not needed for this path. |
| Memory | A `MemoryPort` interface with a Postgres implementation over prior encounters, executions, receipts and messages. Shaped so Vene's existing memory (Zep, per its privacy policy) can implement it later. |
| Shared-device audio | One authenticated patient connection publishes a room microphone; Deepgram diarization supplies speaker labels; the patient maps labels to people. Labels are attribution only. |
| Telephone | LiveKit SIP with a Twilio inbound trunk, joining the same room. Credential-gated. |
| Live updates | Execution and checklist state join the authenticated, filtered SSE replacement stream instead of separate one-second polling. |

## Core contracts and invariants added in this round

Define these before implementing the corresponding phase:

- **PlanItem.kind**: `lab | imaging | referral | prescription | other`. Set by validated interpretation or by a human. Errand eligibility uses `kind`, never a regex over free text.
- **Errand**: kind, institution, material parameters, plan fingerprint, prerequisites, digest, state, receipt. Generalizes the current ExecutionRecord.
- **Prerequisite**: `clinician_confirmation | order | prior_authorization | supporting_document | patient_choice`. Each one is satisfied only by a specific human action or an institution receipt.
- **Obstacle**: kind, affected plan item and errand, institution response reference, `checked_at`, `expires_at`, who can resolve it (clinician, office, patient, family) and resolution state.
- **ApprovalBundle**: the patient's single approval over an explicit set of errand digests. It is a convenience over individual approvals, not a transaction.
- **OpenLoop**: source record reference, age, kind, last institution status and proposed agenda wording with citation.
- **SpeakerAttribution**: diarization label → patient-attested person, with confidence and the attesting session.
- **CareCircleRequest**: a scoped request to a family member (for example, a ride) with only the patient-selected fields, and a family response.

Preserve and extend the orthogonal states: discussed, patient-understood, clinician-confirmed, order-available, prior-authorization-status, patient-authorized, dispatched and externally-confirmed are distinct facts.

New invariants:

1. Availability, coverage, formulary, stock and authorization facts come only from institution responses with a receipt or response reference and a timestamp. A model can neither assert nor alter them.
2. A coverage obstacle states the plan's rule and the plan-supplied options. Vene never recommends a medication, test or timing. The clinician decides what the fact means for care.
3. Standing permission to check, granted during preparation, never permits a write. Every booking, submission or message still needs its own approval, bound to its digest.
4. An approval bundle is not atomic across institutions. Each errand dispatches, fails and reconciles independently, and the checklist shows partial results honestly.
5. A corrected plan item invalidates its pending errands, obstacles and bundle membership. A confirmed external result is never "undone" locally; correcting it needs an explicit new errand, as in Phase 6.
6. A diarized speaker label never gains authority. A patient-attested "Dr. Chen said this" is evidence attribution only. It cannot satisfy clinician confirmation; the institution's own order receipt remains required.
7. A telephone caller's role comes from invitation-bound admission, never from caller ID or what the caller says.
8. Open loops shown in preparation obey the patient's audiences. Earlier private items never become visible to a new audience without a new explicit share.
9. A family member's "yes, I can drive" is the family member's commitment, not a booked ride and not a change to the clinical plan.

## Phase 9 — walk-out follow-through

**Outcome:** one visit produces several real sandbox errands. The patient approves them together, and a live checklist fills in from actual receipts before the visit page is closed.

**Build**

1. Add `PlanItem.kind` (migration 0010). Extend `ProposedStep.topic` to `lab | imaging | referral | prescription | other` with prompt `visit-extraction-v5`, still one step per topic. Keep human corrections authoritative over interpretation.
2. Create `execution/errands.py`, an errand registry. Move the lab-specific logic (the regex eligibility, slot model and `/lookup`/`/bookings` paths) behind a `lab` errand definition with no behavior change, proven by the existing Phase 6 suite. Then add:
   - **imaging**: slot lookup; prerequisites are order and prior authorization (Phase 10 supplies the authorization fact; until then it shows as an unresolved dependency).
   - **referral**: specialist intake submission; prerequisite is a supporting document from the referring office. The receipt is an intake acknowledgement, plus an offered appointment when the specialist returns one. Seeded Maria already has "Referral document still needed", so this resolves a real open item.
   - **prescription**: pharmacy readiness check and a "prepare for pickup" request; the receipt gives a ready time. No dose, drug choice or substitution is ever sent or proposed.
3. Split the sandbox office into institutions with separate `OfficeStateRecord` rows, tokens and request-ID namespaces: `lab`, `imaging`, `specialist`, `pharmacy`. Each keeps the existing failure modes (no slot, expired, delayed, rejected, timeout after write, duplicate callback) and signed callbacks.
4. Generalize the action digest and `scope_valid` to include errand kind, institution and kind-specific parameters. Keep stable request IDs per errand so retries never duplicate.
5. Add the approval bundle: `POST /errands/approve-bundle` takes a list of digests, re-verifies each in one transaction, and queues those that are ready. Errands that are not ready stay waiting with their named missing prerequisite. Return per-errand outcomes.
6. Add a care-circle ride request: the patient selects a confirmed errand and a family member. The family member receives only the selected fields (when and where) through the existing family outbox and answers Yes or No in their own authenticated view. Record the answer as a family fact.
7. Build the **Before you leave** checklist in the visit and follow-up views. Each row shows the step, its institution, its missing prerequisite in plain words, and each state transition (waiting → approved → sent → confirmed or rejected or unknown) with the receipt time. One primary action: "Approve the ready steps". Clinician and family views show only shared steps, with honest statuses.
8. Move execution and checklist state into the filtered SSE replacement so updates arrive without polling. Keep the guest-payload isolation tests.
9. Add a scenario fixture where the clinician orders a lab, imaging and a prescription and asks the office to send the referral document. Use the same fixture-turn path as Phase 4, and also original synthetic audio for the live gate.

**Reuse**

Reuse the Phase 6/7 execution pipeline, outboxes, signed callbacks, family delivery and fixture-turn infrastructure. Use no workflow engine and no FHIR server. A sandbox response is a sandbox receipt; do not represent a generated FHIR resource as a sent request.

**Tests**

- The existing Phase 6 lab tests pass unchanged after the lab moves into the registry.
- Each kind: a lookup outside scope is denied before data leaves the service; a missing prerequisite blocks dispatch and is named; a correction mid-lookup invalidates the result; a timeout after write reconciles without a second write; duplicate callbacks attach once.
- A bundle with one rejected and two confirmed errands shows exactly that; nothing is rolled back or retried automatically.
- A bundle digest submitted after one member changed is refused for that member only, with a reason.
- Concurrent bundle approvals produce one dispatch per errand.
- A prescription errand payload contains no drug-change instruction; the pharmacy sandbox rejects such fields.
- The family view never contains unselected fields, private steps or other errands; a revoked family member cannot answer.
- SSE payloads for clinician and family contain only shared steps and their permitted errand fields.
- Interpretation: v5 produces at most one step per topic, and unsupported owner/date/location fields remain null (fixture and live gates).

**Local browser checkpoint**

Run the scenario with patient, clinician and family in separate contexts. Confirm the checklist fills in live from receipts. Repeat with the imaging center returning no slot and the pharmacy timing out after write, and confirm partial results are honest. Answer the ride request as family. Inspect desktop and mobile, keyboard flow, console and failed requests.

**Exit evidence**

docs/qa/phase-09.md records the commands and results, the receipt sequence, screenshots, and the elapsed time from end of conversation to the last sandbox confirmation in the scenario (recorded as a sandbox measurement, not a real-world claim).

## Phase 10 — catch the obstacle while the clinician is in the room

**Outcome:** shortly after a step is discussed, Vene checks it against the relevant sandbox institution and health plan. A real obstacle reaches the patient privately within seconds and, with agreement, is raised aloud so the clinician can resolve it before the visit ends.

**Build**

1. Add a sandbox **health plan** institution for the fictional member:
   - Coverage rules: the imaging study requires prior authorization; one drug is non-formulary with plan-listed covered alternatives in the same class.
   - Prior-authorization submission returns a reference and moves pending → approved or denied through a delayed signed callback.
   - Plan data is a seeded synthetic rule table, clearly labelled.
2. Add a **standing check permission** to preparation: "During my visit, Vene may check scheduling, coverage and pharmacy for the steps we discuss." It is per kind, bound to the patient session, revocable at any time, and advances the consent epoch. It never authorizes a write.
3. Add a feasibility worker. When a validated plan item of an eligible kind appears or changes, it enqueues read-only checks. Results are fenced by plan fingerprint and epoch, exactly as Phase 6 lookups are.
4. Add an `Obstacle` record and deterministic derivation:
   - `no_slot_in_window` (lab, imaging)
   - `prior_authorization_required` (imaging)
   - `not_on_formulary` (prescription; includes the plan-listed alternatives as plan facts)
   - `not_in_stock` (pharmacy)
   - `missing_supporting_document` (referral)

   Each obstacle names who can resolve it and expires when resolved, superseded or the visit ends.
5. Feed obstacles into the existing cue pipeline (`speech/service.refresh`) with source and timestamp. Use template wording such as: "Maria's plan requires prior authorization for this MRI. Can the office submit it today?" Public speech keeps every existing rule: current patient authority, every present participant's agreement, current sharing, interruption and pause.
6. Add clinician resolution actions in the clinician view, each recorded as a clinician fact from their authenticated session: "Office will submit prior authorization", "Use another window" and "I'll review coverage". A medication or test decision stays outside the product; Vene records only the clinician's administrative response. The "office will submit" response creates a prior-authorization submission errand that still needs the patient's approval.
7. Turn unresolved obstacles at visit end into follow-up dependencies on the checklist.
8. Set a latency budget and instrument it: finalized utterance → validated step → institution response → private cue. Target in fixture mode: under 3 s at p95 over 20 trials. Record live-provider timing separately.

**Reuse**

Reuse the cue, speech-agreement, interruption and pause machinery from Phase 5; the lookup fencing from Phase 6; and signed callbacks from Phase 7. Add no clinical decision-support library or drug database. The formulary is synthetic plan data.

**Tests**

- An obstacle exists only with a matching institution response reference; a model output alone creates none.
- Without standing permission, no check leaves the service; revoking permission mid-check discards the result.
- A correction ("Thursday, not Tuesday") invalidates the earlier obstacle and its cue before playback.
- Formulary alternatives appear only as plan-listed facts in the clinician or patient view. No text recommends one, and the speech path never names a medication unless the patient shared that step and every participant agreed.
- A prior-authorization callback that arrives after the visit updates the follow-up dependency once.
- The guest view contains obstacles only for shared steps whose supporting sources are also shared.
- Pause stops checks, cues and speech; a silenced voice alone does not stop checks.
- Latency instrumentation produces 20 samples and reports p95; a missed target is reported as missed.

**Local browser checkpoint**

During a real WebRTC call (fixture intelligence), have the clinician order the MRI and the non-formulary drug. Observe Maria's private cues, invite Vene to raise the MRI obstacle aloud, interrupt it once, then let the clinician choose "Office will submit prior authorization". Approve the submission and watch the delayed approval arrive. Repeat with live providers when configured.

**Exit evidence**

docs/qa/phase-10.md records obstacle traces with their institution references, cue and speech receipts, latency samples and p95, screenshots, and the open live gates.

## Phase 11 — preparation that writes itself

**Outcome:** before the visit, Maria sees "Vene found 3 things worth bringing up", each drawn from her actual history with source and age. She keeps or drops them with taps and approves once. Preparation takes seconds rather than writing.

**Build**

1. Define `MemoryPort`, with operations such as `open_loops(patient)`, `history(patient, since)` and `record_outcome(...)`, and implement it over Postgres: earlier encounters, next-visit records, non-terminal and unknown errands, pending prior authorizations and referral intakes, unanswered priorities and dated institution messages.
2. Seed a fictional history for Maria: a visit three months ago whose lab errand never completed, a referral waiting 21 days for a supporting document, and a refill that needs a new prescription. Seed variants for James and Asha.
3. Add deterministic open-loop detection rules (age thresholds, terminal-state checks and receipt status queries to the sandbox institutions). Each candidate carries its evidence references and age.
4. Optionally use the model to phrase each candidate as a question, constrained to cite the candidate's evidence (same citation validation as Phase 4). On failure, use the template wording. Never let the model add candidates.
5. Redesign preparation:
   - Drafted agenda first.
   - Keep and drop toggles.
   - Proposed audiences shown inline with sensible defaults (approved questions shared with the clinician, nothing shared with family) and one explicit approval.
   - Sources collapsed behind "Why Vene suggested this".
   - Manual questions and family suggestions still available.
6. Carry approved open loops into the visit as priorities, so Phases 9 and 10 can close them during the visit.
7. Record outcomes back through `MemoryPort` after the visit so the next preparation reflects what was resolved.

**Reuse**

Reuse ContextAdapter scoping, citation validation, next-visit preparation from Phase 7 and the existing priority model. No new memory platform; the port keeps Vene's memory replaceable.

**Tests**

- Each drafted item cites an existing source and shows its correct age; there are no candidates without sources.
- A loop resolved by a confirmed receipt is not proposed again.
- Earlier private items are proposed only to the patient; default audiences never include family; nothing is visible to the clinician before approval.
- Model phrasing that cites an unsupplied source is rejected and falls back to the template.
- A prompt-injection string inside an old institution message is treated as data.
- Preparation for a patient with no history shows an honest empty state.

**Local browser checkpoint**

Open Maria's preparation from a fresh seed and approve the drafted agenda in under five interactions. Open the clinician view to confirm only approved items appear. Complete a visit in which one loop is closed, then open the next preparation and confirm it is not proposed again. Check mobile and keyboard flow.

**Exit evidence**

docs/qa/phase-11.md records the interaction count, screenshots of before and after, scoping payload checks and test results.

## Phase 12 — phone on the table and dial-in

**Outcome:** Bring Vene works when the patient simply places a phone on the table during an in-person visit, and when a participant joins by telephone. The clinician needs no account.

**Build — 12a: one phone in the room**

1. Add an "In the room" mode to the visit, started from the patient's authenticated phone session. The patient declares who is present (for example, "Dr. Chen, my daughter"). Vene speaks a short disclosure through the phone speaker. Processing starts only after the patient records each present person's verbal agreement. The record states that it is patient-attested.
2. Publish one room microphone track from the patient's device with echo cancellation enabled. Exclude Vene's own playout windows from transcription, reusing the Phase 5 self-speech handling.
3. Enable Deepgram diarization for that track. Map labels ("Speaker 1") to declared people through a patient tap ("That's Dr. Chen"). Store mappings as `SpeakerAttribution` and allow the patient to correct them; a correction invalidates dependent interpretations as source corrections do.
4. Enforce clinician-confirmation semantics: in this mode, a clinician's spoken instruction is recorded as "said in the visit, attributed by Maria". It can create proposals and obstacles but cannot satisfy clinician confirmation. Errands that need an order still need the institution's own order receipt (the sandbox office issues it after the office-side confirmation step), so honesty does not depend on diarization.
5. Build a phone-first layout:
   - Large Pause.
   - Private cue area.
   - "Ask aloud" control.
   - Before-you-leave checklist.
   - Readable while the phone lies on a table.

**Build — 12b: telephone dial-in**

6. Add LiveKit SIP inbound with a Twilio trunk to the same room. Callers enter a one-time PIN derived from their invitation. The PIN binds the call to that membership and role, expires like invitations, and works once.
7. Speak a disclosure at join. Add DTMF controls: one key for "pause Vene", one for "resume" (patient line only), and spoken confirmation of each.
8. Telephone participants get the same consent, epoch and scope checks as browser participants. Private cues are never spoken to a telephone participant; on a patient-only phone line, the agreed spoken mode replaces cues, as the blueprint requires.

**Reuse**

Reuse the LiveKit agents worker, consent epochs, speech controller and Deepgram plugin (diarization option). For 12b, reuse the audited LiveKit SIP/Twilio examples per extension E1 of IMPLEMENTATION_PLAN.md, after a fresh license and commit check recorded in reuse-manifest.json.

**Tests**

- Original mixed synthetic audio with two generated voices: diarization labels map correctly after attestation; a remapped label invalidates dependent proposals.
- A diarized "clinician" utterance never sets clinician confirmation or order availability.
- Vene's own speech is not transcribed as a participant.
- Processing does not start before attestation of every declared person; adding a person mid-visit advances the epoch and requires attestation.
- PIN admission: wrong, expired or reused PINs are refused; caller ID is ignored; a revoked membership disconnects the caller.
- DTMF pause stops processing and speech, not just audio.
- Telephone participants never receive private cue content.

**Local browser checkpoint**

12a: run the mobile layout in a Playwright mobile context with the synthetic mixed track. Map the speakers, complete the Phase 9/10 scenario and verify the checklist. Physical-device acoustics remain an open gate unless tested on an actual phone in a real room with consenting participants.

12b: with configured test credentials and a test number, place an explicitly authorized test call into a fictional visit. Exercise the PIN, disclosure, DTMF pause and resume, and the leave/reconnect path while inspecting the browser plan. Without credentials, the gate is unverified. Never dial a clinic.

**Exit evidence**

docs/qa/phase-12.md records the attribution traces, admission tests, screenshots, and which of the physical-device and real-telephony gates were or were not exercised.

## Standard commands to add

These are requirements for this round, not commands that exist today.

```bash
./scripts/setup.sh
./scripts/dev.sh --mode fixture
./scripts/check.sh --phase 9
./scripts/check.sh --phase 10
./scripts/check.sh --all
./scripts/stop.sh
```

```powershell
.\scripts\check.ps1 -Phase 9
.\scripts\check.ps1 -All
```

`scripts/check-live.*` gains the Phase 10 obstacle-latency trials and the Phase 12 diarization gate, which are run only with explicit provider configuration.

## Original regression scenarios added

| ID | Scenario | Phases |
|---|---|---|
| S16 | Lab, imaging, referral and prescription from one visit; bundle with one rejection | 9 |
| S17 | Pharmacy times out after write; reconcile, no duplicate pickup request | 9 |
| S18 | Ride request to family; family sees only date/place; revoked family cannot answer | 9 |
| S19 | MRI requires prior authorization; raised aloud; clinician chooses "office will submit" | 10 |
| S20 | Non-formulary drug; plan alternatives shown as plan facts; no recommendation spoken | 10 |
| S21 | Correction invalidates an obstacle between generation and playback | 10 |
| S22 | Standing check permission revoked mid-lookup | 10 |
| S23 | Drafted agenda from a 21-day-old referral and a never-completed lab | 11 |
| S24 | Resolved loop is not proposed again | 11 |
| S25 | One phone, two speakers, speaker remapping invalidates proposals | 12 |
| S26 | Diarized clinician statement cannot satisfy clinician confirmation | 12 |
| S27 | Dial-in with a reused PIN; DTMF pause | 12 |

Generate original synthetic data and audio. Do not copy restricted datasets.

## Founder demonstration this enables

About three minutes, all fictional and sandbox-labelled:

1. Maria's phone: "Vene found 3 things to bring up." Two taps and an approval.
2. Phone on the table. Dr. Chen orders an MRI, a lab, a referral document and a new prescription.
3. Maria's screen shows a private cue that the MRI needs prior authorization. She taps "Ask aloud". Vene asks; Dr. Chen says the office will submit it.
4. The visit ends. Maria taps "Approve the ready steps". The checklist fills in: lab confirmed, referral intake received, prescription ready at 5 pm, prior authorization submitted, Elena driving.
5. A founder breaks something live (removes the lab slot, or makes the pharmacy time out). Vene reconciles honestly and states what is still open.

Measure and report: steps discussed versus steps moving at visit end, sandbox time to the last confirmation, obstacles raised in the room versus found afterward, cue latency p95, unsupported assertions and unwanted interruptions. These are prototype measurements, not outcome claims.

## Explicitly out of scope for this round

- Real clinic, pharmacy, plan or telephony integrations, and deployment.
- Recommending or substituting medications, tests or timing.
- Transport booking marketplaces, benefits discovery (Covered Support) and CareDays multi-visit optimization. These remain separate future candidates.
- Face or voice identity recognition.
- New memory platforms. MemoryPort keeps Vene's memory pluggable.

## Resuming this work

Read BUILD_STATUS.md first, then this plan, then IMPLEMENTATION_PLAN.md for the shared rules. Inspect the actual code and git state before assuming a task is unfinished. Start with the groundwork, then Phase 9. Record each phase's evidence in BUILD_STATUS.md using the existing format, and do not request routine approval between phases.
