# Bring Vene — technical implementation plan

Created: 12 October 2026. Execution owner: Codex in this chat.

This is the implementation runbook for the accepted Bring Vene product. Read BUILD_STATUS.md for actual progress. This plan describes work to do; unchecked tests and browser checks are not completed work.

Product background: BRING_VENE_BUILD_BLUEPRINT_2026-10-12.md. Source diligence: BRING_VENE_REPO_AUDIT_2026-10-12.md. Company boundaries: VENE_COMPANY_CONTEXT.md.

## Delivery target and execution rules

Deliver a locally runnable product in which a patient prepares an approved agenda, invites Vene into a conversation, receives useful contextual support, resolves a practical obstacle and authorizes follow-through. The plan must remain correct when a participant changes an important detail.

Eight phases produce the flagship browser experience. Telephone, shared-microphone and existing-meeting-platform adapters follow the flagship; their extension gates are specified at the end.

For each phase, Codex will implement, run the relevant automated tests, start the local application, inspect it in a browser, repair observed defects and write the evidence into BUILD_STATUS.md. Routine phase transitions do not need another user approval. If a provider credential or external dependency is missing, record the exact unverified gate, continue independent work and do not mislabel a simulation as a live integration.

Do not stop at a polished storyboard. The first complete demonstration requires real multi-participant media, model-backed behavior, durable visit state and executable sandbox errands. The sandbox represents the unavailable Vene/provider integration, not fake internal state.

No deployment, founder contact, real-patient data or real healthcare outreach is part of these phases.

## Technical decisions

| Area | Decision |
|---|---|
| Frontend | Next.js, React, TypeScript; LiveKit React components; a custom, accessible patient interface |
| Application API | Python 3.12, FastAPI, Pydantic; one source of truth for domain rules |
| Persistence | PostgreSQL 17 with SQLAlchemy and Alembic; pinned supported patch/container digest during setup |
| Voice worker | LiveKit Agents Python with per-participant input and one coordinated public output |
| Voice services | Replaceable STT/TTS adapters; initial live choices Deepgram and Cartesia, matching Vene's disclosures |
| Model access | Provider adapter with structured outputs; select one available supported model during live setup and record its exact model ID |
| Jobs | Postgres outbox and a bounded worker; no separate workflow platform initially |
| UI updates | Authenticated server-sent events plus REST commands; WebRTC handles media separately |
| API contract | FastAPI OpenAPI export and generated TypeScript client/types; validate model output server-side |
| Tests | pytest/pytest-asyncio and API tests; Vitest where UI logic warrants it; Playwright for complete browser flows |
| Local operations | Repository-owned PowerShell/Node launchers, explicit ports, retained logs with redaction, health checks and owned-process cleanup |

Next.js serves the frontend and same-origin API proxy. It does not duplicate the Python authorization or plan rules. The worker calls internal authenticated endpoints or shared application services, never browser-controlled privileged commands.

Prefer existing packages as dependencies. Copy small, audited source files only where ownership of the implementation materially helps. Do not fork an entire framework to customize one example.

### Two provider configurations, one product

**Fixture configuration:** deterministic model/STT/TTS/test-service adapters with original synthetic fixtures. It runs without paid model credentials. Every fixture enters the same application services, authorization checks, event store and action pipeline as live inputs. The developer view labels fixture mode. This supports repeatable tests and development.

**Live configuration:** real WebRTC, real STT/model/TTS providers and the same encounter and sandbox-execution services. Live mode must fail visibly when its provider is unavailable. Never silently replace a failed live model with scripted answers.

Media can also be tested with real WebRTC and prerecorded synthetic audio while intelligence remains deterministic. Label that combination precisely: it proves the media path, not model understanding.

### Workspace layout to create

