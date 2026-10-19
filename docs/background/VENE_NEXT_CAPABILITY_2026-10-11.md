**Vene's next capability: Bring Vene**

Update, 12 October: the user accepted this direction and clarified that they want an ambitious implementation, not a minimal-agent restriction. The implementation recommendation below is historical. The current build design is in BRING_VENE_BUILD_BLUEPRINT_2026-10-12.md, with repository diligence in BRING_VENE_REPO_AUDIT_2026-10-12.md.

Research date: 11 October 2026. A proposed additive feature, not a built product or statement about Vene's private roadmap. This supersedes CareDays as the recommendation for the user's revised brief. No real healthcare calls were made and no patients or founders were contacted.

**The recommendation**

Bring your existing Vene assistant into a healthcare conversation so it can help you communicate what matters, get your questions answered, and carry the agreed next steps into follow-through.

The patient-facing request is: “Vene, come with me to this conversation.”

The new capability is participation in a conversation between the patient and another person. Its core contribution is making the patient's approved context available while questions can still be answered. The implementation should start with one agent, existing voice infrastructure and a small set of tools.

This is a stronger answer to a V3/V4 extension brief than another arrangement of existing scheduling tools. It is not established as more profitable, easier to adopt, or absent from Vene's private roadmap. V3/V4 are planning labels; the exact current product version is unverified.

**Why the company context points here**

