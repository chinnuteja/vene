# Phase 4 — grounded understanding and the evolving visit plan

Local synthetic verification, 13 October 2026. Implementation and local gates passed. The real-model gate remains open because no project OPENAI_API_KEY is configured. No fixture result establishes language-model quality.

## Implemented behavior

- Finalized, consent-permitted voice utterances create private versioned conversation evidence in the same database transaction. Fixture text enters through a separate, explicitly labelled local patient-only endpoint and uses the same interpretation, citation, correction and persistence services. No fixture audio is presented as recognized speech.
- A project-owned understanding worker runs outside the media loop. Its input is limited to 30 recent finalized sources, 24,000 source characters and 20 selected priorities. It does not retrieve unrelated private office/patient evidence or accept a browser-selected model audience.
- The gateway proposes priority status and next steps with owner, timing, location, dependencies and exact source ID/version/quote citations. An unrelated mention is not an answer. The deterministic adapter covers the original lab/referral cases only; it is not a general language model.
- The live gateway uses OpenAI Python SDK 2.54.0 and Responses structured Pydantic outputs. Requested default model: gpt-6-astra; prompt version: visit-extraction-v1. Provider/model, input snapshot, fingerprint, result and terminal state are journaled per run, including the returned model identifier when a response exists. No tools or dispatch routes are given to the model. store=false and max_retries=0 are explicit; request timeout defaults to 20 seconds. These options do not establish account-level data retention or clinical readiness.
- Acceptance rechecks patient session authority, current encounter version, consent epoch, source revisions and audio-processing gate for real voice sources. Missing, foreign, outdated or fabricated quote citations produce a safe clarification draft, rather than publishing invented details. Unsupported owner/time/location spans remain unresolved.
- Transcript/model text cannot set audience, approval, clinical confirmation, order availability or external completion. All newly derived steps are drafts and private. Guest REST/SSE views exclude the understanding controller and private conversation sources. Sharing a step alone cannot publish it without all cited sources; new answer interpretations also require fresh patient sharing before an invited role can receive them.
- Source corrections increment version, retain prior text in a private history, make the changed source private, invalidate dependent interpretations and fence in-flight results. The corrected source moves to the latest context position. A saved patient step correction is not overwritten by a later model response. If an already externally completed item ever requires reconciliation, its completion is preserved and flagged; no local correction claims to reverse a booking.
- The existing three visit-card areas update through the authenticated, audience-filtered SSE view service. Source dialogs expose exact text/version and correction controls. Next steps distinguish proposed understanding, unresolved owner/time/location, dependencies and actual confirmation/completion. Follow-up reads the persisted fields.
- Understanding failure preserves the existing plan and human call. Retry is explicit. Generation is cancelled when its snapshot/consent becomes stale, and late completions fail transactional validation. Disabling understanding does not mute the human microphone; the real voice processing pause also fences generation based on voice sources.

## Verification and evidence

Final command: `scripts/check.ps1 -Phase 4`. Passed at 15:01:37 +05:30: 66 backend tests, contract drift check, TypeScript, production build and all 16 Chromium scenarios. The final browser suite itself took about 1.2 minutes; total command wall time was 627.81 seconds including an external tool/approval delay. An earlier combined 65-test/16-scenario run also passed before the availability regression was discovered and repaired. The production visit/prepare/follow-up bundles were about 120 kB initial JavaScript, with LiveKit still loaded separately by the call panel. All screenshots were opened; the final desktop explanation layout is readable and the mobile viewport has no horizontal overflow.

Initial backend checks passed 65 tests, including existing Phases 1–3. Added cases cover explicit/partial/deferred answers, unrelated mentions, injection-like source text, corrected dates, ambiguous owners, source invalidation, stale results, all four citation failures, manual correction, guest payload isolation, expired authority, idempotence, bounded context, voice-to-source ingestion, pause fencing, provider failure, SDK request parsing with an in-memory HTTP fixture, timeout and cancellation. The SDK fixture is not a real provider response.

Browser acceptance exercises Thursday → Tuesday → unknown owner, a version-2 source correction, manual Friday correction, persistence after refresh, step-plus-source sharing and a separate invited renderer. An injection-like fictional turn cannot expand permissions or mark an action completed. Desktop/mobile and source-dialog images are opened for visual review.

Evidence:

- phase-04-browser-report.json — actual correction, sharing and browser results; provider explicitly fixture.
- phase-04-evolving-desktop.png, phase-04-evolving-mobile.png, phase-04-source.png — visit and cited-source captures.
- ignored .local/check-phase-04.json — final combined check result, when passed.
- phase-04-real-model.json — created only by an actual successful check-model.ps1 run; currently absent.

During development, exact textarea-label matching stalled a browser correction; explicit accessible labels repaired it. Sharing checkboxes wait for server persistence, so the test now clicks and awaits the checked state. The combined suite also exposed a synchronous runner waiting while child logs were piped: the runner now awaits the CLI asynchronously so API/media/worker logs drain during testing. Visual inspection found the answer explanation occupying a narrow grid column; its text and citation links now span the question-content column. Failed runs were not labelled passing evidence.

The refreshed development preview exposed a selected availability question incorrectly matching the substring “lab.” Fixture topic matching now uses whole words, and full-context re-assessment clears previous answer interpretations that are omitted/unsupported. A dedicated regression test verifies both behaviors; the complete check was rerun after the repair.

The working database was upgraded to migration 0004 without resetting preparation or sharing. The project-owned development tree was restarted with the final worker code. A separate Chromium run opened Maria's preview, added labelled fictional lab text, awaited its accepted and processed revision, verified that the unrelated availability question stayed open, and paused understanding afterward. The saved draft is visible at /visit. phase-04-preview-report.json and phase-04-preview-card.png record the check. The final input-injection browser test likewise waits for the newly accepted source revision to finish, rather than mistaking a previous saved state for success.

## Open gates and operating boundaries

`scripts/check-model.ps1` was attempted with no configured project key. It reported UNVERIFIED and stopped before any model call, database reset or fixture fallback. `scripts/dev.ps1 -ModelLive` was also attempted and refused startup before launching a fallback. A real free-form extraction conversation remains required for Phase 4's complete exit evidence.

Phase 3's live Deepgram STT and physical-microphone gates remain open. No deployment, founder contact, real patient input or healthcare-service call occurred. No end-to-end acoustic, production latency, distributed-worker recovery, clinical or regulatory readiness is claimed. Vene output/floor control and external administrative execution belong to later phases.

## Reuse

Reused the existing Pydantic contracts, transactional projections, ContextAdapter, server sessions, SSE filtering and LiveKit finalization boundary. New application services and scenario fixtures are original. [Official structured-output documentation](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses) informed the maintained SDK integration; reuse-manifest.json and THIRD_PARTY_NOTICES.md record it. No agent example with public transcripts or broad permissions was copied.