```text
apps/
  web/
    src/app/                         preparation, encounter and follow-up routes
    src/components/                  patient UI and media controls
    src/lib/api/                     generated client and filtered-view hooks
services/
  backend/
    src/bring_vene/
      api/                           commands, views, SSE and admission
      domain/                        evidence, priorities, plans and permissions
      persistence/                   SQLAlchemy repositories and migrations
      intelligence/                  context, extraction and participation
      adapters/                      model, memory, executor and notification ports
      workers/                       practical checks and action outbox
    tests/
  voice/
    src/bring_vene_voice/             track supervisor and speaking controller
    tests/
  sandbox/
    src/bring_vene_sandbox/           scheduler and office-response simulator
    tests/
packages/contracts/                  exported schemas and generated TS types
fixtures/                            fictional patients and original scenarios
tests/e2e/                           multi-context browser tests
tests/media/                         original synthetic audio scenarios
scripts/                             setup, dev, checks and teardown
infra/                               local Compose and LiveKit configuration
docs/qa/                             phase reports and selected screenshots
third_party/                         retained license/notice files
THIRD_PARTY_NOTICES.md
reuse-manifest.json
IMPLEMENTATION_PLAN.md
BUILD_STATUS.md
```

Use one Python workspace with a single resolved uv lock where package compatibility permits; keep core backend tests independent of native voice dependencies. Pin JavaScript dependencies in pnpm-lock.yaml. Do not create a second parallel app under a disposable demo folder.

## Environment preflight already performed

Verified locally on 12 October:

- Bundled Node 24.19.0 and Python 3.12.14 run.
- uv 0.12.13 and bundled pnpm 11.25.0 run.
- Docker CLI is installed, but the Docker Desktop Linux engine was not reachable.
- No psql, LiveKit server or LiveKit CLI was found on PATH.
- The bundled Playwright library exists; the project still needs its own test dependencies and a verified browser installation.
- There is no application code or package manifest yet.
- Provider credentials and service access have not been checked.

Phase 1 includes starting the existing local Docker installation if available and confirming the intended local context. Never stop unrelated containers or processes. If Docker cannot run, use pinned official project-local Postgres binaries on Windows, then exercise the same real Postgres gates. If neither database mode can run, those gates remain unverified. Do not substitute SQLite and declare Postgres concurrency tests passed. During implementation, Docker was unavailable and the official EDB Postgres 17.11 archive was pinned by URL and SHA-256 in infra/postgres-binary.json.

The current official LiveKit Meet manifest supplies a compatibility reference, not a requirement to copy every dependency. Exclude its analytics, optional commercial audio filters and unused features. Resolve currently compatible package versions and security fixes during setup, then freeze them in the lockfiles.

## Source reuse policy and map

For every copied file, record repository, commit, upstream path, local path, license and our changes in reuse-manifest.json. Retain the applicable license and NOTICE material, mark modifications and audit dependencies introduced by the copy. A README badge is not the licensing authority.

| Key | Audited source | Reuse |
|---|---|---|
| LK | livekit/agents at b58e83f5c77d5b4bd4c8586793885151a91c4c83, Apache-2.0 | SDK dependency; adapt multi-user-transcriber.py lifecycle pattern; inspect room I/O behavior |
| MEET | livekit-examples/meet at 13e4fd88d6f3c238060746a8f476e32af5c97fbf, Apache-2.0 | Selected pre-join, device and room component patterns from PageClientImpl.tsx |
| UI | livekit-examples/agent-starter-react at c5d78a6c381a0ac80b081cf6aeb8ac454d00ca78, MIT | Selected session-provider and audio/control components |
| PIPE | pipecat-ai/pipecat at 19fca83d2e2336b7c82145fe66b7b1cc76e44ac9, BSD-2-Clause | Turn timing reference; port a bounded algorithm only if it solves an observed problem |
| VEXA | Vexa-ai/vexa at f1a62fbbdfd2c98cb162582d82c31fe8102acc89, Apache-2.0 | Optional later meeting-platform adapter; not on the flagship path |

Snapshots already exist in research/bring-vene-sources with hashes. They are not imports or installed application dependencies.

Do not copy the example unauthenticated room/token endpoints, transcript logging, default public agent endpoint, broad transcript broadcast or unsafe participant-startup lifecycle unchanged. Those are the specific gaps our implementation must close.

