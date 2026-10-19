# Bring Vene integration boundary

Bring Vene extends a patient-controlled healthcare conversation into sourced, approved follow-through. It is a separate local prototype; no access to Vene's internal code, memory, accounts or clinical systems is assumed.

## Reproducible local configuration

Run `scripts/setup.ps1` and `scripts/setup-media.ps1` on the verified Windows runtimes, then `scripts/dev.ps1`. The ignored `.local/runtime.json` holds generated local database/media/office credentials; `.env.example` lists provider names without real secrets. Default providers are labelled fixtures. DeepSeek (or optional OpenAI), Deepgram and Cartesia are separately selected; a missing or failing provider never becomes fixture success.

`ContextAdapter` in `services/backend/src/bring_vene/domain/context.py` supplies server-authorized views and retrieval input. An eventual Vene/Zep adapter must receive current encounter, membership, role and scope, return only authorized records with stable evidence IDs/versions, and preserve correction/revocation semantics. Do not replace Vene's memory platform or submit full private records for later redaction. The existing API/OpenAPI contracts can also support a surrounding Vene application rather than replacing it.

The current test configuration selects `MODEL_PROVIDER=deepseek`, `DEEPSEEK_MODEL=deepseek-flash`, Deepgram `nova-3` and Cartesia `sonic-3-2026-01-12` with public English voice Skylar. Start all three live adapters for the original fictional cases with `scripts/dev.ps1 -LiveProviders`. This keeps loopback-only synthetic invitations enabled while recognition, understanding and speech all use their actual configured providers. `-Mode live -ModelLive -TtsLive` also selects live providers but disables the fictional invitation launcher. Plain `scripts/dev.ps1` still explicitly selects fixtures. Keys stay in ignored `.env`; launchers never infer a substitute provider from a failed request.

DeepSeek uses the existing OpenAI-compatible SDK at the fixed official `https://api.deepseek.com` endpoint. Its JSON mode is validated against the local bounded Pydantic contract; incomplete, empty, invalid or tool-call responses fail. Thinking is explicitly disabled and temperature is zero for visit extraction, and no reasoning content is retained. Source versions, exact quotes, audience checks and correction/approval fences remain in the existing domain service. Provider provenance is `deepseek`, not `openai`.

Audio ingestion uses 100 ms native frames with a two-frame queue and a current authorization check before each batch reaches the provider. Receipt and interruption activity remain 20 ms windows within each batch. Deepgram finalized segments are assembled per authorized track until an end-of-speech event, with 300 ms endpointing and a 12,000-character bound. Pause/revocation discards unfinished text; it does not flush it into the saved transcript. Public closeout selects currently shared steps and sources before forming speech, and keeps the same scope check before queueing and playout. Unshared steps are excluded from the spoken contribution.

## Office and family adapters

`OfficeGateway` currently permits only the explicit loopback sandbox. Lookup accepts administrative place, calendar date and window; order and booking APIs use opaque IDs. Clinical text and patient names are not needed for these calls. A real adapter needs independent authentication, permission recheck at the last reversible boundary, stable idempotency keys, real order verification, a receipt schema and reconciliation. Local clinician confirmation is not professional identity verification or a real order.

Callbacks send a JSON `OfficeCallback` to `/integrations/office/results`. Headers `x-office-timestamp`, `x-office-nonce` and `x-office-signature` sign `timestamp + '.' + nonce + '.' + exact_body` with HMAC-SHA256. A fresh UUID nonce and <=60-second timestamp are required; used nonces are rejected. Delivery ID and immutable result identifiers correlate only to an already dispatched action. Retry the same delivery ID/body with a fresh nonce after lost acknowledgement. Callback credentials are independent from browser sessions. The callback outbox is owned by `bring_vene.continuity.office_worker`.

Family text is formatted only from the selected fields already visible to the selected current member. The patient approves that exact digest; the durable family outbox rechecks it before transmission. A receiver acknowledgement is a sandbox delivery receipt, not proof that a person read it. The independent local receiver retains only a payload hash and receipt, not the update text. Delivered information cannot be recalled; later revocation removes retrieval and prevents pending work.

## Documents, review and recovery

Upload text or machine-readable, unencrypted PDF <=250 KB/10 pages. The pinned pypdf child has no database/provider secrets, a five-second timeout and extraction limits. Raw upload bytes are not saved. Extracted source text, SHA-256 provenance, page offsets and exact quotes are saved privately. The limited discrepancy matcher flags wording/day/place differences and always requires human review; it cannot establish clinical correctness. Clinician review acknowledges differences without changing medication, a plan or an existing reservation. A new related document invalidates pending booking approvals until current review.

A next visit starts with private copied preparation, no inherited approval and no guest membership. Existing guest credentials cannot access it. Worker restart records a new worker instance, visible processing gap and manual resume; human participants keep their room. Unacknowledged dispatches remain unknown until an actual receipt is reconciled. Neither a correction nor deletion reverses an external reservation.

