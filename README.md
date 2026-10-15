# Bring Vene

A locally developed patient-controlled visit companion. Phases 1–2 provide persistent preparation, invitations, separate patient/clinician/family views, scoped evidence and live sharing updates. Phase 3 adds real local WebRTC calls, a visible Vene participant, explicit processing consent and genuine pause/resume. Phase 4 adds cited understanding, question-answer status, evolving proposed next steps and corrections that invalidate stale interpretations. Phase 5 adds patient-private cues, separately agreed public speech, interruption and sourced closeout.

## Run on this Windows workspace

```powershell
.\scripts\setup.ps1
.\scripts\dev.ps1 -Mode fixture
```

Open the Local URL printed by the launcher. Start the fictional preview at http://127.0.0.1:3000/dev. Choose Maria, Dr. Chen or Elena. Use separate browser profiles to see all three together. Opening /prepare without a session shows an invitation gate.

Setup uses Docker Postgres if reachable, otherwise the pinned official Postgres 17.11 Windows binaries under ignored .local. It creates separate development and test databases, applies migrations and seeds Maria's fictional visit. Re-running setup preserves edits.

To stop the owned app processes:

```powershell
.\scripts\stop.ps1
# Also stop the project's database:
.\scripts\stop.ps1 -Infrastructure
```

## Check the implemented phases

The local database must be running. Use the preview launcher for visual review. Setup verifies the Chromium test browser and installs it if necessary.

```powershell
.\scripts\check.ps1 -Phase 5
```

The tests exercise a real isolated Postgres database. The check runs backend tests, contract comparison, TypeScript checks, a production build and Chromium interactions against isolated local frontend, API, LiveKit, voice and understanding-worker processes backed by bring_vene_test. Browser tests preserve the working preview database. They use generated tone WAVs through actual WebRTC; this verifies transport and consent behavior, not STT accuracy or hardware acoustics. Phase 4's default tests use original finite scenarios, not a live language model. Run backend, browser and model checks sequentially because they share the isolated test database. Browser screenshots and review evidence are under docs/qa.

Development, production preview and verification builds use different output directories so checks can run while the preview stays open.

After the Phase 5 check, run `scripts/check-speech.ps1 -Measure` sequentially for twenty controlled WebRTC speech trials. It uses a 0.2-second repeat-trial cooldown (the product default stays ten seconds), saves individual samples and nearest-rank p95 values under docs/qa/phase-05-latency.json, and keeps recognition delay explicitly unmeasured. Local audio decoding does not establish physical hearing or live provider latency.

With project Cartesia key and voice configuration, `scripts/check-speech.ps1 -LiveTts` exercises the same authorized speech and interruption services using live TTS and original synthetic text. Missing configuration stops before the test database is reset. It writes separate `phase-05-live-tts-*` evidence and never falls back to the offline voice. Recognition and model gates remain separate.

## Current product boundary

This checkpoint uses only synthetic records and runs on loopback. The Your visit page supports audio calls. Join as Maria and Dr. Chen in separate browser profiles, agree to processing in both, then resume Vene as Maria. Declining processing preserves the human conversation. Microphone mute, Vene-output silence and processing pause are separate controls. Speech recognition in the default fixture preview is deliberately unconnected.

Maria can use Help me keep track for private unresolved-question cues. To speak publicly, choose Speak when invited and allow speaking in every connected profile. Share and approve the question for every role present, then ask Vene to say the cue aloud. Human speech interrupts; Stop Vene speaking cancels speech without pausing the humans; Pause Vene processing stops both understanding and speech. Changed permissions, corrections and expired suggestions invalidate approvals. Direct patient invitations use the same standing mode and scope; a transcript never grants permission. Agreed closeout requires shared proposed next steps and shared supporting sources. It cannot confirm a clinical decision, order or external completion.

The default Windows offline voice synthesizes original text in memory and publishes one audio track through the existing LiveKit participant. Raw audio is not recorded. Receipts report publisher playout duration and retain full wording only after completion; they never claim that a listener heard it. Interrupted speech does not retain a full delivered transcript. Live TTS is separately selected with `scripts/dev.ps1 -TtsLive` after configuring CARTESIA_API_KEY and CARTESIA_VOICE_ID in ignored .env. Missing configuration stops startup; a provider failure leaves the human call available and never becomes a scripted success.

The offline engine is reused within its owned room worker and closed with that worker; cancelled in-flight generation discards the helper. Read-only polling and transient audio-frame/heartbeat diagnostics avoid synchronous disk flushes. Permission changes, approvals, transcripts and final playback receipts keep durable commits. Recent diagnostic counters can be lost on a hard crash; they are not clinical records or proof of hearing.

Controlled Windows media tests enable Chromium's loopback peer-connection interface and use original tone inputs. The speech timing rig disables microphone echo/noise/gain processing for that fixed nonspeech input. These settings are test conditions, not a physical-acoustics qualification. The local test uses normal ICE selection with authenticated TURN offered; forcing relay-only was tested and reverted after connection failures.