No new repository is required for every phase. For preparation, plan semantics, authorization and administrative execution, small application code against stable libraries is more reusable than importing an unrelated healthcare app. TEN has additional license conditions; PRESENT lacks a verified root reuse license; MP-Bench has noncommercial/evaluation-only restrictions. They are not approved source dependencies.

## Core contracts and invariants

Define these before model integration:

- Encounter: ID, processing state, event sequence, participant membership, consent epoch and transcript gaps.
- Participant: server-issued ID, invited role, verification method and encounter scope. A voice cluster is not verified identity.
- Evidence: source ID/type, exact reference, observed/authored time, revision and audience restrictions.
- Priority: patient approval, desired resolution and discussion status.
- Plan item: kind, owner, timeframe, version, evidence references, human confirmation and required dependencies.
- Authorization: exact action/scope, request digest, dependency versions, audience, expiry and revocation.
- Action: request, authorization reference, idempotency key, execution attempts and external receipt.

Preserve orthogonal states: discussed, patient-understood, clinician-confirmed, order-available, patient-authorized and externally-completed mean different things.

Each accepted command includes an idempotency key and, where appropriate, expected entity version. Store accepted events and updated projections in a transaction. Add a unique encounter/event sequence constraint. Use optimistic concurrency for conflicting edits.

A model returns proposals with evidence references and intended audience. Application services validate them. No model response can grant permissions or directly mark an external task complete.

An audience or consent change advances an epoch. Generation, playback, view publication and action dispatch check that epoch again at use time. Already delivered information cannot be recalled, but further use can be stopped and cached UI state cleared.

An action's authorization binds its material parameters and dependencies. An accepted correction invalidates any pending action built on old values. A correction to an already executed action requires an explicit new corrective task.

## Phase 1 — reproducible application and domain foundation

**Outcome:** a locally running, persistent application shell with the three visit-card areas and real backend health.

**Build**

1. Create the workspace, lockfiles, environment example, ignore rules and third-party records.
2. Write scripts/setup.ps1, scripts/dev.ps1, scripts/check.ps1 and scripts/stop.ps1. Launch only owned processes; use hidden windows if Start-Process is needed. Persist owned PIDs and actual selected ports in ignored .local state.
3. Configure Postgres, backend health/readiness, migrations and fictional seed data. Use a test database distinct from the development database.
4. Implement the core IDs, event envelope, evidence references and version checking. Use an injected clock in tests.
5. Build a coherent responsive shell: preparation, visit and follow-up routes; readable typography, status language and loading/error states.
6. Establish generated API types and a repeatable contract-drift check.

**Reuse**

Use MEET's compatible React/LiveKit dependency set as a reference and its basic room layout conventions later. Retain only relevant dependencies. Use standard FastAPI, SQLAlchemy, Alembic and generated-client tooling; no copied patient-product backend.

**Tests**

- A migration applies to an empty Postgres database; seeded encounter survives API restart.
- Invalid event shapes and conflicting expected versions are rejected without partial writes.
- Duplicate command ID produces one accepted change.
- Health distinguishes running API from unavailable database.
- Generated client matches exported OpenAPI.
- Production frontend build and type checks pass.

**Local browser checkpoint**

Run the launcher, confirm a successful HTTP response and open its printed frontend URL. Visit preparation, visit and follow-up pages; refresh each directly. Inspect the mobile and desktop layouts, keyboard focus, loading and backend-unavailable state. Check console and network failures.

**Exit evidence**

Working URL, runtime versions, migration/test/build results and representative desktop/mobile screenshots in docs/qa/phase-01.md. Postgres readiness is required for phase completion.

## Phase 2 — preparation, evidence and audience controls

**Outcome:** Maria can approve what matters today and precisely control what can be shared.

**Build**

1. Implement server-issued, short-lived invitation redemption and HttpOnly session cookies. Invitations map to existing server-side memberships; role cannot come from a URL parameter.
2. Add a local-only synthetic fixture launcher for isolated patient, clinician and family sessions. It is excluded from non-development operation.
3. Build ContextAdapter over fixture records and the authorized evidence store. Keep private and shared model contexts separate from the beginning.
4. Build priority selection, source drawer, family suggestions and approval/edit/revocation.
5. Implement filtered view endpoints and authenticated SSE snapshot/delta delivery. Same-origin API access avoids duplicating session logic in the browser.
6. Add a canary private fact in synthetic fixtures to make leakage observable in tests.

