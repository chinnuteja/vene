# Bring Vene — build status

Updated: 19 October 2026.

## Current state

19 October Windows follow-up: checked out `claude/venehealth-codebase-review-hop817` and re-read Phases 9–12. Migrated the existing development DB to 0014 after a local dump; all saved visit projections were unchanged. Fixed generated-contract LF/CRLF drift, saved-cluster startup, Chromium path detection, filtered SSE service updates and a reproducible stale-worker authority race (instance leases now fence late joins, heartbeats, failures and audio). 203 backend tests, contracts, TypeScript and the production build passed. The actual prompt-v5 DeepSeek gate passed five conversations/four errand kinds; original David/Zira audio passed live Deepgram diarization. The real-WebRTC/STT/model/office obstacle gate passed: one finalized-source-to-cue sample was 5,037 ms (not p95). Actual worker recovery passed three trials; repeated media tests also exposed their pre-existing assumption of an empty receipt history. Earlier full Windows browser runs had native join failures; their complete cause and a clean full-suite result remain open. Evidence and failure traces stay under ignored `.local/evidence` and `test-results`; no further narrative QA reports are planned. The next work is the single-screen demo, deadline-aware alternatives, speech speed and founder packaging/fictional hosting explicitly authorized by the latest user request.

Live verification on 15 October has passed the actual combined Deepgram -> DeepSeek -> Cartesia -> explicitly approved local sandbox reservation gate, plus Cartesia private-cue/interruption/pause safety. Four live model cases passed with prompt v4, including unrelated speech, date correction and unknown owner with known date/place retained. The latest backend regression passed 144 tests. Repeated timing is still open: the first attempt completed a short contribution before a valid interruption was measured; the retry failed native room-worker admission despite connected human browsers. No valid 20-sample live timing report exists yet. The complete deterministic regression is being repeated. See docs/qa/phase-08-live-review.md and the individual actual-output reports. Keys are in ignored `.env`; they are never copied into QA.

Phases 7 and 8 are implemented and their final local gates passed on 15 October: 133 backend tests, one actual process-log lifecycle regression, 25 browser scenarios with two explicit live/timing gates skipped, contracts, TypeScript and the optimized frontend build. Continuity, private family delivery, document review, worker/API/server recovery, three cases and populated accessibility checks are verified. Live provider quality, repeated timing, physical audio and human acceptance remain open; this is not a founder-demo or clinical-production readiness claim. The restored saved preview is running at http://127.0.0.1:3000/dev, and desktop/mobile review passed without changing saved plan/source/question data. See docs/qa/phase-07.md, phase-08.md and phase-08-final-checks.json.

Phases 1 and 2 are complete. Phase 3 is implemented and its local gates passed: 45 backend tests, 14 Chromium scenarios, contract generation, TypeScript and production build. Real local LiveKit/WebRTC verifies authorized admission, participant consent, processing pause, microphone replacement and media-server recovery. The local preview is at http://127.0.0.1:3000/dev, backed by API port 8001 and project-local Postgres 17.11 on port 5432. Live Deepgram STT remains an open credential/accuracy gate; physical microphone quality was not exercised. See docs/qa/phase-03.md for evidence and limitations.

Phase 4 is implemented and its final local gates passed on 13 October at 15:01 +05:30: 66 backend tests, all 16 Chromium scenarios, generated contracts, TypeScript and production build. The visit now has evidence-backed interpretations, answer status, evolving draft steps, source/plan corrections and filtered sharing. The default interpreter is an explicitly labelled finite fixture; real-model extraction remains an open gate because no project OpenAI key is configured. See docs/qa/phase-04.md.

Phase 5 is implemented and its final local functional checks passed on 13 October at 20:10 +05:30: 95 backend tests, 17 Chromium scenarios, generated contracts, TypeScript and production build. Private cues, agreed public speech, sourced closeout, human interruption, pause and media recovery use the same domain services in fixture and live configurations. Twenty separate real WebRTC timing trials passed: p95 startup proxy 3,127 ms (roughly 2,000 ms target missed), stop-to-silence 473 ms (500 ms target met). Live providers, physical acoustics and startup performance remain open items. See docs/qa/phase-05.md.