On Your visit, enable visit understanding and open Fictional conversation input. Add the clear next step, corrected date and unclear owner examples to see question status, source explanations and next steps change. Inspect a source to correct its exact version. Correcting a next step saves your interpretation privately without authorizing an action. Invited views require both the step and its supporting sources to be shared; new interpretations return to private review.

The model gateway uses OpenAI's Responses API with structured Pydantic outputs, bounded context, no tools, disabled automatic retries and store=false. With a project OPENAI_API_KEY in ignored .env, `scripts/dev.ps1 -ModelLive` explicitly selects live extraction (independent of `-Mode live` for STT). Missing credentials stop startup before a fixture fallback. `scripts/check-model.ps1` runs a separate original free-form synthetic conversation gate against bring_vene_test; do not run it alongside other checks. The real-model gate remains open until that command succeeds and its output is reviewed.

To test all real providers with the original fictional cases, configure `MODEL_PROVIDER=deepseek`, `DEEPSEEK_API_KEY`, `DEEPGRAM_API_KEY`, `CARTESIA_API_KEY` and `CARTESIA_VOICE_ID` in ignored `.env`, then run `scripts/dev.ps1 -LiveProviders`. This retains loopback-only fictional invitations while recognition/model/speech use actual providers. OpenAI is an optional explicitly selected model provider. `-Mode live -ModelLive -TtsLive` disables fictional admission and requires an existing invitation/session. Missing configuration fails before starting processes; a provider failure never becomes scripted success. See `docs/qa/phase-08-live-review.md` for actual results and limitations.

Visit APIs require a server-issued session. Invitations expire after 15 minutes and redeem once; sessions expire after eight hours. The browser receives an HttpOnly, SameSite=Strict cookie. Mutation requests also require CSRF protection. Invitation links use fragments, which are removed before redemption.

Maria chooses each question's audience and approves the selected list. Sources and next-step context have independent sharing controls. Accepting a family suggestion creates a private draft. Changing a selected question invalidates list approval. Revoking a source removes it from subscribed views; withdrawing membership closes all that person's sessions and pending invitations. A new invitation does not restore old credentials.

The local launcher explicitly sets BRING_VENE_DEVELOPMENT=true and COOKIE_SECURE=false for loopback HTTP. Application defaults disable fixture admission and use Secure cookies. These prototype checks do not establish production or clinical readiness.

ContextAdapter provides separate private and audience-scoped retrieval inputs for later integration. SSE sends filtered state replacements rather than exposing the private command journal. Already delivered information cannot be recalled.

Run scripts/phase2-browser-review.mjs with the bundled Node runtime for local screenshots. It saves a private restart checkpoint under ignored .local; after stopping/restarting with the owned launchers, run it with --after-restart to verify persistence and restore the original approval.

## Architecture and progress

- IMPLEMENTATION_PLAN.md — eight phases and acceptance checks.
- BUILD_STATUS.md — actual completed work and next tasks.
- BRING_VENE_BUILD_BLUEPRINT_2026-10-12.md — product design.
- BRING_VENE_REPO_AUDIT_2026-10-12.md — upstream source/license diligence.

FastAPI owns the contracts and domain rules. TypeScript types are generated from its OpenAPI schema. Accepted edits update the encounter and command history in one transaction, with version conflict detection and command idempotency.

Secrets, database files, process state and runtime logs are ignored under .local. Only the owned launcher tree and project database are stopped by repository scripts.



## Local office follow-through

Phase 6 starts a separate persisted sandbox office and execution worker with the owned launcher. After a sourced lab step appears, share that step and its supporting sources with the clinician. Maria allows office checks and chooses a window; Dr. Chen confirms the intended step and issues a sandbox order; Maria then approves the exact reservation. The office panel shows the actual receipt. Its development controls exercise no slots, expiry, delayed responses, rejection, duplicate receipt events and timeout after write. These are fictional windows and synthetic orders; no real office is contacted. See docs/execution-adapter.md.

Run scripts/check.ps1 -Phase 6 for the complete isolated functional checks. DeepSeek (or optional OpenAI), Deepgram and Cartesia live gates remain separate; the local office needs no external provider key.

## Continuity and finishing checks

Follow-up now supports private document comparison, clinician review, field-selected family updates with sandbox acknowledgement, and a private next-visit preparation. Signed callbacks and transactional outboxes survive retries/restarts without duplicate bookings. Unknown external outcomes are reconciled from actual receipts.

The launcher provides three original fictional encounters; enable its developer checkbox to expose controlled scenario inputs. Ordinary views hide those controls. Run `scripts/check.ps1 -All` for all eight phases' local deterministic checks. Live providers remain separate: after filling ignored `.env`, run `scripts/check-live.ps1` for the combined sequential model/STT/TTS/booking/speech/timing gates. It stops before reset or provider calls when configuration is missing.

See [integration boundaries](docs/INTEGRATION.md), [demo flow](docs/DEMO.md), [live output review](docs/LIVE_GATE_REVIEW.md) and [build status](BUILD_STATUS.md). For an intentional fresh demo, stop the owned app and run `scripts/reset-demo.ps1 -ResetSavedSyntheticVisits`; ordinary startup preserves saved edits.
