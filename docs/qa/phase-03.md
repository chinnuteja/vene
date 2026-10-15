# Phase 3 — multiparty media and consent lifecycle

Local verification on 13 October 2026 (Asia/Calcutta). Synthetic encounter and generated audio only. Implementation and real-media verification are complete; live-provider STT accuracy remains an open gate.

## Implemented

- An owned LiveKit 1.13.9 Windows server runs locally alongside the API and voice worker. The official archive is pinned by URL and SHA-256 in infra/livekit-binary.json; generated credentials and server configuration remain under ignored .local. Signaling and TURN listeners bind to loopback. Loopback ICE candidates and mDNS resolution support browsers without microphone permission.
- The API issues two-minute, session-bound, room-generation-scoped JWTs. Browser roles, identity metadata and requested room names cannot select privileges. Tokens start listen-only; the supervisor verifies the current server admission before enabling microphone publication. Browser data publication, metadata updates, room administration and recording grants are absent or disabled.
- The visit page has device selection/checking, a microphone-free join path, human audio playback and an actual, visible Vene participant. A microphone can reach the other humans while Vene processing is paused.
- Each present participant independently agrees or declines. New arrivals and new track publications pause processing. Only the patient resumes or ends the call; any invited participant can pause. Withdrawal, expired sessions and retired connections cannot authorize processing. Membership withdrawal ends the old room generation; only the patient can reopen an ended call.
- Microphone mute, output silence and processing pause are separate controls. Pause cancels pending starts, track consumers and provider readers. The worker acknowledges the stopped epoch only after processing tasks close; it does not drain buffered audio afterward. SDK reconnecting states are not reported as healthy processing.
- Source attribution binds authorized connection, track SID, track epoch, room generation and consent epoch. Late finalized callbacks fail the current authorization check before persistence. The supervisor registers starts before awaiting them and removes completed/cancelled tasks safely.
- Raw audio is not written to disk. There is no egress/recording service, automatic shared transcript publisher or ordinary transcript logger. Stored audio receipts contain counts/timestamps only. Real-provider utterances are private to the patient; other roles cannot fetch them or processing diagnostics.
- Fixture and Deepgram adapters use the same supervisor/domain services. Fixture mode receives real WebRTC audio and records transport evidence without inventing transcripts. The live adapter owns its HTTP session, bounds provider connection retries, closes its streams on pause and reports failure rather than falling back to fixture success.
- The browser uses the supported dual-peer-connection transport mode for verified compatibility with this local server. Call snapshots include observation time, preventing an older poll from overwriting a newer control acknowledgment. LiveKit code loads only with the call UI, keeping preparation/next-step initial bundles at about 118 kB in the verified build.

Relevant files: services/backend/src/bring_vene/voice, migration 0003_calls.py, apps/web/src/components/call-panel.tsx, scripts/setup-media.ps1, scripts/dev.mjs and scripts/browser-check.mjs. The voice worker shares the backend package deliberately; services/voice/README.md documents that boundary.

## Verification

The final scripts/check.ps1 -Phase 3 run exercises real Postgres migrations, backend tests, generated contract drift, TypeScript, production build and an isolated production browser stack. Browser tests start their own API, LiveKit and voice worker against bring_vene_test. They do not reset or mutate the working preview database.

Final command: `scripts/check.ps1 -Phase 3`. Passed on 13 October 2026 at 13:25:36 +05:30, taking 260.99 seconds: 45 backend tests, generated contract check, TypeScript, production build and all 14 Chromium scenarios. The result is also recorded in BUILD_STATUS.md and ignored .local/check-phase-03.json. Live STT is explicitly `unverified_missing_project_credentials`; physical microphone is `not_exercised`.

The real-media scenario uses two independently launched Chromium instances with different, original three-second tone WAVs. It verifies distinct connection/track IDs, overlapping reception windows, zero accepted frames before consent, declining consent, separate output silence, stopped tasks and stable frame counts after acknowledged pause, late arrival, fresh rejoin provenance and patient-only transcript access. Tone transport is not speech recognition.

Backend checks additionally cover token scopes, own-connection consent, guest restrictions, replay/idempotency, stale consent/track callback rejection, revoked membership, new room generations, provider failure without fallback and 30 cancellation/startup cycles without orphan tasks.

Fault scenarios:

