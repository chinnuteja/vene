# Consent-gated voice worker

The executable worker lives in the shared backend package at services/backend/src/bring_vene/voice so transport, fixtures, live STT and domain authorization use the same services.

Run python -m bring_vene.voice.worker with DATABASE_URL, LIVEKIT_URL, LIVEKIT_API_KEY and LIVEKIT_API_SECRET. The project launcher supplies the local values and owns the worker process. setup-media.ps1 installs the pinned official Windows LiveKit server.

Fixture mode processes original tones through real WebRTC and records source/epoch/count evidence. It does not fabricate a transcript. Explicit live mode uses the Deepgram adapter and requires the project's DEEPGRAM_API_KEY. No provider error becomes fixture success.

Each human token is a signed, session-bound listen-only admission. The RTC supervisor validates the current admission before granting microphone publication. Human subscription permission is issued by the authenticated backend, never by a URL role or browser metadata. Vene's own audio subscription and AudioStream exist only after all present humans agree and Maria resumes processing. A new source or arrival pauses processing. Pending starts, audio tasks and provider readers are cancelled before the worker acknowledges a pause; no buffered audio is drained after pause.

Final STT callbacks are re-authorized against membership, connection, room generation, track epoch and consent epoch before persistence. Raw audio is not recorded. There is no shared transcript publisher or ordinary transcript logger. Membership withdrawal ends the active room generation; only Maria can reopen an ended conversation.

The adapted lifecycle structure and Apache-2.0 attribution are recorded in reuse-manifest.json and the included voice/licenses directory. Live STT accuracy and physical microphone acoustics are separate verification gates.


