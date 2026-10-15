# Bring Vene — repository audit and reuse decision

Checked: 12 October 2026. Companion to BRING_VENE_BUILD_BLUEPRINT_2026-10-12.md.

Method: public repository metadata, selected source, READMEs, root licenses and current official documentation. Commit IDs were resolved through the commits API. Code was inspected, not installed or run. This is targeted diligence, not a full security, dependency-license or runtime audit.

Sixteen permitted source/license snapshots are stored under research/bring-vene-sources. The manifest records upstream paths, commits and local SHA-256 values. These are research references, not a runnable application.

## The decision

**Build on LiveKit Agents and LiveKit's React components. Use LiveKit Meet as the multiparty room reference.**

Reuse transport, device handling, audio pipelines, participant lifecycle hooks and basic media UI. Build the patient context rules, participation policy, evolving visit plan and authorized action handoff ourselves.

Do not fork a complete patient assistant just to get visit preparation. That would add a second record store, permissions model and product architecture beside the one Vene already has.

## Comparison

| Project | Inspection depth | Actual useful contribution | Decision |
|---|---|---|---|
| LiveKit Agents | Source, root license, session documentation | Per-participant transcription pattern; voice pipeline; room I/O | Primary backend foundation |
| LiveKit Meet | Room page and token route source, README, license | Multiparty room and pre-join/device patterns | Frontend reference/base; replace admission code |
| LiveKit Agent Starter React | Token route and provider source, README, license | Voice UI/provider patterns | Selective reuse, not a second app |
| Pipecat | Turn strategy source, Daily transport excerpts, README, license | Explicit turn strategies and per-user audio support | Strong alternative; useful design reference |
| Vexa | TTS playback, bot entrypoint/orchestrator excerpts, README, license, current docs | Meeting join/capture; partial speaking plumbing | Later transport experiment; current API cannot deliver complete experience |
| TEN Framework | Example READMEs, directory listing, root license | Diarization and voice-companion examples | Research reference; no foundation switch |
| PRESENT | README, tree and metadata | Earlier voice/collaborative-canvas concept | Inspiration only; default product has changed; no root reuse license found |
| HealthSteward | README, metadata and root license | Longitudinal context and visit-preparation product reference | Related work; no source reuse recommendation |
| HealthAdvocate | README and root license | Patient-facing explanation and preparation reference | Related work; clinical scope differs; no source reuse recommendation |
| MP-Bench | Paper, README and license | Multiparty attribution/turn-taking evaluation design | Research reference; no commercial reuse or training assumed |

None of these projects was verified as an implemented, drop-in Bring Vene product.

## 1. LiveKit Agents

Repository: https://github.com/livekit/agents  
Commit: `b58e83f5c77d5b4bd4c8586793885151a91c4c83`  
Root license: Apache-2.0.

Inspected:

- [multi-user-transcriber.py](https://github.com/livekit/agents/blob/b58e83f5c77d5b4bd4c8586793885151a91c4c83/examples/other/transcription/multi-user-transcriber.py)
- [room_io/types.py](https://github.com/livekit/agents/blob/b58e83f5c77d5b4bd4c8586793885151a91c4c83/livekit-agents/livekit/agents/voice/room_io/types.py)
- [room_io/_output.py](https://github.com/livekit/agents/blob/b58e83f5c77d5b4bd4c8586793885151a91c4c83/livekit-agents/livekit/agents/voice/room_io/_output.py)
- [License](https://github.com/livekit/agents/blob/b58e83f5c77d5b4bd4c8586793885151a91c4c83/LICENSE)

The transcription example creates an AgentSession for each remote participant identity, disables its audio output and stops generation after collecting text. This is useful infrastructure for a shared encounter stream. It does not provide the encounter reasoning, consent, selective disclosure or one coordinated speaking agent.

Important changes before reuse:

1. The example logs transcript contents. Remove that from ordinary logging.
2. It enables text output. Our transcript delivery must be audience-scoped.
3. The legacy transcription publisher in room I/O has no destination parameter. Do not use broadcast transcription for patient-private material.
4. The example's disconnect handler uses dictionary `pop` without a default, while session creation is asynchronous. A departure during startup needs an explicit cancellation/lifecycle design. Duplicate startup and a late startup completion also need handling. These are source-level concerns, not reproduced runtime results.
5. AgentSession's ordinary participant linking is one participant at a time. Multiple humans in a room require deliberate input routing, not merely a longer system prompt.

Use the example as a pattern, with a supervised track lifecycle and a shared event service. Retain a single public output path with explicit speech cancellation.

## 2. LiveKit Meet

Repository: https://github.com/livekit-examples/meet  
Commit: `13e4fd88d6f3c238060746a8f476e32af5c97fbf`  
Root license: Apache-2.0.

[Room implementation](https://github.com/livekit-examples/meet/blob/13e4fd88d6f3c238060746a8f476e32af5c97fbf/app/rooms/%5BroomName%5D/PageClientImpl.tsx), [connection route](https://github.com/livekit-examples/meet/blob/13e4fd88d6f3c238060746a8f476e32af5c97fbf/app/api/connection-details/route.ts), [license](https://github.com/livekit-examples/meet/blob/13e4fd88d6f3c238060746a8f476e32af5c97fbf/LICENSE).

The room page uses LiveKit's PreJoin, RoomContext and VideoConference components with device and connection handling. These are valuable starting points for two humans and a visible AI participant.

The example connection endpoint takes the room name, participant name and metadata from request parameters and creates a participant token. It is not a healthcare admission system. Replace it with server-authorized encounter membership, scoped invitations and server-assigned roles. Never treat a client-supplied name or metadata field as verified identity.

Build a calm patient view around these components. Do not ship a generic video-conference dashboard as the product. Camera can be optional; the useful content is the voice interaction and the small visit card.

The example includes encryption-related UI. Do not inherit a broad “end-to-end private” promise without accounting for the AI processing endpoint and the actual key/trust model.

## 3. LiveKit Agent Starter React

Repository: https://github.com/livekit-examples/agent-starter-react  
Commit: `c5d78a6c381a0ac80b081cf6aeb8ac454d00ca78`  
Root license: MIT.

[Token endpoint](https://github.com/livekit-examples/agent-starter-react/blob/c5d78a6c381a0ac80b081cf6aeb8ac454d00ca78/app/api/token/route.ts), [session provider](https://github.com/livekit-examples/agent-starter-react/blob/c5d78a6c381a0ac80b081cf6aeb8ac454d00ca78/components/agents-ui/agent-session-provider.tsx), [license](https://github.com/livekit-examples/agent-starter-react/blob/c5d78a6c381a0ac80b081cf6aeb8ac454d00ca78/LICENSE).

The provider composes session context and room audio rendering. The token endpoint explicitly rejects ordinary production use without a new authentication layer. The README also explains that its default app connects to a public example agent.

Useful for voice controls, component conventions and a private preparation interaction. It is not already the multiparty patient/clinician experience. Do not point real context at the default example agent.

## 4. Pipecat

Repository: https://github.com/pipecat-ai/pipecat  
Commit: `19fca83d2e2336b7c82145fe66b7b1cc76e44ac9`  
Root license: BSD-2-Clause.

[External turn strategy example](https://github.com/pipecat-ai/pipecat/blob/19fca83d2e2336b7c82145fe66b7b1cc76e44ac9/examples/turn-management/turn-management-custom-external-turn-strategy.py), [wake-phrase strategy](https://github.com/pipecat-ai/pipecat/blob/19fca83d2e2336b7c82145fe66b7b1cc76e44ac9/src/pipecat/turns/user_start/wake_phrase_user_turn_start_strategy.py), [Daily transport](https://github.com/pipecat-ai/pipecat/blob/19fca83d2e2336b7c82145fe66b7b1cc76e44ac9/src/pipecat/transports/daily/transport.py), [license](https://github.com/pipecat-ai/pipecat/blob/19fca83d2e2336b7c82145fe66b7b1cc76e44ac9/LICENSE).

The custom stop strategy delays a proposed end of turn and cancels that delay when speech resumes. It provides a concrete pattern for avoiding a response before an afterthought, with an explicit latency cost.

The wake-phrase strategy gates interaction and resets accumulated context for non-matching input while idle. That is not directly appropriate for Bring Vene's “listen with permission but speak selectively” mode: the observer must retain permitted context even when the public speaker is quiet. Preserve separate observation and speaking paths.

Daily transport supports per-user audio tracks and participant-addressed messages. That establishes useful routing support; it does not by itself give an application permission or correct multiparty reasoning.

Pipecat is a credible alternative. Switching from a framework Vene already discloses has no demonstrated advantage here, and running two voice frameworks in the first build would add integration work.

## 5. Vexa

Repository: https://github.com/Vexa-ai/vexa  
Commit: `f1a62fbbdfd2c98cb162582d82c31fe8102acc89`  
Root license: Apache-2.0.

[TTS playback](https://github.com/Vexa-ai/vexa/blob/f1a62fbbdfd2c98cb162582d82c31fe8102acc89/core/meetings/services/bot/src/tts-playback.ts), [bot entrypoint](https://github.com/Vexa-ai/vexa/blob/f1a62fbbdfd2c98cb162582d82c31fe8102acc89/core/meetings/services/bot/src/index.ts), [license](https://github.com/Vexa-ai/vexa/blob/f1a62fbbdfd2c98cb162582d82c31fe8102acc89/LICENSE).

The project supplies bots for established meeting platforms and attributed transcripts. Its bot entrypoint routes speak/stop actions to a speaker controller. The playback implementation requests speech and streams PCM into a virtual microphone using system audio tools.

This is more than an empty method, but it is not sufficient evidence of a usable integration:

- Missing TTS configuration makes speech a no-op in the inspected playback function.
- Errors can log and resolve without successful speech.
- Current official 0.12 documentation says speaking, chat write, screen sharing and avatar functions are not reachable through the public API; speaking is described as proven at the bot layer but not API-wired. [Current interactive-bot status](https://docs.vexa.ai/interactive-bots).
- Meeting admission, host permission, platform changes and retention behavior need separate validation.
- Its general meeting/knowledge architecture should not be copied wholesale into a patient product.

Use only as an isolated later adapter experiment. The initial demonstration should not depend on an API the current documentation says returns 404.

## 6. TEN Framework

Repository: https://github.com/TEN-framework/ten-framework  
Commit: `c6cbeebbf9a3fb6a3f9ed245359d72c792840d00`.

[License](https://github.com/TEN-framework/ten-framework/blob/c6cbeebbf9a3fb6a3f9ed245359d72c792840d00/LICENSE), [diarization example](https://github.com/TEN-framework/ten-framework/tree/c6cbeebbf9a3fb6a3f9ed245359d72c792840d00/ai_agents/agents/examples/speaker-diarization), [companion example](https://github.com/TEN-framework/ten-framework/tree/c6cbeebbf9a3fb6a3f9ed245359d72c792840d00/ai_agents/agents/examples/voice-assistant-companion).

The diarization README describes Speechmatics-based speaker labels, and explicitly notes that some advertised sensitivity settings are not supported by its pinned provider version. The companion example uses provider models and an Agora transport graph. We inspected these descriptions, not the complete extension implementations.

The root license is Apache-based **with added conditions**, including restrictions on end-user-device hosting and deployments competing with Agora's offerings. It is not standard Apache-2.0. This does not mean every commercial application is forbidden; it means “Apache, freely interchangeable with LiveKit” would be an inaccurate description.

The examples are useful references. No unique capability here justifies moving Vene to a new transport foundation for this feature.

## 7. Related patient products and interaction references

**MedsBuddy:** the previous round found a close patient-side live visit companion. The linked repository was unavailable then; this audit did not establish new access. It supports acknowledging product precedent, not source reuse. [Submission](https://devpost.com/software/medsbuddy-ai-patient-advocate-n59jzr).

**PRESENT**, commit `44af55e5d3c1f7eb49f72a92494f29798520d428`: the current README says the default product is now a workspace/mission-control shell and its LiveKit collaborative-canvas experience is an archived appendix. No root license was found in the inspected tree/metadata. A vendor subdirectory license does not license the whole repository. Use the idea of a visible, editable conversation artifact as inspiration; no code reuse recommended. [Repository](https://github.com/human-bee/PRESENT).

**HealthSteward**, commit `0f0b4baca54c537869b518995ee6a7b24f6debb8`: README describes local records, visit preparation, pending work and document parsing. Root license is GPL-3.0. This is adjacent product work; its implementation was not audited. It does not establish a live multiparty foundation, and no code reuse is recommended. [Repository](https://github.com/nidhi-menon/HealthSteward).

**HealthAdvocate**, commit `efbe95b75a0c1f7b98becc18f613236b3d823ab1`: README describes preparation and administrative help alongside symptom/urgency features beyond Bring Vene's scope. The README displays an Apache badge, while the inspected root LICENSE says MIT. Record the discrepancy rather than copying the badge into a diligence report. No code reuse recommendation follows from this README-only product inspection. [Repository](https://github.com/simongonzalezdc/healthadvocate).

## 8. Research artifacts, not runtime dependencies

**MP-Bench**, commit `44da1feca5e87ade5c1ac46e52b1d9cdb7a6a61a`: its README and license specify CC BY-NC 4.0, evaluation-only use and no model training. Do not put its tasks into a commercial product or training set on the assumption it is permissively licensed. We use its published evaluation dimensions to inform original synthetic cases; no dataset or code was imported. [Repository and license](https://github.com/atosystem/MP-Bench).

**When2Speak:** the paper describes a synthetic participation-timing dataset and training pipeline. The relevant implementation/data license was not audited. It is a research lead, not an approved dependency. [Paper](https://arxiv.org/abs/2605.05626).

**ModeratorLM:** a role-conditioned multiparty turn-taking paper. Its result concerns research settings, not healthcare deployment. No implementation or model weights were verified for this build. [Paper](https://arxiv.org/abs/2606.13544).

## What we reuse and what we invent

Reuse the media substrate and replaceable models. Integrate with Vene's existing memory and errands through proposed adapters rather than rebuilding them.

The new application work is:

1. Purpose-scoped context for each encounter and audience.
2. Patient-controlled, context-aware participation.
3. A continuously updated, evidence-linked visit plan.
4. A practical check that can inform the conversation while participants are present.
5. Correction-aware authorization and handoff into existing execution.
6. Continuity into the next conversation without indiscriminate transcript sharing.

The competitive value, if demonstrated, is the quality of this experience and its integration. It is not exclusive ownership of voice transport, a claim to have invented visit companions, or a guarantee of founder adoption.