Operational traces have only an allowlist of IDs/timing counters and are pruned after seven days. Used callback nonces are pruned after three minutes; expired signed messages cannot be replayed. Document text persists until explicit visit deletion; this is not an automatic patient-record retention policy. Visit deletion purges sessions, evidence, documents, derived next visits and local queues/caches; unresolved external work blocks deletion. A minimal audit records only deletion time and count. Real-use logging/audio retention policies need separate deployment design; raw audio is unrecorded by default.

## Verification

` scripts/check.ps1 -All ` runs deterministic local checks. `scripts/install-extra-browsers.ps1` installs optional owned Firefox/WebKit builds under `.local/pw-extra`; smoke evidence describes platform limitations. `scripts/check-live.ps1` first verifies the explicitly selected model provider and its key, Deepgram key, Cartesia key and voice ID, then runs actual model extraction, original synthetic speech through Deepgram/configured model/Cartesia into a sandbox booking, speech safety checks and twenty timing trials, sequentially against the isolated test database. Review its generated wording and evidence with `docs/LIVE_GATE_REVIEW.md`; passing code is not patient/clinician acceptance.

For a deliberate fresh demo, stop the owned app, run `scripts/reset-demo.ps1 -ResetSavedSyntheticVisits`, then start it again. This explicitly replaces saved edits in only the three known fictional cases and their derived visits. Ordinary startup preserves saved state. `scripts/reset-demo.ps1 -Test` exercises the same reset against the isolated test database. Never run reset/model/browser checks concurrently.

Controlled local media tests allow loopback ICE and disable client mDNS address obfuscation in those owned test browsers. The server uses numeric loopback candidates, and its authenticated TURN permits the single loopback peer CIDR. These are local test conditions, not a claim that physical devices, public hosting or every ordinary browser has been qualified.

The local voice supervisor owns at most four per-room multiprocessing runtimes. Native joins/crashes are isolated, obsolete generations are stopped by owned process handles and their exact old room is closed, and an unavailable transport pauses processing before restarting. The same RoomWorker/domain services run inside those children; no transcript or audio crosses a multiprocessing IPC queue. Both human clients and the native SDK use one peer connection. This avoids a listen-only join depending on a later publisher and prevents a stale native join from holding up replacement after server loss.

One runtime is prewarmed without connecting or processing audio; launchers wait for an opaque per-run readiness marker. Room readiness still comes from the actual connected heartbeat. Warm processes carry no audio or transcript IPC. Recovery duration is variable (7.95 seconds in one full run, about 25.3 seconds in another focused run) and must be measured again under live providers. Native FFI cleanup assertions have been observed; the prototype is not qualified for production uptime.

The browser proxy only accepts an HTTP loopback backend and forwards the original cookie/CSRF/origin controls. Each upstream request owns a fresh Node HTTP connection; ordinary JSON has a 15-second deadline and a reset becomes an explicit unavailable response. Stream cancellation destroys its socket. Mutation requests are not automatically repeated, and a missing response requires reviewing saved state before retrying. This bounds local service-restart failures without manufacturing success.

Supervisor stdout/stderr share an owned log whose lifetime spans child restarts. Children must pipe with end:false; closing that destination can eventually block the restarted process. A two-child large-output regression checks real drainage. Native room joins that never make a connected heartbeat are stopped by the 15-second owned-process startup watchdog and replaced; each runtime has a unique assistant identity under the same generation. Processing stays unavailable/paused until actual recovery and patient resume.

Latest final local observations: media-server recovery safely paused at 6,731 ms; the voice-process recovery sequence safely paused/ready at 18,028 ms. These individual functional observations do not replace dedicated timing or physical/live-provider review.

## Phone bridge contract (Phase 12b)

Real telephony is not part of the local build. A phone bridge (for example LiveKit SIP with a Twilio inbound trunk) would:

1. Answer the call in a lobby, play a short greeting and collect a 6-digit PIN with DTMF.
2. `POST /integrations/phone/admit` with `Authorization: Bearer $PHONE_BRIDGE_TOKEN` and `{pin, participant_identity, caller_number?}`. `caller_number` is accepted and ignored; the PIN alone binds the call to one invited membership. The response names the visit room, the person, the disclosure to speak and the keypad prompt.
3. Move the SIP participant (same `participant_identity`) into that room and speak the disclosure and prompt.
4. Keypad digits reach the visit through the voice worker's `sip_dtmf_received` handler: 1 agree, 2 decline, 9 pause (anyone), 0 resume (patient line only, when everyone agreed).

PINs are single-use, expire after 15 minutes, are stored hashed, and one live PIN per person replaces older ones. Revoking the PIN or the person's access invalidates the phone connection, and the worker removes it from the room. Bridge-side brute-force limits (attempts per call) and the lobby/move steps are unimplemented and unverified.