Vene already describes personal history, record access, proactive contact, approved errands and family communication. Its consumer offering explicitly says clinicians need no new account. Its organization offering keeps clinical decisions with named staff. The feature should extend those assets into an invited conversation and return administrative work to the existing assistant. [Consumer](https://www.venehealth.com/consumer), [Organizations](https://www.venehealth.com/for-care-organizations).

The opportunity is a hypothesis: information from different providers and home conversations may be useful during a visit, yet the patient or caregiver often has to carry that context into the room and carry instructions back out. Having a summary available does not guarantee that a question gets asked or an unclear instruction gets clarified.

Vene's family mission makes the interaction especially relevant when a relative cannot attend. It would support communication; it would not replace physical assistance, a qualified interpreter, a clinician or a legally authorized decision maker.

**A concrete fictional experience**

Maria has a follow-up conversation with a clinician. Her daughter cannot join. Maria has already told Vene that a requested prescription has not reached her pharmacy and that she wants to ask where and when to complete a lab visit.

Before the encounter, Maria chooses those two questions and the facts Vene may share. Optional family suggestions remain suggestions until the patient or appropriate authorized decision maker approves them. The whole longitudinal record is not automatically exposed.

At the start, participants are told that Vene is AI, that it will process the conversation and retain the agreed transcript, and how to stop it. Participation requires their agreement. A refusal ends the live feature; preparation and ordinary follow-up remain possible.

During the conversation, Vene is quiet by default. Maria says, “Vene, help me ask what we discussed.” It briefly raises her approved questions. It can supply source-attributed factual context when requested. It does not answer clinical questions directed at Maria, choose treatment, or challenge the clinician with generated medical advice.

At a participant-invited closeout, it can clarify a practical ambiguity: “For the follow-up you requested, should the lab be completed beforehand, and which office is arranging the order?” The clinician supplies the answer. The system preserves the distinction between an utterance, an understood instruction, and a signed order required to act.

After the encounter, Maria approves the administrative errands. Vene requests any required confirmation, contacts the pharmacy or office, books what is actually authorized, and updates the chosen family member. A proposed action, submitted request and confirmed result remain distinct.

The meaningful outcome is that Maria's priorities were discussed and the next steps were clarified before the conversation ended. A transcript alone is not that outcome. This scenario is illustrative and is not evidence of reduced errors or clinical benefit.

**Why a simpler agent is the right implementation**

The user correctly rejected complexity as a selling point. A general model with permitted live audio, the right patient context and existing tools may implement most of this feature. That is desirable. Do not build a multi-agent hierarchy, new foundation model or speech stack to make it appear technically difficult.

There are two separate comparisons:

1. Product value: does invited live support help more than good visit preparation, a question checklist, a passive transcript and ordinary after-visit follow-up?
2. Implementation value: given the live feature, does extra machinery improve it beyond a single well-prompted agent and simple controls?

The first must be tested. For the second, prefer the simpler system unless a concrete failure justifies more. The feature adds a usable interaction and access to a live event; it is not an argument that ordinary models are incapable of understanding a transcript.

**What research supports—and does not support**

A 2026 scoping review included 46 empirical studies of older patients and informal companions. It describes roles spanning preparation, in-visit communication and subsequent care. In-visit effects were mixed. This supports the importance of the communication task and warns that an extra participant can also harm the experience. It is not evidence that AI can replace companions or improve health outcomes. [Guo et al., published online May 2026, September issue](https://pubmed.ncbi.nlm.nih.gov/42224912/).

A 2024 interview study involved 25 patients and 22 physicians. Participants saw possible value in digital consultation support, but roughly two-thirds of the physicians rejected the proposed communicative digital expert. The concept included a more expert-like role than the bounded feature proposed here; the sample is not representative. This is material negative evidence. It motivates patient-invited speech and a restrained role, but does not prove those design choices solve acceptance. [Färber et al.](https://humanfactors.jmir.org/2024/1/e49647/).

No AI outcome trial found in this round establishes the benefits of this specific proposal. The first proof should concern communication quality, patient control and workflow completion, not hospitalizations, adherence or clinical safety claims.

**Competition and novelty**

MedsBuddy's July 2026 OpenAI Build Week submission is a close precedent. Its author describes preparation, speaking through the phone after patient and doctor consent, and post-visit summaries. The event has ended; the submission is not evidence of winning or clinical validation. Its linked repository, dande10/patient-advocate, returned 404 through GitHub for both repository metadata and its tree. Its implementation and license could not be verified. Do not claim source reuse or that its advertised behavior was independently tested. [Submission](https://devpost.com/software/medsbuddy-ai-patient-advocate-n59jzr), [Event](https://openai.devpost.com/).

The MedsBuddy public product page describes visit organization and capture, with store links forthcoming when checked. That establishes close product overlap. Bring Vene is not the invention of a patient-side AI companion. The tailored contribution would be connecting participation to Vene's existing longitudinal context and approved execution. Whether competing implementations already do this well remains uncertain. [Product page](https://www.medsbuddy.app/).

The previous round discarded in-visit help too quickly on crowdedness and adoption difficulty. Under the revised criterion—an additional capability within Vene—existing examples support plausibility while limiting novelty. The adoption objection still stands and must not be disguised with a new name.

**What the non-English search contributed**

Google Japan's October 6, 2026 announcement describes Gemini Live visual assistance for older adults, including camera guidance and reading small print. It explicitly separates text assistance from diagnosis or medication guidance. This demonstrates a useful interaction principle: reduce the amount a person must describe or type. It also makes a generic camera assistant a weak originality claim. [Japanese announcement](https://blog.google/intl/ja-jp/company-news/technology/simpleguide/).

Ant's Chinese-language announcements and Afu listings show that multimodal questions, personal/family records and care services are already being combined. The transferable lesson is a familiar assistant spanning several moments of care. Their institutional connections, clinical claims and Chinese service ecosystem cannot be assumed available to a US startup. Afu is competition/context, not proof that this proposal is unprecedented. [Ant's December 2025 release](https://www.antgroup.com/news-media/press-releases/1765785600000).

The current Japanese/Korean/Chinese searches did not uncover a uniquely superior feature to import. They were used to challenge assumptions, not to choose an idea by geography. The strongest direct warning about consultation acceptance came from the Swiss interview study above.

**Other capability extensions considered**

| Candidate | Actual additional capability | Judgment |
|---|---|---|
| Bring Vene | The patient invites the assistant into a live healthcare conversation with approved context and questions. | Recommend for a narrow, independently demonstrable product prototype. |
| Show Vene | The patient shows items or documents at home, allowing the assistant to collect observable context and arrange appropriate help. | Strong runner-up. A visual inventory for pharmacist review is concrete, but general visual assistance already exists and medication interpretation must remain with professionals. |
| Clinician-delegated care routines | A care team directly configures a reviewed sequence of patient outreach and administrative actions. | Useful, but too close to the programs and configured trackers Vene already describes to be the headline addition. |

For Show Vene, a pharmacist-led video medication-management protocol describes patients showing medications and explaining their use at home. It establishes a real workflow, not AI efficacy; it is a trial protocol rather than completed outcome evidence. A separate 2026 usability pilot involved study-supported setup and in-home assistance, warning against assuming every older patient can use a camera independently. [Protocol](https://pmc.ncbi.nlm.nih.gov/articles/PMC11840363/), [Usability study](https://www.sciencedirect.com/org/science/article/pii/S2561326X26005974).

CareDays, CareCommit and recovery mechanisms operate mainly on errands already inside Vene's advertised scope. Bring Vene changes where the assistant can help. That is the basis for the changed recommendation; no head-to-head product test has been run.

**A feasible initial build**

Start with an explicitly invited, scheduled healthcare conversation hosted through the prototype. Use separate browser or telephone participants. Do not promise arbitrary capture of an existing iPhone call, automatic entry into any telehealth platform, or reliable speaker authentication from a shared microphone.

The patient flow has four small surfaces: invite Vene, approve the questions/context, control its participation, review proposed follow-through. Voice remains the primary interaction. Secure browser links are compatible with Vene's current public model; this does not establish that every older adult can use the new flow unaided.

Implementation:

- Session service: participant admission, disclosed processing, consent and immediate mute/leave controls.
- Context package: only patient-approved, relevant facts and questions, retaining sources and whether a fact is a patient report or an imported record.
- One conversational agent: listens to the allowed tracks, responds when invited and can run a requested closeout. No automatic clinical decisions or unsolicited medical debate.
- Question state: answered, partly answered, deferred or still open, with the relevant utterance. Do not treat a vague mention as a complete answer.
- Existing errand interface: return approved administrative task drafts to a sandbox equivalent of Vene's executor. Medication changes and orders require the responsible clinician's instructions and normal verification.

Vene's privacy policy lists LiveKit and Twilio, so an adapter built on that ecosystem is plausible. It is not a guarantee of plug-and-play integration. Preserve the policy's no-stored-audio design for the prototype; transcript handling and access remain explicit. [Privacy policy](https://www.venehealth.com/privacy).

**Open-source implementation inspected**

LiveKit Agents commit `e7d4cf20804e1faf3867878976dcaf1750a07d1c` was resolved through the commits API. Apache-2.0 license read. Source was inspected, not executed.

- `multi-user-transcriber.py` creates a transcription session for each remote participant identity, disables generated audio and raises StopResponse after a transcript. It provides a concrete pattern for keeping different audio tracks attributable; it is not a patient advocate.
- `warm_transfer.py` calls the library's warm-transfer task using SIP. `support_agent.py` shows the AI handing over and shutting down while the human participants remain. That is useful transport reference, not an implementation of an AI staying as a supporting participant.
- The multi-user translation example was also inspected as a routing reference. It is not a validated medical interpretation service and is excluded from the initial feature.

Current LiveKit documentation says an ordinary AgentSession links to one participant at a time. Multiple people in a room therefore do not automatically produce a correctly attributed multi-party agent. Use per-track transcription into a shared, source-labeled context or a suitable custom media path. On one shared microphone, speaker diarization is not identity verification; ask when attribution is uncertain. [Participant documentation](https://docs.livekit.io/intro/basics/rooms-participants-tracks/participants/).

Pinned source: [Multi-user transcriber](https://github.com/livekit/agents/blob/e7d4cf20804e1faf3867878976dcaf1750a07d1c/examples/other/transcription/multi-user-transcriber.py), [Warm transfer](https://github.com/livekit/agents/blob/e7d4cf20804e1faf3867878976dcaf1750a07d1c/examples/warm-transfer/warm_transfer.py), [Support agent](https://github.com/livekit/agents/blob/e7d4cf20804e1faf3867878976dcaf1750a07d1c/examples/warm-transfer/support_agent.py).

Copies of those three code files and the license are saved in research/v3-sources with a manifest. No proprietary code, patient data or hospital access is needed for the independent demonstration.

**The founder demonstration**

Use a fictional patient, synthetic history, a consenting actor as the clinician, and explicit sandbox services. The founder can play either human role or introduce a new statement. The demo is not a clinical encounter.

1. Show the patient's approved priorities and a separate piece of history that must remain private.
2. Start a conversation with the patient, clinician and disclosed AI participant. Let the humans talk normally while Vene stays quiet.
3. The patient asks Vene to help raise a question. It uses the correct approved context and briefly asks it.
4. The clinician gives an incomplete administrative instruction. At the requested closeout, Vene asks for the missing detail and preserves the clinician's correction.
5. The patient changes their mind about sharing or an errand. The prototype respects that immediately.
6. After the call, the approved administrative work actually executes against the independent sandbox. Show the resulting receipt or open blocker, with an update for the authorized family member.

The strongest moment is an unanticipated human correction handled accurately and followed by appropriate action. Do not script both sides into agreement, label simulation as production, or demonstrate medication decisions made by the assistant.

**What could disprove the recommendation**

- Patients or clinicians do not want an AI participant even when it is invited and quiet.
- A prepared question list plus passive transcription gives equivalent benefit with less friction.
- Speech attribution, latency or interruptions make the conversation worse.
- The feature exposes context the patient did not intend to share, or gives undue authority to generated summaries.
- Clinical confirmation creates more work than the administrative assistance removes.
- Vene already has this experience or its near-term bottleneck lies elsewhere.

Measure patient-priority questions answered, unsupported factual statements, unwanted interruptions, patient control, encounter duration, subsequent clarification contacts and approved errands actually completed. Include the cases where silence, refusal or human follow-up is the right outcome. The benchmark is a supporting validation activity, not the product being pitched.

**Release-shaped scope**

First capability: one invited conversation with approved context, patient-controlled participation and a reliable return to errands.

Later expansion, if that interaction is wanted: additional accepted call/visit surfaces and optional invited family participation. Visual input may be a separate subsequent feature; do not combine camera assistance, clinical interpretation and multi-party calls in the first build.

The proposed promise is modest enough to be useful and specific enough to demonstrate: Vene can accompany the patient into the conversation where care instructions are discussed, then help carry out the approved administrative steps. The recommendation is for testing this capability, not a claim that founders cannot reject it.