**Reuse**

Reuse UI primitives and applicable accessibility behavior from the selected LiveKit frontend dependency stack. Use generated clients rather than hand-writing every request. Do not import an unrelated memory graph; the ContextAdapter preserves future Zep/Vene integration.

**Tests**

- Clinician/family cannot obtain the canary via REST, SSE, evidence lookup or guessed IDs.
- URL/metadata role spoofing cannot expand privileges.
- Expired, replayed and revoked invitations fail correctly.
- Family suggestions remain unapproved until patient acceptance.
- Revocation removes future private payloads and invalidates stale view subscriptions.
- Quoted instructions inside a document cannot modify application permissions.
- Preparation survives refresh and server restart.

**Local browser checkpoint**

Use separate authenticated browser contexts for patient, clinician and family. In the patient context, approve two priorities, reject a family suggestion and keep a fact private. Inspect the other views, then change scope and confirm their state updates. Try an expired invite and direct evidence URL. Check the actual response bodies in automated browser tests, not only whether a card is visually hidden.

**Exit evidence**

Multi-role browser scenario passes. Patient can explain the meaning of each sharing control from its label. No unauthorized canary appears in captured synthetic-test network payloads.

## Phase 3 — real multiparty media and consent lifecycle

**Outcome:** two humans and a disclosed Vene participant can share a browser conversation, with attributable input and genuine processing pause.

**Build**

1. Run local LiveKit or use a configured development project; keep the application itself local. Record which was tested.
2. Implement backend room admission and short-lived tokens bound to encounter membership. Do not copy the public example token route.
3. Adapt LK's multiparty transcriber pattern into a track supervisor keyed by participant and track epoch. Handle join, leave during startup, duplicate events, reconnect and cleanup.
4. Add the MEET pre-join/device UI and a visible Vene participant. Disable recording/egress and pre-connect audio buffering until processing consent is active.
5. Collect explicit per-participant agreement before STT/model processing begins. A new participant pauses processing until admitted/agreed. Refusal leaves human conversation possible.
6. Implement separate microphone mute, silence-Vene-output and pause-processing controls.
7. Add a real STT adapter and an original synthetic-audio input path for repeatable browser tests. Disable automatic shared transcript publication and ordinary transcript logging.

**Reuse**

Adapt research/bring-vene-sources/livekit/multi-user-transcriber.py, retaining attribution and fixing the audited lifecycle issues. Borrow selected MEET room/device patterns and UI audio provider. Depend on the LiveKit SDK for transport, not a homemade WebRTC stack.

**Tests**

- Two real WebRTC participant tracks retain distinct source IDs.
- Leaving before transcription startup completes leaves no orphan session.
- Reconnect creates a new track epoch; overlapping speech is not falsely serialized.
- No audio goes to STT/model before consent or while processing is paused.
- Late callbacks from a previous consent epoch cannot write transcript state.
- Microphone denial, disconnected device and server loss produce recoverable states.
- Repeated join/leave cycles do not grow the count of active worker tasks.
- Synthetic audio through real WebRTC is tested separately from real-provider STT accuracy.

**Local browser checkpoint**

Join as patient and clinician in isolated browser contexts. Accept/decline consent, inspect device selection, speak or inject original synthetic WAV input, disconnect one participant and rejoin. Confirm pause stops processing while the human call remains available. Test a late arrival and microphone-denied browser context.

For physical microphone quality, document whether a real hardware session was actually exercised. Browser audio fixtures prove transport behavior but do not establish real-room acoustic performance.

**Exit evidence**

Real-media test passes and the consent lifecycle is verified. If live STT credentials are unavailable, retain that explicit open gate; other phases may progress against deterministic transcript inputs.

## Phase 4 — grounded understanding and the evolving visit plan

**Outcome:** the visit card responds to what was said, cites evidence and handles corrections.

**Build**