Phase 6 is implemented and its local sandbox gates passed on 14 October at 11:28 +05:30: 112 backend tests, 18 Chromium scenarios, generated contracts, TypeScript and a clean production build. The actual local WebRTC conversation now reaches office checks, private/spoken cues, explicit clinician/order prerequisites, separate patient approval and a persisted sandbox reservation receipt. The browser observed queued → in_flight → unknown → confirmed after an actual HTTP timeout following office commit. A final 17-test execution regression verified stable slot identity, permission concurrency and expiry fencing. Saved development data and desktop/mobile/follow-up views were checked separately. Live model/STT/TTS and physical/startup gates remain open. See docs/qa/phase-06.md.

Execution plan: IMPLEMENTATION_PLAN.md. Product design: BRING_VENE_BUILD_BLUEPRINT_2026-10-12.md. Source audit: BRING_VENE_REPO_AUDIT_2026-10-12.md.

The user authorized Codex in this chat to build using this plan. Continue without requesting routine approval between phases.

## Phase tracker

| Phase | Deliverable | Implementation | Automated tests | Local browser check |
|---|---|---|---|---|
| 1 | Reproducible app and domain foundation | Complete | 15 backend + 5 Chromium tests; contracts/type/build passed | Passed; screenshots and report saved |
| 2 | Preparation, evidence and audience controls | Complete | 33 backend + 10 Chromium total; contracts/type/build passed | Passed; multi-role payload isolation, live revocation, desktop/mobile and restart |
| 3 | Multiparty media and consent lifecycle | Implemented; local gates passed; live STT gate open | 45 backend + 14 Chromium; contracts/type/build passed | Real two-track WebRTC, consent/pause, microphone denial/replacement, server recovery; desktop/mobile inspected |
| 4 | Grounded understanding and evolving plan | Implemented; local gates passed; real-model gate open | 66 backend + 16 Chromium; contracts/type/build passed | Date/owner/source/manual corrections, unrelated-question regression, persisted scoped sharing; desktop/mobile/source inspected |
| 5 | Useful initiative and coordinated speech | Implemented; local functional gates passed; live TTS/hardware/startup target open | 95 backend + 17 Chromium; contracts/type/build passed; separate 20-trial timing gate recorded | Real two-peer speech, guest cue isolation, interruption/pause and media recovery; desktop/mobile reviewed |
| 6 | Practical checks and authorized execution | Implemented; local sandbox gates passed; live-provider gates open | 112 backend + 18 Chromium; contracts/type/build passed; final 17 execution regressions passed | Actual HTTP office, two-peer speech, missing order, expiry/delay, timeout reconciliation, family receipt and desktop/mobile inspected |
| 7 | Continuity and failure recovery | Implemented; local gates passed; inherited live gates open | 133 backend + 1 process-log regression + 25 browser total; contracts/type/build passed | Signed/duplicate replies, PDF review, actual family acknowledgement, private next visit/deletion and owned restart recovery passed |
| 8 | Founder-ready integration and packaging | Implemented; local gates passed; live/performance/hardware/human gates open | Final browser: 25 passed, 2 explicit gates skipped; dependency audits show no known vulnerabilities | Three cases, ordinary controls, keyboard/zoom/reduced motion and platform smoke passed; Windows WebKit media unavailable |
| 9 | Walk-out follow-through | Implemented; local gates passed (Linux) | 160 backend + 25 browser | Before-you-leave checklist, bundle approval, care-circle ask |
| 10 | In-room obstacle catch | Implemented; local gates passed (Linux) | 173 backend + 27 browser; 20-turn latency p95 930–938 ms | Private obstacle cues, resolver-only answers, prior-auth gating |
| 11 | Preparation drafted from open loops | Implemented; local gates passed (Linux) | 185 backend + 28 browser | Found loops, 3-interaction approval, private drafts |
| 12 | Phone on the table and dial-in | Implemented; local gates passed (Linux); telephony/diarization/acoustic gates open | 201 backend + 29 browser | 390 px phone in real local WebRTC, agreement gate, speaker naming, guest isolation, PIN issue |

