# Phase 8 integration, accessibility and packaging QA

15 October 2026. Implementation and local fixture gates passed. Configured live-provider, timing, physical-audio and human-acceptance gates remain open.

## Final verification

The unchanged backend passed 133 tests, including 17 continuity and 17 execution cases. The owned-process log regression passed: two sequential real child processes each drain 1 MiB stdout plus a stage marker through the same still-open destination. Contracts, TypeScript and optimized Next.js build passed.

`check.ps1 -All` passed those stages and found one populated follow-up overflow at 200% zoom. After the layout-only correction, `pnpm typecheck`, `pnpm build` with NEXT_DIST_DIR=.next-check and `browser-check.mjs` with BRING_VENE_PHASE=8 passed the final entire browser suite: **25 passed, 2 explicitly skipped, 0 unexpected or flaky**, 5.5 minutes. The skipped cases are the separately invoked twenty-trial timing gate and configured live-provider gate. See phase-08-final-checks.json.

The browser run covers private multi-role payloads and revocation, one-use invitations, scoped live updates, real local multiparty WebRTC, microphone denial/replacement, actual received speech and interruption, grounded corrections, separate order/patient approval, actual sandbox booking/reconciliation, signed callbacks, original PDF review, acknowledged selected-field family delivery, private next visits, disposable deletion, actual API/worker/media-server restarts, three different fictional cases, keyboard focus, reduced motion and populated 200% reflow. Screenshots and per-scenario JSON evidence are in this directory.

## Repairs verified in the final run

- Owned child stdout/stderr must pipe with end:false. The former default ended the shared destination after stopping a child; restarted API access logs then filled an undrained pipe and blocked requests. The large-output regression and full post-restart run verify the repair. Earlier fetch-pooling explanations were hypotheses, not the confirmed cause.
- The loopback web proxy now owns cancelable Node HTTP connections, buffers ordinary responses under a 15-second deadline and returns explicit unavailability on failure. Mutations are not automatically repeated. The three-role stream/API-restart regression requires subsequent patient edits and scoped guest reads to complete.
- Native SDK runtimes are isolated per room, at most four including a prewarmed spare. A healthy spare remains ready. A join without a real connected heartbeat is stopped by a 15-second startup watchdog and its own process is replaced. Each runtime has a distinct disclosed assistant identity. SDK prewarming never claims room readiness or processing consent. Recovery records a gap, pauses processing and requires patient resume.
- Routine canceled native joins drain the SDK ready-event handshake before cleanup. Native FFI disposal assertions have been observed; their containment does not qualify production uptime.
- Numeric loopback candidates/mDNS disabled and authenticated loopback TURN are explicit controlled test conditions. No transport encryption or application permission bypass is added. Test tone captures disable speech DSP only in owned fixture browsers; physical voice quality remains untested.
- Office scenarios normalize their independent conditions; failed synthetic room scenarios end their own call. Safe status GETs may retry ECONNRESET twice; action requests are not retried. Whole-scenario budgets include setup/recovery; dedicated performance targets are unchanged.
- Loading states distinguish pending retrieval from missing office/follow-up data, reopened office forms retain the actual requested date, document citations show pages, and populated continuity grids shrink/wrap at zoom. Ordinary views hide developer controls; the checkbox is off by default and never grants backend authority.

After interruption, the stopped existing native Postgres cluster was restarted from its verified project data directory without resetting development visits. The connection-only failed pytest attempt was stopped before final verification.

## Platform and reset evidence

Chromium real media passed. Firefox 157 on Windows passed forms, actual two-peer room admission and synthetic microphone publish/mute. Windows WebKit 27.2 exposes neither RTC nor getUserMedia: forms and the explicit unsupported-media fallback passed, its media gate did not. iOS/macOS, physical microphones/acoustics and screen-reader acceptance were not exercised. See phase-08-firefox-smoke.json and phase-08-webkit-smoke.json.

The guarded reset passed against bring_vene_test: three private fictional roots reset, an unrelated inserted test record preserved, and a development reset without the explicit switch rejected before opening the engine. Saved development data was not reset. See phase-08-reset.json. Ordinary startup preserves saved records.

## Reuse and advisories

Direct versions are frozen. Final pnpm audit and exported frozen Python pip-audit report zero known vulnerabilities. Four transitive PostCSS 8.4.31 advisories were addressed by the compatible Next.js override to 8.5.30; initial and final snapshots are retained. These are dependency checks, not a security certification. Maintained SDKs, the pinned pypdf parser and original Node stdlib lifecycle helpers avoid copying entire upstream applications. Origins/licenses are in reuse-manifest.json and THIRD_PARTY_NOTICES.md.

## Remaining gates

All four live configuration fields are still absent: OPENAI_API_KEY, DEEPGRAM_API_KEY, CARTESIA_API_KEY and CARTESIA_VOICE_ID. The combined check-live.ps1 gate fails before reset/provider calls when configuration is missing; it never converts a failed provider into fixture success. Original synthetic live speech was generated locally, but recognition, free-form extraction, actual Cartesia quality and end-to-end output review remain unverified.

The final functional media-server recovery took 6,731 ms to become safely paused; the voice-restart observations reached safely paused/ready at 18,028 ms including the test's recovery sequence. These are individual functional observations, not latency qualification. Earlier offline twenty-trial p95 speech startup proxy was 3,127 ms (roughly 2,000 ms target missed), stop-to-silence 473 ms (500 ms target met). Repeat the dedicated measurements with the configured providers before claiming improvement. Human patient/clinician acceptance remains separate. No founder-demo, clinical or production readiness is inferred from fixture tests.

## Saved preview review

The restored project-owned preview is running at http://127.0.0.1:3000/dev (API 8001). `scripts/phase8-browser-review.mjs` passed against the saved development database: preparation/visit/follow-up desktop views and 390px mobile, ordinary debug controls absent, no page errors or horizontal overflow, and saved plan/evidence/priorities/version unchanged. No room join, booking or provider call was made by this review. The current mobile family empty state and 200% follow-up capture were visually inspected. See phase-08-preview-review.json and phase-08-preview-*.png. Opening the in-app preview was queued by Codex; HTTP readiness and browser inspection were independently verified.