1. Add the model gateway, timeout/cancellation handling, structured proposal schemas and an exact provider/model configuration record.
2. On finalized utterances, update bounded context and run extraction/priority interpretation outside the audio loop. Partial transcripts may be shown as provisional text but cannot authorize actions.
3. Extract proposed owner, timing, location, dependencies and priority-answer status with supporting evidence references.
4. Validate source references, versions and audience before accepting any proposal.
5. Apply accepted changes transactionally and stream small filtered deltas to the visit card.
6. Handle “actually…”, changed dates/locations, ambiguous owners, explicit deferral and changed source transcripts. Do not automatically call every mention an answer.
7. Expose a concise source explanation and manual correction controls.

**Reuse**

Use Pydantic schemas and the existing event/view services from earlier phases. Use LiveKit's current testing facilities for conversational behavior where useful. No patient-advocate repository provides this exact domain model; copying a generic clinical reconciliation rule would create incorrect assumptions.

**Tests**

- Exact synthetic cases cover explicit answer, partial answer, deferral, unrelated mention and contradiction.
- A superseded transcript cannot remain the sole active evidence for a plan item.
- Out-of-order model completions cannot overwrite a newer correction.
- Invalid/missing citations produce a draft requiring clarification, not an authoritative fact.
- Quoted prompt injection does not expand access or trigger tools.
- Model failure leaves the conversation and current plan usable.
- Deterministic provider tests are separate from real-model behavior runs; model-backed checks are not called deterministic.

**Local browser checkpoint**

Run a conversation, watch the three visit-card areas update and inspect sources. Introduce “Tuesday, not Thursday,” then an ambiguous “they'll do it.” Confirm the first becomes a sourced correction and the second remains unresolved. Refresh a second participant's view to verify persisted, audience-correct state.

**Exit evidence**

The original scenarios produce expected structured outcomes and at least one real-model conversation demonstrates extraction from free-form input. Screenshots alone are insufficient.

## Phase 5 — useful initiative and coordinated speech

**Outcome:** Vene can support the conversation with appropriate private suggestions and short public contributions.

**Build**

1. Implement explicit help, patient-private cues and agreed closeout modes.
2. Separate candidate generation from floor control. Rank candidates by patient priority, relevance, unresolved status, authority fit and freshness.
3. Maintain a bounded candidate queue with expiry, deduplication, cooldown and version/permission checks.
4. Add the single public TTS output path. All allowed human speech can interrupt it; explicit pause cancels generation and queued playback immediately.
5. Suppress replies to questions addressed to another participant. Invalidate a cue when the humans answer it themselves.
6. Exclude Vene's own output from human-input processing and track only actually played output as heard.
7. Keep private audio out of the initial shared room; private cues use the authenticated patient UI.

**Reuse**

Use LK speech handles, interruption hooks and TTS integrations. Reuse UI voice state/media controls where suitable. Consult PIPE's explicit turn-delay pattern if a measured afterthought problem warrants it; do not import its whole pipeline or wake-phrase behavior that discards listening context.

**Tests**

- Silent turns, direct invitation, invitation to another human, agreed closeout and topic changes.
- A stale cue is never spoken after its underlying question is answered.
- A role/scope change between generation and playback cancels the utterance.
- Human interruption stops playback and does not save unplayed words as delivered.
- Vene does not trigger itself from its own audio.
- A slow tool/model does not block pause or human speech.
- Long pauses, false starts and overlap are covered by synthetic audio plus targeted live testing.

**Local browser checkpoint**

Use the private patient panel to approve a suggestion, hear it publicly, interrupt it, then continue the conversation. Switch modes, pause processing and resume explicitly. Confirm other participants do not receive the private suggestion payload. Exercise a long natural pause and a question addressed to Maria.

**Exit evidence**

Record end-of-speech-to-first-audio and stop-detection-to-silence distributions for the exercised scenarios, including recognition delay separately. Initial targets: roughly two seconds and half a second respectively at p95 under stated conditions. Report actual sample counts and results; do not manufacture a percentile from a handful of trials or call it a clinical standard.

## Phase 6 — live practical checks and authorized execution