- Browser microphone permission is actually denied; joining without a microphone remains possible and emits no receipts for that connection.
- A published real WebRTC track is stopped; its hardware-ended event is simulated. A replacement track gets a newer epoch and requires agreement again. This does not claim a physical USB-device unplug test.
- Only the owned test LiveKit PID is stopped, with workspace/path/parent/start-time checks. The UI leaves the stale connection, processing becomes unavailable, the local test server is restarted, and fresh admission succeeds with processing still paused. No unrelated server is killed.

During development, the interruption left Postgres stopped. The owned database was restarted and recovered before tests resumed. A database-unavailable test run was not treated as an application pass. Other failures exposed loopback/mDNS configuration requirements, SDK retry states being reported as connected, unscoped alert selectors, and snapshots captured before pause acknowledgment. A recovery cleanup race also showed that an old worker could delete a freshly rejoined room; room deletion is now restricted to ended/revoked generations. These were repaired and rerun.

Transport recovery rotates the room generation before readmission, fencing old connections and consent. The worker manager tracks cancelled cleanup tasks separately so a slow failed SDK disconnect cannot block the replacement worker. During verification, overlapping backend and browser runs reset the same isolated test database; that browser run was discarded and the complete check was restarted sequentially.

Evidence files:

- phase-03-media-report.json — actual source/consent/pause results and browser runtime errors.
- phase-03-call-desktop.png and phase-03-call-mobile.png — two humans and Vene.
- phase-03-paused.png — acknowledged processing pause.
- phase-03-microphone-denied.png and phase-03-server-loss.png — fault states.
- docs/qa/dependency-licenses.json — updated resolved package metadata.

Screenshots were opened for visual inspection. Chromium/Playwright is the actual browser-control evidence. The Codex preview-open request returned queued; it is not evidence of inspection of the visible Codex tab.

After the complete check, `scripts/stop.ps1` stopped only the owned development process tree and `scripts/dev.ps1 -Mode fixture` restarted the preview with the final implementation. A separate Chromium run opened `/dev`, redeemed Maria's fictional invitation and verified both visit prejoin controls without opening a microphone. It reported no page runtime errors; phase-03-preview-report.json and phase-03-preview.png record that check.

## Reuse and primary references

TrackSupervisor adapts the lifecycle structure from [LiveKit's multiparty transcription example](https://github.com/livekit/agents/blob/b58e83f5c77d5b4bd4c8586793885151a91c4c83/examples/other/transcription/multi-user-transcriber.py), Apache-2.0. The included license and attribution notice are under services/backend/src/bring_vene/voice/licenses; reuse-manifest.json records the source and modifications. Automatic text output, transcript logging, startup resurrection and drain-on-close were not retained.

[LiveKit Meet](https://github.com/livekit-examples/meet/blob/13e4fd88d6f3c238060746a8f476e32af5c97fbf/app/rooms/%5BroomName%5D/PageClientImpl.tsx) informed pre-join/device/RoomContext patterns; our admission endpoint and call UI are custom. Transport uses livekit-client 2.22.4, components-react 2.9.24, Python RTC 1.1.20, API 1.2.1 and Agents/Deepgram plugin 1.8.6.

[Local server guidance](https://docs.livekit.io/transport/self-hosting/local/) and the installed SDK/source were checked for transport and grants; [Deepgram integration guidance](https://docs.livekit.io/agents/models/stt/deepgram/) informed the live adapter. These references do not establish provider accuracy for this application.

## Explicit open gates

- No project DEEPGRAM_API_KEY is configured. Explicit live-mode startup was tested and refused to start a fixture fallback. The live adapter is implemented but no real-provider speech accuracy session has passed.
- No physical microphone, speaker, echo/noise or acoustic-quality session was exercised. No production latency/capacity benchmark is claimed. The official Windows server reports CPU capacity monitoring unsupported; local transport still works.
- Attribution identifies an authorized browser/track, not biometric identity or professional verification of a clinician. Previously delivered speech cannot be recalled.
- Raw audio remains ephemeral. Recording/egress is not configured, but these local checks are not production or regulatory certification.
- Vene's spoken output and grounded clinical-plan extraction are later phases. Output-silence control is implemented and independent; actual TTS playback has not been claimed connected.
- The current call belongs to the visit page; navigating away disconnects that browser's call. Cross-route continuity is not yet implemented.

No deployment, real-patient input, healthcare-service call or founder messaging occurred. Next is Phase 4's grounded understanding and evolving plan; retain the live STT gate until project credentials and a synthetic spoken session verify it.