Do not mark an entire phase passed when only its fixture configuration has passed and the phase requires a live gate. Independent work may continue while a specific gate remains unverified.

## Verified preparation

- [x] Read the accepted product blueprint, company context and repository audit.
- [x] Resolve and inspect current pinned LiveKit Meet package.json and LiveKit Agents pyproject.toml.
- [x] Verify Node 24.19.0, Python 3.12.14, uv 0.12.13 and bundled pnpm 11.25.0 execute locally.
- [x] Confirm bundled Playwright library is present; project test package/browser setup remains pending.
- [x] Confirm Docker CLI exists.
- [x] Attempt Docker engine connection: failed because the Docker Desktop Linux engine named pipe was absent.
- [x] Confirm psql, livekit-server and lk were not on PATH.
- [x] Write the eight-phase implementation plan with tests, source reuse and browser acceptance steps.
- [x] Preserve the 16 earlier source/license snapshots and their manifest; no third-party source has been executed.
- [x] Attempt Docker startup; its engine remained unavailable. Run verified native Postgres 17.11 instead.
- [x] Initialize the application, package manifests, lockfiles and scripts.
- [x] Verify provider configuration presence without exposing values: all four fields absent on 15 October; live gate remains open.
- [x] Run the first local application browser checkpoint using Chromium; the Codex preview request is queued.

## Next concrete work

Phases 9–12 are planned in IMPLEMENTATION_PLAN_PHASES_9-12.md (16 October): portable runtime groundwork, walk-out follow-through across several errand types, in-room obstacle catch, preparation drafted from open loops, and phone-on-the-table/dial-in participation. Groundwork passed on Linux on 16 October: setup/dev/check/stop shell scripts, a checksum-pinned Linux LiveKit release, an espeak-ng offline voice and evidence written to .local/evidence. `scripts/check.sh --all` passed with 144 backend tests and 23 browser scenarios (4 explicit gates skipped) after fixing three POSIX harness defects. macOS and a post-change Windows run are unverified. See docs/qa/groundwork-portable.md. Phase 9 is next.

Phase 9 (walk-out follow-through) is implemented and its local gates passed on 19 October on Linux. Lab, imaging, specialist-referral and pharmacy errands run through one registry and four separate sandbox institutions. The patient approves all ready steps at once, while each errand still confirms, rejects or reconciles on its own; the visit shows a live Before you leave checklist; and a scoped care-circle ask lets a family member answer for themselves. `scripts/check.sh --all`: 160 backend tests and 25 browser scenarios passed, 4 explicit gates skipped. Execution updates still use polling (moving them to SSE was deferred). The prompt v5 live-model gate and Windows/macOS re-runs are open. See docs/qa/phase-09.md. Phase 10 (in-room obstacle catch) is next.

Phase 10 is implemented and its local gates passed on 19 October on Linux. With the patient's standing read-only permission, discussed steps are checked against sandbox institutions: a fictional health plan, a pharmacy, a specialist office and imaging and lab calendars. Obstacles are derived only from institution responses and become private cues in under a second. Detected obstacles: prior authorization required, not on formulary (plan-listed alternatives shown as facts), out of stock, no availability and a missing referral packet. Only the named resolver can answer. The clinician's "the office will submit prior authorization" prepares a plan submission that the patient approves, and imaging waits for it. Latency over 20 fixture turns: p95 930–938 ms from turn to obstacle, against a 3,000 ms target. `scripts/check.sh --all`: 173 backend tests and 27 browser scenarios passed, 4 explicit gates skipped. Live-model, live-speech and Windows/macOS runs are open. See docs/qa/phase-10.md. Phase 11 (preparation drafted from open loops) is next.