**Outcome:** Vene finds a logistical obstacle during the conversation and completes the resulting approved sandbox work.

**Build**

1. Build an independent sandbox scheduler/office service with real persisted availability, order prerequisites, request IDs and receipts.
2. Add controllable failure modes: no suitable slot, expired availability, delayed response, rejection, duplicate callback and ambiguous timeout after a successful write.
3. Implement typed prerequisite checks and administrative action proposals. Existing permission may authorize a lookup; booking/messaging needs its own appropriate scope.
4. Feed current lookup results into the private cue/closeout pipeline with source and timestamp.
5. Bind approval to the action digest and relevant plan/evidence versions.
6. Commit authorization, action state and outbox entry together. Dispatch in a worker with leases and idempotency.
7. Reconcile ambiguous results before retrying a write. Record pending, rejected, confirmed and unknown states accurately.
8. Provide a development-only scenario panel to change scheduler availability mid-conversation. It must be visibly a sandbox.

**Reuse**

Reuse our adapters, SQLAlchemy transactions, Postgres uniqueness and ordinary HTTP tooling. Use external sandbox responses to exercise the same interface future Vene execution will use. Do not import a framework merely for queueing or claim a fabricated FHIR object is a sent request.

**Tests**

- A lookup outside scope is denied before data leaves the service.
- A booked slot has an actual sandbox receipt; a suggested slot does not.
- A correction during a lookup invalidates its stale response/action.
- Two concurrent approval/dispatch attempts produce one reservation.
- A missing required order prevents dispatch and records the dependency.
- Timeout after successful booking is reconciled without creating a second booking.
- Revocation wins over queued but not-yet-dispatched work.
- A completed external action is never “undone” merely by changing our local event history.

**Local browser checkpoint**

During the call, change sandbox availability so the requested window has no slot. Observe the private cue, invite Vene to ask, provide a correction, approve the resulting action and inspect its receipt. Repeat with a missing order and a timeout-after-write. Confirm the patient and family see honest statuses.

**Exit evidence**

This phase delivers the first complete flagship loop. Real media/model behavior and sandbox execution must all be distinguished and verified.

## Phase 7 — after-visit continuity and failure recovery

**Outcome:** follow-through survives restarts, late office replies and scoped family communication.

**Build**

1. Add authenticated office-result callbacks, correlation and idempotent ingestion.
2. Generate family updates from approved data fields and completed/open tasks; use a local delivery outbox with acknowledged sandbox delivery.
3. Add after-visit document ingestion for synthetic text and machine-readable PDF first. Retain source provenance; scanned OCR is later scope unless needed for the demo.
4. Compare document statements with conversation-derived drafts. Surface discrepancies to the responsible human; never choose clinical correctness automatically.
5. Build next-visit preparation from resolved/open work without sharing earlier private information outside new scope.
6. Add restart/reconnect recovery, event replay, worker leases, retention/deletion behavior and derived-cache invalidation.
7. Add structured operational traces containing identifiers/timings, not raw sensitive content. Keep synthetic QA captures separate from real-use settings.

**Reuse**

Reuse the existing event/outbox architecture and a maintained PDF text parser after a package/license check. Keep ContextAdapter compatible with future Vene/Zep access; no replacement memory platform is needed. Standard job patterns remove the need for a large recovery framework.

**Tests**

- Duplicate/late callbacks attach to the correct action and do not spawn new work.
- Forged or replayed callback authentication fails.
- Worker crash after external success recovers by reconciliation.
- Family output is generated only from permitted fields, not redacted after unrestricted generation.
- Conflicting after-visit instructions remain unresolved and do not trigger medication changes.
- Explicit encounter deletion purges its application content and derived caches; audit entries retain only permitted minimal metadata. Document backups/log retention separately rather than promise instantaneous total erasure.
- Reconnect restores current filtered state and visibly marks transcript gaps.

**Local browser checkpoint**

Stop and restart the owned backend/worker, refresh all role views and confirm the plan survives. Submit an office response from the sandbox, then duplicate it. Upload a conflicting synthetic document. Open the family update and next-visit preparation. Test revocation and deletion in a disposable synthetic encounter.

