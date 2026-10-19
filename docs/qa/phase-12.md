# Phase 12 — phone on the table and dial-in

Date: 19 October 2026. Plan: IMPLEMENTATION_PLAN_PHASES_9-12.md, Phase 12.

## Outcome

**12a, one phone in the room.**

1. Maria puts her phone on the table and declares who is present. She can tap quick-add for invited people or type a name.
2. She reads or plays the disclosure and records each person's spoken agreement.
3. Until everyone has agreed, nothing is processed: the processing gate, resume and room-speech ingestion all stay closed. If anyone declines, Vene stays off and the conversation continues as usual.
4. The phone's microphone is diarized into anonymous voices. Maria names each one ("That's Dr. Chen"). Renaming a voice corrects every transcript line with that label and invalidates any interpretation built on them.
5. A name given to a voice is attribution only. The clinician's spoken words cannot confirm a step or issue an order; that still needs the clinician's own authenticated session.
6. If someone arrives, the call pauses and processing stays closed until they hear the disclosure and agree.

**12b, dial-in, visit side.** Maria creates a single-use PIN for one person. A phone bridge admits the caller with that PIN; the caller's number is never used. Keypad controls: 1 agree, 2 decline, 9 pause (anyone), 0 resume (patient only, and only when everyone agreed). Revoking the PIN or the person's access invalidates the phone connection.

## Implemented

| Area | Change | Files |
|---|---|---|
| Room session | People, disclosure time and patient-attested agreement, with states setting_up, active, declined and off. Any change bumps the consent epoch and pauses a running call. | `room/service.py`, migration `0013_room` |
| Gate | `voice.gate`, call resume and room ingestion all require an active room whenever room mode is on. Feasibility checks already hold while the call is paused. | `voice/service.py`, `room/service.py` |
| Diarization | Deepgram diarization is enabled only on the patient's own room track (`room_track`). The sink finalizes each consecutive speaker in a turn separately with its label. `voice.finalize` routes labelled turns from that device through room ingestion. | `voice/supervisor.py`, `voice/worker.py`, `voice/service.py` |
| Attribution | `Evidence.speaker_label` and `Evidence.attribution` (`session`, `patient_attested`, `unattributed`). Remapping versions each affected source, keeps its history, and invalidates dependent plan steps and answers as a source correction does. | `domain/contracts.py`, `understanding/service.py`, `room/service.py` |
| Self-speech | Browser echo cancellation is the first defence. A finalized room turn whose words are at least 60% a repeat of what Vene was saying (during playback or up to 8 s after) is dropped and counted. | `room/service.py` |
| Dial-in | Hashed six-digit PINs, 15 minutes, one live per person. A token-authenticated bridge admission endpoint. Phone connections are bound to their PIN by a schema check constraint, with a nullable session and a `dial_pin_id`. Keypad handling, and the worker's `sip_dtmf_received` handler. | `dial/*`, migration `0014_phone_identity`, `voice/worker.py` |
| UI | Phone-first "One phone in the room" card: setup collapses while listening, a large Pause button, and speaker naming showing each voice's last words. Guests see only a one-line note that room mode is on. Preparation gains "Join by phone" PINs. | `components/in-room-mode.tsx`, `dial-in.tsx` |

## Defects found during this phase

