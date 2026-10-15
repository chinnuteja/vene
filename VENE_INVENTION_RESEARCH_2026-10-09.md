**Vene: independent research, candidate selection, and falsification plan**

Research date: 9 October 2026. Purpose: identify a useful contribution a founding-engineer candidate can build without Vene's private code, patient data, or further founder conversations.

**Decision**

My first build-and-test choice is **action-aware speech repair**: a component that notices when uncertainty about what was said could change an approved care action, obtains better evidence or asks one targeted question, and keeps the affected action pending until the ambiguity is resolved.

The intended result is fewer incorrect care actions at an acceptable level of patient effort, latency, and operating cost. It is an empirical engineering bet. No experiment in this research establishes an improvement on Vene's actual implementation. No public source establishes that Vene lacks an equivalent component.

The three surviving opportunities are:

| Rank | Concrete contribution | Why retain it | What could make it unnecessary |
|---|---|---|---|
| 1 | Resolve speech ambiguity before it changes a care action | A bounded component, an independently testable input problem, accessible implementation building blocks, and a result a founder can hear and inspect | Current speech services plus ordinary confirmations may already perform as well |
| 2 | Acquire missing information from the right person or organization with fewer patient interruptions | Fits the administrative burden Vene is trying to remove; works in both text and voice | A strong prompted agent with the same tools may route questions equally well |
| 3 | Recheck pending actions when the evidence supporting them changes | Relevant to longitudinal records and asynchronous care errands | Vene already separates reported facts from records, uses Zep, and may implement this; ordinary version checks and event handling may suffice |

These survive as testable opportunities, not established product gaps. The first is my personal allocation-of-effort choice because it can be falsified with actual speech and observable action outcomes, without inventing a simulated healthcare bureaucracy that rewards our own planner.

**What I verified about Vene**

Vene's public workflow covers records, conversations, proactive outreach, and patient-approved errands involving offices, pharmacies, and health plans. Medical decisions remain with clinicians. [How Vene works](https://www.venehealth.com/how-vene-works)