**Exit evidence**

State and action correctness survive the specified failures. Family and follow-up surfaces pass independent browser-context checks.

## Phase 8 — founder-ready integration, accessibility and packaging

**Outcome:** one coherent, locally reproducible experience that can withstand unscripted changes.

**Build**

1. Refine the complete flow: preparation, guest admission, live visit, short closeout, action approval and follow-up.
2. Ensure plain labels, readable text, visible focus, keyboard operation, responsive layouts, useful empty/error states and reduced-motion behavior.
3. Add a one-command reset/seed for the synthetic demonstration; keep debug controls out of the ordinary patient/clinician UI.
4. Add deployment-neutral configuration examples, adapter documentation and a concise explanation of real versus simulated integrations.
5. Freeze compatible dependencies, verify notices, run relevant dependency advisories and document material unresolved issues.
6. Prepare the demonstration script and an unprompted-change checklist. Do not record an artificial perfect run and call it an unscripted test.

**Reuse**

Continue using maintained UI/media components. Use Playwright's multi-context facilities and accessibility checks instead of building a custom browser test framework. Reuse LiveKit's agent test utilities where they fit. No new product framework is needed.

**Tests**

- Full deterministic regression suite, contract checks and production build.
- Full browser flow in Chromium; targeted microphone/room/form smoke checks in available Firefox/WebKit. Record any platform not exercised.
- Two-role and family-role network isolation through the complete flow.
- At least three distinct synthetic encounters, including the difficult correction/failure scenarios, with variations not used to tune the exact demonstration.
- A configured real-provider end-to-end run, with observed outputs reviewed.
- Measured latency, unwanted interruptions, unanswered priorities, unsupported assertions and action completion.
- Human evaluation remains a separate future step; Codex review or a model judge is not a substitute for patient/clinician acceptance.

**Local browser checkpoint**

Start from a fresh synthetic seed. Run the entire founder demonstration using separate browser contexts, then repeat with a different date/location and an unexpected blocked dependency. Inspect desktop/mobile, 200% zoom, keyboard flow, error recovery, console and failed requests. Confirm the normal interface contains no implementation jargon or hidden reliance on the scenario panel.

**Exit evidence**

docs/qa/phase-08.md includes environment/model versions, commands, screenshots, complete-path outcomes, limitations and remaining gates. The product is “founder-demo ready” only when real media/intelligence and the explicit sandbox work together. It is not automatically “ready for clinical production.”

## Standard commands to implement in Phase 1

These are the required developer interface, not commands that already exist today.

```powershell
.\scripts\setup.ps1
.\scripts\dev.ps1 -Mode fixture
.\scripts\dev.ps1 -Mode live
.\scripts\check.ps1 -Phase 1
.\scripts\check.ps1 -Phase 6
.\scripts\check.ps1 -All
.\scripts\stop.ps1
```

The check script maps phase numbers to targeted suites and prerequisites, runs tests without swallowing nonzero exit codes and writes a summary. Live/provider tests use explicit configuration and are never silently skipped as “passed.” Missing live credentials should mark that part unverified, while deterministic tests still run.

The launcher prints the actual local frontend URL and service status. Default ports: web 3000, backend 8000, sandbox 8010, Postgres 5432, LiveKit signaling 7880; transport ports are set by its tested local configuration. If a port belongs to an unrelated process, choose a new port and update generated local config. Never kill an unknown process to obtain a default port.

## Browser verification protocol for every phase

1. Start/reuse the owned local server and wait for health/readiness.
2. Open the successfully served Local URL in the Codex browser/available supported browser surface.
3. Run the phase's normal path and its meaningful failure paths.
4. Use Playwright isolated contexts for different identities. A new tab alone is not identity isolation.
5. Inspect visible layout, focus/keyboard behavior, refresh/deep links, console errors and request failures.
6. For access-control tests, assert on actual API/SSE payloads and server access checks, not screenshots alone.
7. Save only the screenshots/traces that establish the checkpoint. Tests use synthetic data; authentication state and secrets stay ignored.
8. Fix failures before marking the phase passed. If a browser capability is unavailable, record that limit rather than substitute a successful HTTP request for visual inspection.