1. **Phone connections had nowhere to bind.** The first design stored a PIN reference in the connection's `session_hash`, which is a foreign key to browser sessions, so the database rejected it. The connection now has an explicit `dial_pin_id`, with a check constraint that each connection is either browser-bound or PIN-bound. The local databases still held the old 0014 schema and were rolled back by hand; nothing had been released.
2. **Setup crowded the phone screen.** With everyone agreed, the setup steps still pushed Pause and the speakers far down. Setup now collapses while listening (found in screenshot review).
3. **Family suggestions were rejected by unrelated patient changes.** Found in the second full run (`audience.spec.ts`). The family member submitted "Suggest to Maria" with the version from just before the patient's last sharing toggle, and the server answered 409 "The visit changed". The family member could not see that change and had done nothing wrong. A suggestion only appends a proposal and touches nothing the patient owns, so it is now exempt from the version fence. Command-ID idempotency still applies, and every patient edit stays fenced. Backend test `test_family_suggestion_survives_a_concurrent_patient_change_but_edits_stay_fenced`; mutation-checked (restoring the fence fails it).
4. **Room test race.** The test waited for the card to contain "Dr. Chris Chen", which was already true because of the "That's Dr. Chris Chen" button, and then read the evidence too early. It now waits on the speaker's displayed name and polls the API.
5. **Test order.** The room test first ran after `zz_media_fault`, which stops LiveKit, and timed out joining. It is renamed to `zz_l_room.spec.ts` so that it runs before the fault test.

## Tests

- **Backend: 15 new tests.**
  - `test_room.py` (9):
    - nothing is processed before the disclosure and everyone's agreement;
    - a decline keeps Vene off, and a new arrival closes the gate and bumps the epoch;
    - room changes pause the call and close `voice.gate`;
    - renaming a voice corrects sources and invalidates interpretations;
    - an attributed clinician cannot confirm or order (403, and no order is sent);
    - Vene hearing itself is dropped while other speech is kept;
    - guests receive state only;
    - live room turns from the patient's device carry their label;
    - per-speaker finalization in the Deepgram sink.
  - `test_dial.py` (6):
    - only the patient issues PINs; they are hashed, replaced and single-use;
    - the bridge must authenticate and caller ID is never identity;
    - an expired PIN or an unstarted conversation is refused;
    - keypad consent, pause and patient-only resume;
    - withdrawing access disconnects the caller, including from the room sync;
    - a revoked PIN invalidates an admitted phone connection.
- **Mutation checks:** each of these makes a test fail: the gate always open; no self-speech guard; renaming without invalidation; anyone can resume by keypad; a revoked PIN ignored.
- **Browser (`zz_l_room.spec.ts`).** A 390 px phone with a fake microphone joins a **real local WebRTC call**:
  - room speech is refused (409) before agreement, and "Agreed" is disabled before the disclosure;
  - after everyone agrees, the patient joins, agrees and resumes, and the call becomes active;
  - fictional room speech arrives as "Unattributed speaker 1"; naming it gives Dr. Chris Chen, patient-attested, version 2;
  - the clinician's browser sees only the room-mode note, and its payload has no people or speakers;
  - "Someone arrived" pauses the call, and resume (409) and room speech (409) are refused;
  - no horizontal overflow; a PIN is issued in preparation; no page errors.

## Final verification

`bash scripts/check.sh --all` on Linux, 19 October, third full run (`.local/logs/check-all-phase12c.log`), exit 0:

- 201 backend tests passed.
- Browser: 29 passed, 4 skipped. The skips are the existing explicit live and timing gates.
- Phase 10 latency p95: turn to obstacle 1,019 ms, source to cue 903 ms.
- Contracts, TypeScript and the production build passed.

The first two runs failed on defects 3–5 above. All three were fixed and none was retried away.

## Not done or not verified

- **Real diarization accuracy.** No live Deepgram run on mixed two-voice audio happened here (the provider keys live only in the user's ignored `.env` on Windows). The labelled path is verified with fixture input and a unit test of the sink.
- **Physical acoustics.** No real phone on a real table: echo, distance and cross-talk are unverified. The 60% repeat threshold for self-speech is a starting point, not a tuned value.
- **Real telephony.** No SIP trunk, Twilio credentials or test number were available, so no call was placed. The bridge's lobby, PIN collection and participant move, and bridge-side brute-force limits, are not implemented here and are documented as a contract in docs/INTEGRATION.md. Spoken keypad confirmations are returned as text and are not yet played to the caller.
- **Patient-only phone line.** When the patient joins only by phone and has no screen, the plan's "agreed spoken mode replaces private cues" is not implemented.
- **Platforms.** Windows and macOS were not re-run.