Phase 11 is implemented and its local gates passed on 19 October on Linux. A MemoryPort with deterministic, source-citing rules finds unfinished steps, unanswered questions, offices still waiting and unconfirmed errands from earlier visits. Loops close on later completion, on an answer, or when the patient marks them done, and loops that share a source merge. Preparation opens with "Vene found N things worth bringing up". The patient reaches an approved list in 3 interactions. Drafts stay private until approval, with the clinician as the default audience and never family. Next visits inherit memory. `scripts/check.sh --all`: 185 backend tests and 28 browser scenarios passed, 4 explicit gates skipped, on the third full run. Earlier runs exposed two test races, both fixed, and one intermittent Phase 8 voice-recovery failure whose root cause is not established. Optional model phrasing was not implemented. See docs/qa/phase-11.md. Phase 12 (phone on the table and dial-in) is next.

Phase 12 is implemented and its local gates passed on 19 October on Linux.

- **One phone in the room.** The patient declares who is present and gives a disclosure, and records each person's agreement herself.
- **Gate.** Nothing is processed until everyone agrees. Processing, resume and room ingestion are all closed until then.
- **Voices.** Diarized voices are anonymous until the patient names them. Renaming a voice versions its sources and invalidates the interpretations that depend on them. A name is attribution only and never authority.
- **Self-speech.** When Vene hears itself, those turns are dropped.
- **New arrivals.** A new arrival pauses the call and closes the gate.
- **Dial-in.** Hashed, single-use 15-minute PINs, admitted through a token-authenticated bridge endpoint. Caller ID is never identity. Keypad: 1 agree, 2 decline, 9 pause, 0 patient-only resume. Revocation disconnects the caller.
- **Defect found and fixed.** A family suggestion was rejected with 409 by unrelated patient changes. Suggestions are now append-only and exempt from the version fence.

`scripts/check.sh --all`: 201 backend tests and 29 browser scenarios passed and 4 explicit gates were skipped, on the third full run. The earlier runs exposed that defect and two test-ordering/race problems, all fixed.

Open:
- live diarization accuracy;
- physical acoustics;
- a real SIP/telephony bridge (documented as a contract only);
- the patient-only phone spoken mode;
- Windows/macOS re-runs.

See docs/qa/phase-12.md. All planned phases 9–12 are implemented.

No planned feature phase remains unimplemented. User-authorized test keys are configured: MODEL_PROVIDER=deepseek with DEEPSEEK_API_KEY, DEEPGRAM_API_KEY, CARTESIA_API_KEY and a verified public CARTESIA_VOICE_ID in ignored .env. Continue scripts/check-live.ps1 sequentially against the isolated test database; the combined live flow and speech safety passed, repeated timing remains open. It validates configuration before reset/calls, exercises actual recognition/model/speech and separately approved sandbox booking, and repeats speech timing. Review observed outputs, attribution, citations, unsupported claims and actual receipts; never treat a fixture pass as provider quality.

Keep the earlier startup target miss open: offline p95 3,127 ms versus roughly 2,000 ms. Prior stop-to-silence was 473 ms versus 500 ms; repeat both under the current runtime and real providers. Physical acoustics, available-device qualification and patient/clinician acceptance remain separate. Integration, demo and output-review guides are under docs. Preserve the existing saved development visits and use the explicit guarded reset only for an intentional fictional demonstration.

## Known prerequisites and verification limits

- Docker engine remains unavailable; project-local official Postgres binaries satisfy the actual database gate.
- Local LiveKit 1.13.9 was installed from its pinned official Windows archive and real WebRTC tracks were verified. No project Deepgram key is configured; live STT accuracy remains an open gate.
- No real-patient, founder or healthcare-service contact is authorized by these local build phases.
- Existing research files are untracked user/task work; preserve them.
- JavaScript/Python dependencies are installed and locked. scripts/check.ps1 -Phase 2 passed, including the production build and ten browser scenarios.

## Phase 1 evidence

- Implemented apps/web, services/backend, migrations, fixtures, generated contracts, local infrastructure and launch/check/stop helpers.
- No upstream application source copied yet; LiveKit Meet's package manifest was used as a compatibility reference. Source and license details are recorded in reuse-manifest.json and THIRD_PARTY_NOTICES.md.
- Native Postgres 17.11 satisfies the database gate despite the unavailable Docker engine.
- 15 backend tests, 5 Chromium browser scenarios, contract drift check, TypeScript and production build passed.
- Actual process restart preserved saved state; runtime API proxy worked after moving the backend to port 8001.
- Desktop/mobile, source dialog and unavailable-state captures were reviewed. Normal-page captures had no console/request errors and no mobile horizontal overflow.
- Final report: docs/qa/phase-01.md. Runtime/browser evidence: docs/qa/phase-01-browser-review.json and docs/qa/phase-01-restart.json.
- Preview-open request was queued. Chromium verification and screenshot inspection were completed; the Codex browser-control kernel entrypoint was unavailable.

