# Vene: the founder-impression decision

Research date: 11 October 2026. Additional challenge to the earlier CareDays recommendation. This is a product judgment based on public material, not knowledge of Vene's private roadmap. No company, patient, clinician or service operator was contacted. No prototype or clinical workflow was run.

**Decision: CareDays remains the strongest build candidate. None of the researched ideas is established as a breakthrough or an irresistible offer.**

The earlier recommendation answered which feature is most practical and aligned. The user's stronger question is which feature could demonstrate exceptional product and engineering judgment. Those are related but different tests. This additional round explored communication between care teams, correcting source records, continuity while traveling, and assistance during the visit. It did not establish a better overall bet. That is a negative research result, not a reason to rename an existing idea and call it an invention.

**What Vene actually offers**

Vene describes using records and conversations to identify care work, obtaining approval, contacting offices/pharmacies/health plans, and reporting confirmed results and unresolved steps. Family updates and bringing the appropriate person into an action are already explicit. It reserves diagnosis, treatment and medication decisions for clinicians. Generic reminders, a family dashboard, callback recovery, or a new way of escalating a clinical question would substantially overlap that promise. [Company workflow](https://www.venehealth.com/how-vene-works), [Family offering](https://www.venehealth.com/for-families).

These pages describe intended/public capabilities; they do not establish how well every workflow performs. They also cannot establish which proposed features are absent from the private product.

**The product worth demonstrating**

CareDays: arrange a patient's already-required care into fewer, manageable outings, then complete the approved bookings and paperwork across the organizations involved.

The distinguishing product insight is that a set of individually successful errands can still make a poor week for a patient and family. Start with a fully booked schedule, so the demo cannot succeed merely by finding an unbooked referral. Improve the combined arrangement while preserving the required care and office-supplied timing constraints.

A fictional patient has a lab visit, pharmacy pickup, cardiology follow-up and eye appointment on four separate days. The patient requests at most two manageable mornings, with a limit on time away from home. The caregiver supplies availability. Each office supplies permitted alternatives and prerequisites. The system searches for a feasible joint arrangement, obtains approval, and performs the changes through separate sandbox services and a consenting actor's office call. If feasible, the patient ends with two confirmed outings. Four-to-two is an illustrative case, not a measured result or universal promise.

This belongs within Vene's existing business and uses capabilities it already advertises. It creates a visible outcome for the patient without requiring a new insurer, physical service marketplace, clinical decision engine, or replacement voice stack. The prospective business benefits are better patient experience and less family coordination effort; retention, savings, or completion improvements remain unmeasured hypotheses.

**The originality limit is substantial**

EliseAI publicly describes sequential multi-appointment booking with travel time and convenience considered. Careway describes arranging transportation and consolidating same-day appointments. Therefore, appointment bundling and reducing outings are not defensible as worldwide firsts. These are vendor claims about capability, not independently verified outcomes. [EliseAI](https://health.eliseai.com/online-scheduling), [Careway](https://www.careway.health/advocacy-for/transportation/).

The proposed opportunity is execution from the patient's side across separate organizations, combining patient preferences with actual office constraints and confirmed arrangements. That is a scope worth testing, not proof that no competitor or Vene itself does it.

A Danish quasi-experiment found fewer hospital visit days with aligned appointments plus multidisciplinary conferences, but no measured improvement in patient-reported treatment burden or care integration. Assignment depended on feasible alignment. This supports investigating coordination, while warning against equating fewer calendar dates with a better patient experience. [Bell et al., 2024](https://ijic.org/articles/10.5334/ijic.7535).

**What the additional round challenged**

| Direction | Concrete patient outcome considered | Decision |
|---|---|---|
| Get clarification from my care team | Obtain a response from the responsible clinician when instructions appear inconsistent; communicate the answer and coordinate resulting errands. | Significant need, but substantial overlap with Vene's existing handoffs. Response and resolution depend on clinicians. Do not promise physician consensus or let the model choose medical advice. |
| Fix my record at the source | Help the patient submit a correction and track the originating organization's response, then share an accepted correction where authorized. | Potentially useful, but approval, evidence and turnaround belong to each institution. Public evidence did not establish a stronger frequent first use case or a gap in Vene's actual workflow. |
| Help during the visit | Preserve patient questions, capture permitted visit information, and help clarify unresolved points. | Crowded and more dependent on visit participation and clinical workflow acceptance. No clear advantage over the scheduling opportunity was established. |
| Maintain care while away | Coordinate already-planned care and required records around a temporary move or trip. | Useful for selected patients, but episodic, dependent on destination supply and clinical permission, and less broadly demonstrable. |

MyHealthVaultAI already advertises encounter capture, medication change comparison and cross-visit discrepancy detection. Its site uses fictional demonstration data and says its App Store release is forthcoming; the page is evidence of product direction, not validated deployed effectiveness. Flagging discrepancies cannot be presented as a new invention. [Product workflow](https://myhealthvaultai.com/myhealthvaultai).

Corti's discharge education agent explicitly includes identifying missing or conflicting information and preparing questions for the care team. Obtaining an authoritative response would go further than generating those questions, but that alone does not establish a commercially distinct Vene feature. [Agent description](https://www.corti.ai/agents/patient-discharge-education-agent).

Solace's founder describes his family's experience of conflicting recommendations and the value of advocacy. He also explains that support would not have made the physicians agree. This is an instructive first-person account, not outcome evidence: some disagreement is a legitimate medical decision involving different tradeoffs. A coordination product must not manufacture consensus. [Founder account, September 2026](https://www.solace.health/articles/founder-tips-for-conflicting-medical-advice).

A 2026 qualitative study of 16 working dementia carers describes interruptions, fragmented providers, inconvenient communication hours and difficulty obtaining information. This supports a broad coordination burden, but a small qualitative study cannot rank these proposed features or establish market size. [Study](https://link.springer.com/article/10.1007/s10354-026-01136-9).

The earlier China, Japan and Korea findings and source audits remain in VENE_GLOBAL_CHALLENGE_2026-10-11.md. This round also searched Japanese and Korean visit-support material. It did not find a sufficiently verified new mechanism to justify changing the winner. Search coverage does not establish that no such mechanism exists.

**Additional repository inspection: DischargeGuard**

Inspected actual source at commit `f70830a8cd7cc2a8ce61cd4ed0283c8487210ed7`; MIT license read. The project was inspected after considering the product problem. No code was executed.

- `create-care-team-task.ts` builds and returns a task object with assigned roles, urgency and recommended actions. The inspected function does not dispatch that object to a real care team.
- `generate-fhir-communication.ts` constructs a FHIR Communication object and formats it. A generated resource, including its generated sent timestamp, is not evidence that a clinician received or answered it.
- `reconcile-medications.ts` compares medication requests using RxNorm/name keys and dose/frequency strings. Its inspected path labels a prior medication absent from the discharge map as stopped. Missing data cannot safely be treated as an authoritative discontinuation; this is not a clinical rule to import into Vene.

These findings are limited to the inspected files, not a comprehensive audit of every integration in the repository. They reinforce the distinction between generating coordination artifacts and obtaining a confirmed external result.

Pinned sources: [Task function](https://github.com/nihalnihalani/DischargeGuard/blob/f70830a8cd7cc2a8ce61cd4ed0283c8487210ed7/packages/agent-escalation/src/tools/create-care-team-task.ts), [Communication function](https://github.com/nihalnihalani/DischargeGuard/blob/f70830a8cd7cc2a8ce61cd4ed0283c8487210ed7/packages/agent-escalation/src/tools/generate-fhir-communication.ts), [Medication comparison](https://github.com/nihalnihalani/DischargeGuard/blob/f70830a8cd7cc2a8ce61cd4ed0283c8487210ed7/packages/mcp-server/src/tools/reconcile-medications.ts), [License](https://github.com/nihalnihalani/DischargeGuard/blob/f70830a8cd7cc2a8ce61cd4ed0283c8487210ed7/LICENSE).

**What could make the founder demonstration exceptional**

1. Start with the care already booked correctly, and show the burden created by the combined schedule.
2. Use independent office services whose available slots and requirements are not all supplied to the planner in its initial prompt. Identify every simulated integration plainly.
3. Obtain actual responses within the controlled demonstration, choose an approved feasible option, and write the resulting bookings. A proposed itinerary is not completion.
4. Invite a surprise change: a slot disappears, an office changes an allowed interval, or a caregiver becomes unavailable. Handle the affected arrangements and report any remaining uncertainty.
5. Compare against a competent general agent explicitly asked to minimize outings, with the same tools, information, time budget and permission to use a normal solver. The baseline must not be handicapped by being told to book each task independently.
6. Measure preserved required care, respected timing, outings, maximum time away, caregiver time, unnecessary changes and actual confirmations. A shorter schedule that worsens the patient's experience is not a win.

Preserve existing bookings where possible. If an office requires cancellation first, expose that specific tradeoff before proceeding; do not imply an atomic transaction across independent offices. Do not use speculative duplicate bookings to hold scarce slots.

The first build should be one complete patient workflow. OR-Tools can handle explicit constraints; the previously audited Medplum, Synthea and LiveKit projects can support the synthetic record, office sandbox and controlled call. Those are implementation components, not the product's novelty. The handoff to Vene should expose a small input/output interface rather than require replacing its stack.

**When to stop pursuing this candidate**

Do not expand it into a large product if realistic cases rarely have beneficial feasible alternatives, if the competent baseline achieves equivalent results at similar cost, or if the integration requires substantially more work than the user benefit warrants. Do not compensate for a weak result by adding benefits discovery, clinical reconciliation, accessibility coordination and travel care into one oversized demo.

The founder-facing claim should be concrete: this prototype makes an existing care schedule more manageable and completes the approved changes. Exceptional execution could make that compelling. No research performed here establishes guaranteed enthusiasm, adoption, hiring, or a feature absent from Vene's private roadmap.
