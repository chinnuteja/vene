# Configured provider review — 15 October 2026

The user authorized live calls using test credentials. Keys are in ignored `.env`; no values are copied into QA reports. All speech and conversation text is original fictional material. Calls to the office remain actual HTTP requests to the local sandbox. No real healthcare call or patient data was used.

## Configuration and changes

- Deepgram `nova-3`, the existing pinned LiveKit plugin, 16 kHz recognition input. Final segments are now assembled per authorized track until the SDK end-of-speech event, with 300 ms endpointing and a 12,000-character bound. Pending text is discarded on processing cancellation.
- DeepSeek `deepseek-flash`, verified through the authenticated model list and actual extraction requests. The existing pinned OpenAI-compatible SDK uses the fixed official DeepSeek endpoint, JSON mode, thinking disabled, temperature zero, no automatic retries and a bounded timeout. Local Pydantic validation and the existing source/version/permission fences remain authoritative. Provenance is explicitly `deepseek`.
- Cartesia `sonic-3-2026-01-12`, public English voice Skylar (`db6b0ed5-d5d3-463d-ae85-518a07d3c2b4`). Authenticated voice discovery succeeded. The application synthesizer returned 3,911 ms of audio for the original preflight sentence; no generated audio was recorded.
- Closeout filters current shared steps and sources before composing its contribution. Existing checks still run before queueing and playout. A private step must neither enter public speech nor block another eligible shared step. Scope-related UI errors now state the actual sharing requirement through an exact-message allowlist.
- `scripts/dev.ps1 -LiveProviders` preserves loopback-only fictional invitations while explicitly selecting all three real adapters. Plain startup still selects fixtures. No automatic live-to-fixture fallback exists.

## Failures found during actual testing

1. The first model result split a lab order and lab visit into duplicate `lab` topics and used an extended timeframe. This conflicts with the current one-step-per-topic plan. The extraction contract now states that prerequisites belong in dependencies and owner/date/location are exact excerpts.
2. The first browser closeout was blocked when it included an unshared step. Public closeout selection now uses the existing participant/source scope rule before selecting its two steps. A mixed-private/shared backend regression checks that private text is absent from the delivery and guest payload.
3. Chromium's looping controlled speech file can advance before consent. A later run captured only the closing test sentence and the start of the next loop. The gate now requires the complete actual recognized lab statement before muting, and waits for understanding to finish. It never substitutes known fixture text for recognition.
4. On unrelated/incomplete speech, an earlier model response invented question-derived follow-up steps. Another response left the owner unknown but also cleared a known date/place. Prompt `visit-extraction-v4` and the live gate now explicitly test both cases. These are observed failures followed by bounded checks, not a claim that prompting eliminates all unsupported outputs.
5. Several attempts failed at the patient WebRTC connection before provider processing (`pc connection`). It is retained as a reliability limitation; a later successful run does not establish production uptime. The UDP relay attempt also failed: the selected loopback pair sent 221 connectivity requests and received zero responses. Browser transport defaults were restored. A TCP-only trial also failed, so that setting was reverted. The passing combined and Cartesia safety runs used the original loopback media configuration and explicit local-network permission in the owned Chromium contexts. No firewall, SDK source or data-permission change was made. Credential-free ICE diagnostics are recorded on setup failure.

6. Actual audio counters exposed throughput loss: 17.36 seconds forwarded across 46.92 seconds of reception (868 accepted 20 ms windows). Per-frame authorization/database work could not keep up with 50 native frames/second. Input now uses 100 ms native batches with at most 200 ms queued; every batch rechecks current authority, and its five 20 ms activity windows retain interruption/counter semantics. The existing pause/epoch fence still discards queued data. Live recognition and timing must be repeated after this change.
7. A valid unanswered question may have no citation. Such an `open` response now leaves the question open without saving unsourced prose or creating a spurious clarification step. Claimed answers still require exact current citations.

## Evidence and remaining review

`phase-04-real-model.json` contains the actual bounded synthetic inputs and outputs for unrelated speech, the initial plan, an explicit date correction and ambiguous ownership with retained date/place. `phase-08-cartesia-preflight.json` records actual synthesis. `phase-08-live-config.json` is presence-only and is not credential validity evidence by itself. Earlier failure reports remain distinguishable from passing reports.

Full combined browser and repeated speech timing results are recorded below only after completion. Physical microphones, acoustic listening quality, accents, patient/clinician acceptance and clinical or regulatory readiness are not established by these checks.


## Completed live gates so far

- `phase-08-live-providers.json`: combined gate passed at 07:55 UTC. Actual Deepgram evidence names Maria, Riverside Lab, Tuesday and the order prerequisite; the proposed item retained all approval/order/completion flags as false before explicit human actions. Shared-only Cartesia closeout played 10,839 ms, and the sandbox returned a persisted confirmed reservation receipt after separate clinician/order and patient approvals. The source snapshots precede sharing and approval. Unanswered selected priorities: two at the captured snapshot. The synthetic test marker had one recognition error ("renal" instead of "original"); it was not used as evidence for the lab proposal. This is targeted functional verification, not a general speech-accuracy benchmark.
- `phase-05-live-tts-browser-report.json`: private cue/guest exclusion, completed audio, no self-transcription, actual human interruption and pause passed at 07:58 UTC.
- First repeated-timing attempt did not obtain an interruption before the short contribution completed (3,820 ms playout, no stop-detection timestamp). It produced zero valid timing samples and is not counted as a passing measurement. The repeated test uses a longer explicitly recorded question, prepositions the remote unmute control and checks that speech is still active at interruption request. Its conditions differ from the earlier offline trial.