Automated tests should check user outcomes and important invariants. Do not add broad snapshot tests for incidental markup, or tests that merely repeat an implementation function. Once relevant checks pass, proceed unless a new change or unresolved concern justifies repeating them.

## Original regression scenarios

| ID | Scenario | Primary phases |
|---|---|---|
| S01 | Approved agenda with private canary and unapproved family suggestion | 2, 4 |
| S02 | Two speakers, overlapping speech and leave during startup | 3 |
| S03 | Question addressed to patient; Vene stays silent | 5 |
| S04 | Relevant fact recalled with source and date | 4, 5 |
| S05 | “Tuesday, not Thursday” correction with stale model output arriving later | 4, 6 |
| S06 | No slot in requested window; human clarifies next action | 5, 6 |
| S07 | Order missing; action remains blocked without clinical invention | 6 |
| S08 | Private sharing revoked between generation and playback | 2, 5 |
| S09 | Timeout after booking succeeded; reconcile before retry | 6, 7 |
| S10 | Duplicate office callback after worker restart | 7 |
| S11 | Conflicting after-visit document; unresolved difference remains visible | 7 |
| S12 | Prompt injection in a retrieved document or participant utterance | 2, 4, 6 |
| S13 | New participant arrives or consent is withdrawn mid-call | 3, 5 |
| S14 | Late family member receives only the approved update | 2, 7 |
| S15 | Provider failure with clear degraded state and no scripted-live substitution | 3–8 |

Generate original synthetic data. Do not copy restricted benchmark datasets into this commercial-facing project.

## Extensions after the flagship

These are recorded future work, not requirements to label Phase 8 complete.

**E1 — telephone participation.** Reuse LiveKit SIP/Twilio examples and the same encounter service. Add caller admission, explicit role confirmation, spoken disclosure and a phone-appropriate pause/resume control. Test real browser+SIP participants, reconnect, DTMF and consent; inspect the local browser plan while an explicitly authorized test call runs. Real telephony is unverified until credentials, test numbers and a real call are available. Do not dial a clinic as a test.

**E2 — one phone in the room.** Add a shared-microphone adapter, echo handling and uncertain speaker clusters. Test original mixed audio plus actual device conditions; inspect the local mobile UI and confirm unknown speakers never gain clinical authority from diarization. No face recognition or identity inference is required.

**E3 — existing meeting platforms.** Reassess Vexa's current API and license at implementation time. Prove joining, spoken output, stopping and privacy behavior in an authorized test meeting while inspecting the local plan. Its presently unwired speaking API is not assumed fixed. No calendar integration or automated meeting joining is enabled by this plan.

## Resuming this work in Codex

Read BUILD_STATUS.md first, then this plan and any applicable AGENTS.md. Inspect the actual code and git diff before assuming a task is unfinished. Continue the next unchecked task; preserve existing user work. Update the status with tests actually run and browser evidence actually observed.

A phase report records: changes, reused source, commands/results, browser scenarios, relevant screenshots, real/fixture/provider configuration, unresolved defects and the next task. No automatic “approved” transition and no routine permission request between phases.

## Primary technical references

- [Audited LiveKit Meet dependency manifest](https://github.com/livekit-examples/meet/blob/13e4fd88d6f3c238060746a8f476e32af5c97fbf/package.json)
- [Audited LiveKit Agents Python manifest](https://github.com/livekit/agents/blob/b58e83f5c77d5b4bd4c8586793885151a91c4c83/livekit-agents/pyproject.toml)
- [LiveKit agent testing](https://docs.livekit.io/testing/unit-tests/)
- [Playwright role-isolated browser contexts](https://playwright.dev/docs/auth)
- [FastAPI WebSocket test patterns](https://fastapi.tiangolo.com/advanced/testing-websockets/) — useful if an internal control stream later uses WebSockets; UI updates are SSE in this plan.
- [PostgreSQL supported-version policy](https://www.postgresql.org/support/versioning/)