## Phase 2 evidence

- Implemented persistent memberships, hashed one-use invitations, HttpOnly sessions, CSRF/origin checks and gated synthetic admission.
- Added independent question approval, question/source/plan audiences, family proposal review, invitation cancellation and membership withdrawal/restoration.
- ContextAdapter, role-filtered REST/evidence/context retrieval and authenticated replacement SSE share the same permission rules. Private canary data is absent from captured guest payloads.
- 33 backend tests and 10 production Chromium scenarios passed; contracts, TypeScript and the production build passed. Final backend changes were tested again against real Postgres and the restarted API.
- The browser runner now starts its own API against bring_vene_test, so acceptance tests do not change the working preview. Final isolated run: 10 passed.
- Local browser review used the actual fictional launcher and inspected all routes, mobile and source dialog. No normal-page errors or mobile overflow.
- Actual owned API/web restart preserved session, preparation approval and version. Original approval was restored after verification.
- No new package or upstream application code copied; reuse and reference details are in THIRD_PARTY_NOTICES.md, reuse-manifest.json and docs/qa/phase-02.md.
- Evidence: docs/qa/phase-02.md, phase-02-network-review.json, phase-02-browser-review.json, phase-02-restart.json and screenshots. Preview-open request returned queued; Chromium inspection was completed.
- No Phase 2 external-provider gate is missing. Media, professional identity verification, production deployment and live providers have not been claimed complete.

## Phase evidence format

Append a section for each completed or partially completed phase:

- Date and phase.
- Implemented behavior and relevant files.
- Upstream source reused, commit/license and adaptations.
- Exact checks run, configuration and results.
- Local URL and browser scenarios actually exercised.
- Screenshot/report paths.
- Missing live/hardware checks or unresolved defects.
- Next concrete task.

Keep summaries concise and factual. A missing credential or browser capability is an unverified check, not a passing result.

## Phase 5 evidence

- Final scripts/check.ps1 -Phase 5 passed at 20:10 +05:30: 95 backend tests, contracts, TypeScript, production build and 17 Chromium scenarios. The dedicated measurement case was intentionally skipped in that suite.
- scripts/check-speech.ps1 -Measure passed with twenty real local WebRTC trials. Startup proxy p95 3,127 ms missed the roughly 2,000 ms target; stop-to-silence p95 473 ms met 500 ms. Recognition delay remains unmeasured.
- Guest APIs/DOM exclude private cues. Public speech requires current patient authority, every present participant's agreement and current sharing. Corrections, answered questions, expiry, mode/permission changes and pause fence pending speech. Interrupted receipts do not retain a full delivered transcript; hearing remains unconfirmed.
- Implemented authenticated signal-time microphone verification, preservation of existing human rooms through assistant connection failures, commit notifications, first-frame and pre-generation scope checks, detector reset, bounded queues and owned in-memory offline voice reuse.
- Read-only/diagnostic transactions avoid synchronous disk flushes; durable permission, transcript, stop-acknowledgment and final playout writes remain unchanged. Recent diagnostic counters may be lost on a hard crash.
- Final owned-preview restart preserved saved visit data. Actual desktop/mobile review passed without errors or horizontal overflow; screenshots inspected.
- Evidence: docs/qa/phase-05.md, phase-05-browser-report.json, phase-05-latency.json, phase-05-provider-gates.json, phase-05-preview-review.json and screenshots. Failed/incomplete timing evidence is retained separately.
- Reuse/license records are updated. No new upstream application source copied. Live STT/model/TTS, physical acoustics and the startup target remain open; Phases 6–8 remain unstarted.