Its terms already describe separate storage of patient-reported facts and imported records, scoped permission, callbacks, and care-circle roles. Generic provenance, consent, refill tracking, and callback handling are therefore weak novelty claims. Voice audio is not recorded or stored under the published terms. [Terms](https://www.venehealth.com/terms)

Its disclosed suppliers include LiveKit, Deepgram for patient speech recognition, Cartesia for patient speech synthesis, ElevenLabs for third-party call speech, Zep for memory, and PostHog for observability. Those disclosures do not reveal configurations, versions, internal checks, traffic mix, or error rates. [Privacy policy](https://www.venehealth.com/privacy)

The website establishes strategic fit; it cannot establish the founders' current bottleneck. I have not treated the reported pivot date, accelerator status, or an old public changelog as proof of what their engineers have or have not built.

Forge and CareCommit's outcomes are user-reported experiments. I did not have their implementations or reproduce them. Their lesson governs this recommendation: a sophisticated design must beat a capable conventional implementation, or earn its place through measured cost or user-effort improvements.

**What the wider research eliminated**

| Direction examined | Decision and reason |
|---|---|
| Generic recovery engine / cross-organization planner | Do not revive without a new measured failure. The reported Forge and CareCommit results directly weaken this pitch. |
| Another elder companion, reminder, tracker, or caregiver dashboard | Already central to Vene or common in the projects reviewed. |
| General longitudinal patient memory | Vene already uses memory infrastructure; a new graph is not a contribution by itself. |
| Generic voice testing / patient simulation | Useful supporting infrastructure, but crowded and increasingly available from suppliers. |
| Adaptive pauses and interruptions for older speakers | Current LiveKit supports semantic turn detection, dynamic endpointing, and adaptive interruptions. Test configuration first. |
| Automatic medical terminology replacement | Both vendor keyterm prompting and small open-source projects already do contextual correction; replacement can also corrupt correctly heard unfamiliar information. |
| AI medication reconciliation that chooses the correct regimen | Clinical decisions exceed Vene's stated boundary. Evidence collection for a clinician remains in scope. |
| Voice biomarkers / dementia or emotional-distress diagnosis | Outside the current administrative mission; the reviewed prototypes do not establish clinical validity. |
| Home sensors and appliance monitoring | Requires a different product surface and devices. Useful software mechanisms can be studied without adopting the product. |
| Teach-back as an entire invention | Valuable established practice, but a prompt or workflow can implement the basic loop. No demonstrated special engineering advantage found. |
| Privacy/authorization sidecar as the main pitch | Important, but permission is already explicit in Vene's product. The research reviewed did not establish a distinctive incremental product advantage. |
| Chart-aware previsit intake | Existing hackathon implementations already combine charts, voice, provenance, and review. Broad duplication would not be compelling. |

**Global search and implementation checks**

Native-language searches included Chinese elder medication and contextual speech-correction queries; Japanese elder support, dialogue repair, and hackathon queries; Korean medication, elder voice, and hackathon queries. I followed original repositories and event submissions, rather than treating idea-list pages or search snippets as working products. Repository source checks were targeted static inspections, not comprehensive security audits or executed reproductions.

| Region / source | What was inspected | Mechanism or limitation that affected the decision |
|---|---|---|
| China: [Pills Talk](https://github.com/Andy-cool-blue/yaoshua-pills-talk), TRAE competition submission | Pinned `app/index.html` | `finishPhotoRecognition()` selects a random drug from its local list and generates a confidence display. This is a simulated OCR demonstration, not evidence of working medication recognition. No root project license was found in the inspected tree. |
| China: [ASR-Hotword](https://github.com/HaujetZhao/asr-hotword) | README, license metadata, and pinned `hot_phoneme.py` | Two-stage candidate matching, aliases, and context blacklists. Useful retrieval ideas; forced replacement is unsuitable as a default for care facts. The README's English matching uses letters rather than a full English pronunciation model. MIT. |
| China: [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR) | Official documentation and pinned inference implementation | A practical second recognizer with contextual input. Its streaming path requires vLLM and does not return alignment timestamps. Forced alignment aligns a supplied text; it does not prove that text is correct. Apache-2.0 repository. |
| Japan: [CareRoute AI / 見守り隊](https://github.com/monoqlo78/mimamoritai-careroute-ai) | Submitted-project documentation and pinned `DeviceSafetyPolicy.cs` / `RiskAssessmentService.cs` | Typed permission decisions and checks that distinguish sparse observations from an observed quiet period. Transferable reasoning; the hardware product itself is outside Vene's scope. No root project license found in the inspected tree. |
| Japan: [Hitachi contextual-ASR paper, 25 September 2026](https://arxiv.org/html/2609.30694v1) | Method, experiments, baselines | Select likely error spans, retrieve sound-alike terms, and re-recognize the audio. Supports feasibility of selective repair; does not establish an elder-care or live-call benefit. Numeric-only spans are excluded. No implementation repository was verified. |
| South Korea: [Veteran](https://github.com/uzlnee/Veteran) | Korean documentation and pinned `conversation_logic.py` | A fixed nine-question voice workflow with structured answer validation and retry. Demonstrates how much an ordinary system can do. It does not establish that a learned question router outperforms that baseline. No root project license found in the inspected tree. |
| South Korea: [HiKE](https://github.com/ThetaOne-AI/HiKE) | English/Korean project context, license, and `src/metrics/mer.py` | Code-switch evaluation distinguishes Korean character units from English word units and provides finer labels. A global WER number can conceal relevant language-specific failures. Apache-2.0 code; dataset terms require separate verification. |
| South Korea: [여느날, 2025 SeSAC submission](https://dacon.io/competitions/official/236624/codeshare/13391) | Original dated submission; event page marked closed | Family-call analysis for neurodegenerative risk. Rejected for clinical scope; submission status is not efficacy evidence. |
| South Korea: [MediKonnecT, 2025 K intelligence submission](https://dacon.io/competitions/official/236600/codeshare/13085) | Original dated submission | Medication logs, chat, and appointments demonstrate overlap with obvious ideas. Linked repository retrieval failed; I do not claim a source review. |
| US event: [Prologue](https://github.com/mayu99/prologue-health) | Pinned `lib/intake.ts` / `lib/clinical.ts` | Patient-report versus prescription separation, review gating, FHIR write receipts, and restricted safety-rule locale coverage. This is concrete overlap with generic reconciliation/provenance pitches. No root project license found in the inspected tree. |

Event provenance was checked separately from project quality. The [Medplum organizer recap](https://www2.medplum.com/blog/yc-medplum-hackathon-2026-recap) confirms the August 1, 2026 event completed. Prologue identifies itself as built for that event; that is not a claim it won. CareRoute identifies its August 15 submission freeze. The Korean DACON submissions are dated 2025. Pills Talk has an original competition submission, and the TRAE community has a [finals recap](https://forum.trae.cn/t/topic/178991); I did not verify any award for Pills Talk. Recent ongoing hackathon entries were not counted as completed-event evidence.

**Research findings worth using—and their limits**

1. [WER is Unaware](https://arxiv.org/html/2511.16544v1) studies meaning-changing errors in patient speech, including Deepgram Nova-3 output on mock consultations. Its samples were enriched for errors, so they cannot estimate Vene's real error frequency. The [Ufonia code](https://github.com/Ufonia/wer-is-unaware) is MIT. Its judge explicitly requires a ground-truth transcript: it is an offline evaluator, not a detector that can discover truth during a live call.

2. [Hitachi's September selective-retrieval paper](https://arxiv.org/html/2609.30694v1) reports medical WER of 5.67% versus 5.83% for retrieval over every recognized word, using far fewer dictionary queries. The larger headline gain is against its first-pass recognizer. This is evidence for efficient candidate selection, not evidence that it beats a tuned Deepgram or Scribe deployment. Its medical dictionary is derived from reference transcriptions; test our system with independently available vocabulary instead.

3. [PROUR, 26 September 2026](https://arxiv.org/html/2609.32255v1) distinguishes user-goal ambiguity from missing world evidence, routing between clarification, verification, and action. This suggests a useful source-selection mechanism. However, its tasks are simulated transactional environments; healthcare transfer is untested. Its trained small query generator does not beat every stronger prompted generator. The anonymous code link was inaccessible through the research browser, so code and licensing remain unverified.

4. [MedCache, 30 August 2026](https://arxiv.org/html/2608.29528v1) is relevant to stale records, but its appendix defines a policy-level “Zep” baseline using BM25 over facts and a 20-entry budget. That is not a deployed-Zep comparison. Its main benchmark is small and retrospective. It cannot justify telling Vene their memory vendor is inadequate.

5. [Graphiti's actual implementation](https://github.com/getzep/graphiti/blob/1026ae7ae25e7e4cfcc1c7ebe00347b8a90f52a0/graphiti_core/utils/maintenance/edge_operations.py) already handles candidate contradictions and temporal invalidation. The inspected repository license is Apache-2.0. Public issue reports are useful test ideas, not evidence those bugs exist in Vene's hosted Zep configuration.

6. [The asr-age-gap project](https://github.com/Kayvan-Zahiri/asr-age-gap) explicitly revised its original implication after testing modern turn detection. Its small end-to-end test was inconclusive and underpowered. It does not establish an age-specific problem in Vene. [LiveKit's current options](https://docs.livekit.io/agents/logic/turns/) already include session-adaptive endpointing.

7. [PatientAgentBench](https://github.com/amazon-science/PatientAgentBench) overlaps strongly with a general patient simulator. It uses synthetic conversations and rubric judging. Its published “pass” thresholds should not be mistaken for exact task-state correctness. The repository declares CC BY-NC 4.0, so it is not proposed as a commercial product dependency.

8. [AgentDAM](https://github.com/facebookresearch/ai-agent-privacy) supplies an outside-healthcare lens on task-specific disclosure. Its inspected license is also CC BY-NC 4.0. It informs the privacy candidate's evaluation questions, but is not included as a reusable commercial component.

9. [Cause-aware speech clarification](https://arxiv.org/html/2605.25404v1) investigates error causes and targeted recovery. The study uses English, simulated distortions, automatic evaluation, and no human user validation. It supports an experiment, not a claim of natural or successful conversations with older adults.

Commercial overlap was considered as well: [Assort](https://www.assorthealth.com/blog/building-healthcare-that-remembers) markets persistent patient and operational memory; [Hippocratic AI](https://hippocraticai.com/ai-front-door/) describes care coordination workflows; [Tennr](https://www.tennr.com/) addresses referral/document workflow. These are vendor capability descriptions, not independent comparative evidence. [ElevenLabs testing](https://elevenlabs.io/docs/eleven-agents/customization/agent-testing) and [Hamming's healthcare tests](https://hamming.ai/industry/healthcare) weaken a generic testing-tool pitch.

**Eight-question challenge of the three finalists**

| Challenge | Action-aware speech repair | Source-aware information acquisition | Change-aware action rechecking |
|---|---|---|---|
| Inside scope? | Protects administrative tool calls and reported facts; no diagnosis or medication decisions | Resolves task requirements, preferences, and status using authorized contacts | Revalidates administrative work when its supporting information changes |
| Consequential recurring problem? | Misheard names, negation, corrections, and dates can change an action; Vene frequency unknown | Repeated questions and unnecessary patient investigation create effort; Vene frequency unknown | Stale or conflicting records can outlive a task's original assumptions; Vene frequency unknown |
| Evidence problem exists? | Patient-speech research and public labeled examples | Transactional-agent research; established administrative burden; no Vene-specific measurement | Medication-transition literature and memory research; no Vene-specific measurement |
| What already solves it? | Keyterms, modern ASR, multimodal models, confirmations | Prompted agents, state machines, chart-aware intake, task policies | Zep/Graphiti, version checks, event handlers, reconciliation systems |
| Why not ordinary engineering? | It might suffice. The hypothesis is that action sensitivity improves the error/clarification trade-off | It might suffice. The hypothesis is that explicit source selection reduces real patient effort at equal success | It might suffice. Only messy semantic attribution and selective dependency updates could add value |
| Specific mechanism? | Acoustic alternatives → compare operational meanings → resolve only material uncertainty | Candidate meanings / missing predicates → identify answer owner → choose an informative affordable query | Claims with author/effective/observed times → action dependencies → recheck affected actions |
| Independent demo? | Consenting speakers, fictional tasks, real ASR, mock tools | Scripted institutional endpoints plus consenting people; synthetic validity remains a concern | Synthetic record streams and real FHIR structures; limited evidence of field value |
| Skeptical CTO value? | A small adapter with measured effect and visible costs | A demonstrated reduction in patient contact work, not modeled step count | A narrow tested improvement over their memory/event stack, not a replacement platform |

**Winner: precise product behavior**

A caller says something that is transcribed plausibly but incorrectly. The agent prepares to schedule the wrong date, request the wrong refill, log the wrong reported status, or share information outside the intended request. A fluent response does not expose the mistake.

The overlooked unit of quality is the **care action implied by the speech**. Some transcription differences do not change that action. A single negation or corrected name can. The component evaluates this distinction at the point where a pending action could take effect.

Illustrative fictional call: “The refill is for hydralazine. I don't need hydroxyzine.” An existing medication list makes the second name plausible. The system should use the list as candidate context while preserving the possibility that the caller is introducing or correcting something. It should not silently force the speech to agree with old memory. This example is a test specification, not a measured error from a vendor or Vene.

Start with two administrative tool families: requesting a refill of an existing prescription, and booking/rescheduling within the patient's approved limits. Do not add prescribing, dose recommendations, clinical urgency assessment, or a broad care planner.

**Technical operation**

1. **Observe the current turn and proposed action.** Inputs are the streaming transcript, available word timings, ephemeral audio, narrowly relevant task context, permission constraints, and the pending tool arguments. Keep raw recognition separate from derived interpretation.

2. **Identify the fields that can change this action.** Medication identity, prescription identifier, appointment date, cancellation versus rescheduling, and scope of permission are examples. Check critical fields even when the first recognizer is confident. Confidence alone is not an adequate trigger.

3. **Obtain bounded alternative evidence.** Use an independent recognizer or a targeted second audio pass when warranted. Do not assume the commercial API exposes an N-best list. Retrieve a small vocabulary with source and recency information; retain an open-world “other / unknown” option. The production prescription list is not a closed set of things the patient is allowed to say.

4. **Compare action meanings without executing tools.** Convert supported candidate interpretations into structured task fields. If differences change the tool, a material argument, the person involved, a reported status, or permission, mark the affected field unresolved. Do not let a majority vote manufacture clinical truth. Agreement between recognizers does not prove correctness.

5. **Resolve the smallest remaining ambiguity.** Re-listen if more acoustic evidence may help. Ask a neutral focused question for a patient preference or intended request. For an institution-controlled fact, use the authorized institution or existing record interface. A question such as “Which date would you like?” avoids suggesting that one candidate must be right. Limit repeated clarification and expose unresolved work honestly.

6. **Gate only the affected write.** Return a typed result such as resolved, needs-clarification, or needs-source-verification, with original spans and supporting evidence. Existing authentication, consent, and clinical boundaries still apply. Preserve patient-reported status as reported; an accurate transcript does not independently verify a pickup or ingestion.

The deliverable is a LiveKit-side adapter plus a small pre-tool check and replayable examples. Its visible product effect is a better call. A developer inspection view is useful for the demonstration, but it is not a proposed patient dashboard.

Use transient audio processing with a bounded in-memory buffer and prompt disposal; do not introduce stored patient recordings. Integration must be checked against Vene's actual call architecture and published audio policy. Begin on the patient-facing LiveKit/Deepgram path. Do not assume the third-party ElevenLabs path exposes identical interception points.

**What suppliers already provide, and what would remain ours**

[Deepgram keyterm prompting](https://developers.deepgram.com/docs/keyterm) and [ElevenLabs keyterm prompting](https://elevenlabs.io/docs/eleven-api/guides/how-to/speech-to-text/batch/keyterm-prompting) must be enabled where supported in the baseline. Vocabulary adaptation is not our novelty. Current turn detection and normal tool confirmations belong in the baseline too.

Our proposed specialization is the connection between acoustic uncertainty, the current authorized care action, the patient's changing context, and the least burdensome way to resolve uncertainty. None of those individual ideas is new. I did not establish global novelty for their combination.

The useful contribution would be implementation and measured performance: fewer incorrect actions or fewer necessary interruptions at the same error level, with small integration and operating costs. If the same result comes from better prompts or vendor settings, that simpler change wins.

**Reusable components and licensing**

| Component | Proposed use | Constraint |
|---|---|---|
| [LiveKit Agents](https://github.com/livekit/agents) | Live audio integration and normal turn handling | Framework Apache-2.0; model/plugin/service terms are separate |
| [Qwen3-ASR](https://github.com/QwenLM/Qwen3-ASR) | Candidate independent recognizer / contextual second pass | Repository Apache-2.0; verify selected weight terms and actual latency before choosing it |
| [Ufonia evaluation utilities](https://github.com/Ufonia/wer-is-unaware) | Offline transcript alignment and semantic-error analysis | MIT code; do not pass the ground-truth-dependent judge off as a runtime detector |
| [HiKE evaluation](https://github.com/ThetaOne-AI/HiKE) | Optional Korean-English evaluation methodology | Apache-2.0 code; it is not an elder-care dataset |
| [ASR-Hotword](https://github.com/HaujetZhao/asr-hotword) | Candidate-generation ideas or bounded matching utilities | MIT; forced replacements and its English approximation require scrutiny |
| [RxNorm API](https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html) | Medication-name normalization and candidate identifiers | Public terminology API, not proof of the patient's medication or clinical appropriateness; observe source-specific terms |

A small ordinary data store and schema validation are sufficient for the task contract. Do not introduce a graph database or a new agent framework for the first version. Do not import unlicensed hackathon source into the product. Research snapshots in this workspace are inspection material, not production dependencies.

**Founder demonstration**

Use a live call into a fictional patient's existing refill or appointment task. Run a tuned conventional agent and the candidate against the same audio and task state. Show the actual recognized spans, any question asked, and the final tool payload.

Include four kinds of turn: a clean request, a name/date ambiguity that changes the action, harmless wording differences, and a legitimate correction that contradicts stored context. Include an irrecoverably unclear case that remains pending. Let the founder choose a held-out case or speak a new request. Do not inject an incorrect transcript into one side while calling it an ASR failure.

The decisive moment is a bounded operational result: the system resolves the relevant ambiguity, then completes the approved task with the correct arguments while leaving easy speech alone. Show baseline ties and candidate failures as well. A prerecorded failure montage alone would not substantiate the pitch.

**Head-to-head validation**

Build the baseline before tuning the candidate. All variants receive the same model family where applicable, source records, task policy, permissions, tool schemas, audio, and opportunities to clarify. Pin versions, parameters, vocabulary, codec, and prompt revisions.

| Variant | What it controls for |
|---|---|
| A: Current commercial STT + relevant keyterms + tuned LiveKit + capable tool-using LLM instructed to clarify ambiguity | Competent conventional implementation |
| B: A plus an independent recognizer, with a straightforward ask-on-material-disagreement rule | Extra acoustic evidence rather than sophisticated routing |
| C: A with routine confirmation of every critical field | Low error through additional patient effort |
| D: Strong multimodal model given audio and the same task context for a bounded pre-action check | The possibility that a single capable model already solves the problem |
| E: Proposed component | Whether selective repair improves the measured trade-off |
| Oracle transcript control | Upper bound on what could improve if recognition were perfect; evaluator only |

First perform an exploratory failure-existence study using roughly 400 task-bearing turns from at least 40 consenting adult speakers, including older speakers. Those are proposed study sizes, not completed work or a claim of statistical sufficiency. Use fictional details. Separate speakers and task scenarios across development and locked evaluation sets. Include ordinary turns, interruptions, natural pauses, self-corrections, background speech, unfamiliar names, numbers, negation, and truthful departures from the supplied chart. Do not assume an accent or an age is itself a defect.

Maintain separate naturalistic and deliberately difficult sets. Do not report an enriched challenge-set failure rate as production prevalence. Synthetic voices may stress codecs and noise; they cannot substitute for human turn timing or older-adult usability. Start with a language we can label well. Add another only with competent human review.

Primary measurements:

- Incorrect operational writes and incorrect claims of completion, assessed against independently annotated permissible task states.
- Correct completion, unresolved tasks, missed corrections, and inappropriate record-based overrides.
- Patient clarification turns, repeated content, active speaking time, and actual user-rated effort.
- Added median and tail latency, recognizer/LLM usage, and cost per correctly completed task.

Use human-verified transcripts and task-state checks as the primary reference. Keep the hidden intent and answers out of runtime prompts. Audit disagreements and clean cases manually. An LLM judge can assist error analysis but should not be the sole success oracle.

Compare trade-off curves: at a matched error level, does the candidate use less patient effort; or at matched effort, does it make fewer wrong actions? Include zero-repair and always-repair ablations, context removal, and removal of action comparison. Compare with an equal-compute baseline, so an extra model call is not mistaken for a policy advantage.

For a confirmatory study, use the exploratory rates and speaker clustering to determine sample size before unlocking a new test set. Predeclare an acceptable error margin and operationally worthwhile burden/cost difference. Use paired comparisons and speaker-clustered confidence intervals. A small zero-error test cannot establish safety or superiority. A randomized, counterbalanced live-call study should measure actual effort; modeled steps are insufficient.

**Reasons to kill the winner**

1. The tuned conventional system already resolves the observed errors; there is no useful room to improve.
2. The second-recognizer-plus-simple-rule baseline matches the candidate. Ship the simpler method if useful; abandon the elaborate mechanism.
3. Benefits disappear when real spontaneous speech replaces synthetic audio, or on speakers and cases not used in tuning.
4. Contextual bias suppresses new or corrected patient information, or prompts induce users to agree with wrong suggestions.
5. Added latency, questions, call duration, or cost exceeds the reduction in errors and staff cleanup.
6. The errors are mainly missing institutional data or tool-policy mistakes; speech repair cannot fix those causes.
7. Vene's patient interactions are predominantly text, voice volume is too small, or their internal controls already cover the problem.
8. Integration requires replacing their working call platform or storing audio contrary to their product constraints.
9. A stronger current multimodal model or vendor upgrade removes the advantage.
10. We can only demonstrate a hand-selected failure clip, not a reproducible improvement over strong baselines.

**Disposition of the other finalists**

Source-aware acquisition remains attractive if speech repair fails. Build it only around one administrative workflow and measure patient time, completed work, and external-contact cost. “The patient knows their preference; the clinic knows whether the referral arrived” is a useful boundary, but also an obvious rule a good baseline must receive. PROUR motivates trying a learned selector; it does not prove one is needed. Real answered contacts and uncertain availability matter more than a simulation that supplies instant answers.

Change-aware rechecking remains plausible where a late document or corrected report changes the basis of an already scheduled errand. Record author, observation time, effective time, and uncertainty separately; use authority appropriate to the fact, not a blanket latest-wins rule. Link pending actions to their supporting claims and selectively revalidate. Compare against the actual Graphiti implementation plus ordinary versioned event processing. [AHRQ's reconciliation toolkit](https://www.ahrq.gov/patient-safety/settings/hospital/match/intro.html) supports the existence of care-transition discrepancies; the contribution would collect evidence and route decisions to professionals, not select treatment. This direction has more overlap with Vene and the prior recovery proposals, so it ranks below the first two.

**What is complete and what remains unknown**

Completed: public-scope review, cross-language discovery, original submission checks, paper-method and baseline scrutiny, selected source and license inspection, candidate comparison, implementation proposal, demonstration design, and falsification plan.

Not completed or claimed: a running prototype, benchmark reproduction, clinical validation, measurement of Vene's private system, or confirmation of founder demand. The next engineering artifact should be the strongest baseline and the first real-audio comparison. The result that earns a founder's attention is an observed improvement they can reproduce—not this research document's confidence.

Pinned source URLs and SHA-256 hashes are preserved in `research/sources/manifest.json` and `research/sources/component-manifest.json`. Downloaded project code was inspected as text and was not executed.
