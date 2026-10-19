**Vene: research and proposed build**

Research date: September 25, 2026. This is a strategic recommendation and build specification, not a shipped prototype or a report on Vene's private implementation.

The user knows a founder and describes the pivot as clinical context, reminders, and tracking for older adults. Public materials now describe a broader care-coordination service. The exact pivot date, current private capabilities, pilot results, and internal roadmap have not been established.

**Recommendation in one sentence:** build Vene Rehearsal, a configurable simulation of several days of an older adult's care, which lets Vene run its existing assistant against a persistent household and healthcare environment, inspect failures, and retest changes.

This is an engineering product for Vene's team and its workflow reviewers. Its benefit to families is indirect: finding and fixing failures in the assistant they already use. If the objective is exclusively a new family-facing feature, the secondary recommendation below is a better match.

The purpose is to deliver a useful complement without rebuilding their patient assistant. Confidence is moderate: the public evidence establishes fit, but cannot establish that Vene lacks this capability or wants to own it.

**What the public sources establish**

| Evidence | Consequence for our build |
|---|---|
| The [homepage](https://www.venehealth.com/) positions Vene around proactive calls/texts, family communication and care coordination. | Preserve familiar patient channels; another mandatory app would add friction. |
| [How it works](https://www.venehealth.com/how-vene-works) describes records, patient approval, third-party contact and reporting remaining work. | A basic autonomous errand agent overlaps the advertised core. |
| The [organization page](https://www.venehealth.com/for-care-organizations) describes program-specific outreach and human escalation ownership. | Model a specific organization's policy; avoid assuming one universal escalation protocol. |
| [Terms](https://www.venehealth.com/terms), effective July 24, describe dedicated callback lines, scoped errands, sponsored access and patient reports separated from imported records. | Callback continuity, permissions and contradictory sources are appropriate evaluation targets; they are not undiscovered product ideas. |
| The [privacy policy](https://www.venehealth.com/privacy), effective September 10, describes persistent memory, trackers, transcript retention and quality monitoring. | Generic memory and observability are poor headline contributions. Audio is not retained, so transcript/event inputs are the natural starting point. |
| The [evidence page](https://www.venehealth.com/evidence/care-follow-through), dated August 18, reports no completed public outcome cohort and defines prospective measures. | Operational evidence is strategically relevant. This does not establish their present private results or absence of customers. |
| The [changelog](https://www.venehealth.com/changelog), last updated June 30, has no versioned releases. | Its age makes it inadequate evidence about what exists today. |
| A [founder profile](https://www.linkedin.com/in/niknandi) publicly describes SR007 and the founders' caregiving motivation. | Family burden is a credible alignment point. Cohort membership alone says little about product maturity. |

Public descriptions establish intended scope, not verified end-to-end performance. We did not use the authenticated product or inspect its code.

**Strategic interpretation**

Vene's potential advantage is continuity across the person's everyday life and several organizations. A family could otherwise be forced to carry context between separate systems. A useful extension should reduce the work needed to maintain that continuity.

The testable hypothesis is that failures accumulate across time and handoffs: a valid instruction becomes outdated, an office calls back after a task was closed, a caregiver becomes unavailable, or an ambiguous answer is promoted into certainty. A single successful conversation does not establish a successful episode. We have not observed these failures in Vene; they are scenarios to test.

The proposed initial customer is the founder or engineer shipping agent changes. A secondary user is the care-operations or clinical reviewer who defines expected behavior. The recurring job is: run the same difficult care episode against a new version, see exactly what changed, and decide whether it is ready for a supervised pilot.

**Directions considered**

These are qualitative judgments, not measured scores or confirmed roadmap exclusions.

| Direction | Potential value | Main objection | Decision |
|---|---|---|---|
| Reminder, tracker or family dashboard | Familiar direct usefulness | Explicit core overlap | Exclude as the headline |
| Clinical deterioration prediction from voice or records | Potentially significant | Requires appropriate data, qualified validation and an expansion beyond coordination | Do not start here |
| Personal memory or medical-record graph | Better continuity | Vene already describes persistent memory | Supporting capability only |
| Cross-organization operational memory | Could improve execution efficiency | Cold start, maintenance, permissions and substantial competitor overlap | Longer-term candidate |
| Coverage, savings or benefits assistant | Tangible household financial value | Complex external rules and a separate expertise burden | Pursue only if founder identifies this bottleneck |
| Caregiver replacement handoff | Direct relief when the usual caregiver is unavailable | Depends on reliable household knowledge and access authority | Strong second choice |
| Longitudinal care simulation | Can accelerate many existing workflows; synthetic demonstration possible | Must outperform buying/configuring an existing testing tool | Recommended initial build |

**Competition changes the claim we should make**

[Hippocratic AI](https://hippocraticai.com/ai-front-door/) markets proactive follow-up and external coordination. [Assort](https://www.assorthealth.com/blog/building-healthcare-that-remembers) explicitly describes operational intelligence, patient memory and workflow evaluation. [Tennr](https://www.tennr.com/) markets orchestration through documentation, payer requirements and patient communication. These vendor descriptions demonstrate positioning overlap; their outcome and scale claims were not independently audited.

Testing is also an existing category. [Hamming](https://hamming.ai/resources/healthcare-appointment-scheduling-voice-agent-testing) describes synthetic fixtures, tool traces and final-state checks. [H-AdminSim](https://arxiv.org/abs/2602.05407) presents a healthcare administrative simulation framework with FHIR integration.

Therefore, we should not claim invention of healthcare simulation, workflow memory or evidence-based verification. The contribution would be a useful, narrowly tailored environment and scenario library that matches Vene's actual longitudinal workflows. Evaluate existing tools before building commodity voice testing or infrastructure.

**The proposed demonstration**

Use an entirely fictional household. Maria, 78, has a clinician-issued care plan, an existing prescription renewal request and a follow-up appointment. Her daughter helps with coordination. The fictional clinician defines all medical instructions and escalation rules.

The demonstration moves through seven simulated days. Time is virtual; the system does not wait a real week. The founder can introduce a disruption and replay the episode.

| Event introduced | What the demonstration should expose |
|---|---|
| Maria says she has her medicine, but refers to an older supply | Whether the assistant preserves uncertainty and seeks appropriate clarification without choosing a dose |
| The pharmacy says a request was sent | Whether the assistant distinguishes a request from dispensing readiness |
| A callback arrives after a conversation ends | Whether it attaches to the correct open task and changes subsequent actions |
| The daughter is unavailable | Whether the agreed backup process operates without silently assigning work to an unavailable person |
| The appointment moves | Whether the old reminder is superseded and the new time has a confirmation source |
| Maria changes sharing permission | Whether later actions and updates respect the new permission state |
| Maria declines an offered administrative task | Whether the system respects that choice rather than treating persistence as success |

Start with one renewal workflow and its callback/handoff dependencies. Add appointment changes only after the first workflow works. The full table is a roadmap, not the minimum implementation.

The key presentation has three synchronized views: what the assistant heard, what it believed or committed to do, and what the simulated environment actually contains. A difference becomes a reproducible finding with a timestamp and relevant evidence.

Compare two real versions against the same seeded scenarios. Before connecting Vene, label them as reference agents or policies. Never label a baseline as Vene, invent a defect in their product, or fabricate a performance improvement for the demonstration.

**How it should work**

1. A persistent environment stores patient preferences, scoped permissions, office availability, task status, incoming events and confirmed administrative outcomes.
2. A virtual clock triggers callbacks, scheduled follow-ups and changes. Repeated delivery and out-of-order events can be deliberately tested.
3. Each actor sees only its own information. The assistant learns through allowed interactions; it cannot inspect hidden answer keys.
4. Tool adapters provide controlled equivalents of records, messages, calls and third-party responses. Vene would supply a test endpoint or integration seam for its actual assistant.
5. Deterministic checks verify event ordering, authority, stale information, duplicate actions and completion evidence. Language models may vary conversation phrasing or assist review, but must not invent the underlying truth or act as the only judge.
6. A replay interface records the exact scenario, seed, agent version, observations, actions, world state and reviewer decisions.

Run mostly text and structured events initially. Add a small voice set to test interruption, misunderstanding and accessibility once the core environment is credible. A synthetic accent alone is not a valid model of an older person's cognitive or communication needs.

Connecting a real longitudinal agent requires control of its test clock, scheduled work and tools. A phone number alone will not allow a faithful accelerated replay. If the team can provide only transcripts, limit the claim to retrospective auditing; transcripts cannot reveal what an agent would do after a different intervention.

**What to measure**

Define each task's completion contract before the run. For example, a pharmacy confirmation may close a readiness task; it cannot prove collection or ingestion. Those are different questions with different evidence requirements.

Proposed engineering measures:

- Unsupported completion statements divided by completion statements inspected.
- Open obligations that exceed the scenario's policy-defined deadline without the required next action.
- Correct application of the latest permission and task state.
- Appropriate handoff behavior, including acknowledgment only where the configured policy requires it.
- Patient questions repeated despite valid existing evidence.
- Calls, messages, tool use and reviewer interventions per correctly resolved episode.

Report denominators, scenario composition and unresolved cases. Keep patient refusal, clinical review, blockers and administrative completion distinct. Do not compress them into a reassuring composite score.

Synthetic performance measures engineering behavior under constructed conditions. It does not establish improved adherence, fewer hospitalizations, clinical safety in general, or real-world effectiveness. An operational pilot requires separate observation and review.

**Build boundary and acceptance**

First milestone: a single coherent fictional episode with three meaningful disruptions, deterministic state and evidence checks. It must expose an intentionally seeded defect and show the exact event causing it.

Second milestone: a small, independently reviewed scenario library with separate development and held-out cases. Hold out combinations of disruptions as well as wording. Avoid optimizing only for visible examples.

Third milestone: a replay UI that makes one failure understandable within a minute and lets a reviewer change a policy or expected outcome with a recorded reason.

Fourth milestone: a documented adapter contract and a reference integration. Integration with Vene is subsequent work requiring their cooperation; it should not require replacing their memory, voice or messaging stack.

Fifth milestone: two-version comparison using actual recorded results, plus a concise report separating fixed failures, regressions, and untested behavior.

A credible first delivery is the environment, reviewed scenarios, replay and adapter. A collection of attractive scripted screens does not meet this boundary. We should estimate schedule after choosing the integration depth and checking the builder's available time and skills.

**Why it might matter commercially**

The hypothesis is faster review of agent changes and fewer preventable workflow failures during pilots. This could support team velocity and care-organization confidence. It could also reveal that a less ambitious workflow is the right first deployment. No revenue increase or time savings should be promised before measurement.

The compounding asset would be the library of reviewed failure cases tied to real workflow requirements. When permitted, a production failure can become a suitably de-identified or synthetic regression case. More generated scenarios alone are not a moat.

**Reasons to reject this recommendation**

- Vene already has an adequate longitudinal simulator or an existing vendor solves the same job with modest configuration.
- The immediate bottleneck is acquiring users, enrolling them, record access or engagement rather than workflow reliability.
- The team cannot offer a meaningful test integration or reviewer time.
- A caregiver or care-operations reviewer finds the scenarios implausible.
- The product produces interesting demonstrations but does not change a release decision, uncover a useful failure or reduce review effort.

A founder conversation should establish the last operational failure they struggled to reproduce and what their current testing misses. This is a relevance check, not a request to share patient-identifying data.

**Secondary recommendation: caregiver replacement handoff**

If they want a directly family-facing extension, build a bounded handoff for when the usual caregiver is unavailable. Using approved existing context, Vene prepares the incoming caregiver with what is due, what changed, what is unresolved, which information is uncertain, and who is authorized to do what. It records acceptance of responsibility and routes questions to the appropriate person.

The useful test is whether the authorized replacement can complete a predefined nonclinical task with fewer clarification calls and without a missed handoff. Do not expand this into training an unqualified person for clinical procedures. This direction is emotionally aligned with family caregiving and could preserve continuity, but its overlap with Vene's private Care Circle roadmap is unknown.

**Target founder demonstration, after the build exists**

"I built a synthetic week of care around the workflows you describe. You can change a pharmacy response, remove an available caregiver or deliver a late callback, then watch whether the assistant keeps the care thread intact. Every failure is replayable, and you can run the same episode after a fix. The adapter is designed to let you test your own assistant."

The strongest proof is one useful failure they recognize and a verified fix. Their reaction cannot be guaranteed, and broad novelty is not the selling point.
