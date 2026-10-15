**Recommendation: build CareDays as an optional feature inside Vene.**

Research conducted 9 October 2026; recommendation finalized 11 October 2026. This memo replaces the earlier speech-repair recommendation for the user's current objective: demonstrate a new patient-facing feature. It does not claim access to Vene's private roadmap, production performance, or patient population. No founders, clinics, patients, or other people were contacted. Public source files were inspected, not executed. No prototype or outcome experiment was built in this research turn.

**The feature:** “Vene arranges the care you already need into fewer, manageable outings—and handles the bookings and paperwork to make that plan happen.”

The initial user is a family coordinating several upcoming appointments, tests, and pickups for one older adult. The user experience is a short conversation in the existing Vene thread: “Mum has four separate trips coming up. Can you fit them into two mornings? I can drive Tuesdays and Fridays.”

The product contribution is an executable change to the family's schedule. The output is confirmed arrangements and a simple itinerary. A proposed schedule alone is insufficient.

**The three finalists**

| Rank | Feature | Visible result | Main reason it did not rank higher |
|---|---|---|---|
| 1 | CareDays | The same required care occupies fewer suitable outings, within patient preferences and office-supplied requirements. | Success depends on actual scheduling flexibility; bundling already exists elsewhere. |
| 2 | Keep My Care | When insurance changes, Vene checks the existing care arrangements against the new plan and completes the approved administrative changes before each affected service. | Consequential but event-driven, dependent on plan-specific information, and harder to validate independently. |
| 3 | Lower-cost care, arranged | For an already ordered, suitable service, Vene obtains comparable patient-specific estimates, presents a usable alternative, and handles the approved booking, order, and authorization transfer. | Strong existing competition, difficult price completeness, and greater dependence on commercial data and payer access. |

These are proposed additions to Vene, not claims of worldwide invention. All reuse existing providers and Vene's advocacy channels; none requires a new marketplace or business model.

**Applying all nine selection questions**

| Test | CareDays | Keep My Care | Lower-cost care, arranged |
|---|---|---|---|
| Mission fit | Appointments, errands, family coordination. | Coverage, records, prescriptions, appointments. | Coverage checks and arranging an existing order. |
| User desirability | Concrete trips and work interruptions potentially avoided. | Preserve established care during a stressful transition. | Potential reduction in out-of-pocket expense. |
| Problem evidence | Contact-day research and a real appointment-alignment intervention. | Insurer transition instructions; research on involuntary plan switching. | Price variation and existing shopping/navigation services; transparency alone has often disappointed. |
| Difference from public Vene | Optimize several tasks jointly around the family's available time. | A complete transition of ongoing arrangements, rather than an individual coverage question. | Present and complete a lower-cost alternative, rather than merely explain coverage. |
| Founder priority hypothesis | Reuses current execution channels; offers an easily understood result to existing caregiver users. | Attractive if current users frequently experience coverage changes. | Attractive if cost-related abandonment is prevalent. |
| Independent prototype | Strong: synthetic chart, controlled calendars, real calls to consenting participants. | Good workflow demo; weaker evidence without actual plan transitions. | Good workflow demo; weak real savings claim without current benefit information. |
| Competent agent baseline | Can accomplish much of it. Use ordinary scheduling tools where sufficient. | A good checklist agent is a formidable baseline. | Existing estimate API plus a good navigator is a formidable baseline. |
| Existing solutions | EliseAI; hospital scheduling programs; human coordinators. | Insurer transition teams, Rightway, other navigators. | Amino, Turquoise Health, MDsave and other navigators. |
| Demonstration appeal | Founder changes availability and sees a feasible plan actually rebooked. | One coverage-change event triggers verified administrative continuity work. | A real comparable estimate becomes a confirmed alternative appointment. |

The rankings are product judgments. We cannot infer founder priorities, willingness to pay, or patient adoption from public pages.

**Why CareDays fits Vene specifically**

Vene publicly combines a patient's care context, calls and texts, family participation, and approved administrative execution across appointments, referrals, prescriptions, and insurance. That combination is suitable for acting on constraints that span offices. The public pages reviewed do not explicitly present joint scheduling to reduce the patient's outings. This is an observation about advertising, not proof the private product lacks it. [Vene for families](https://www.venehealth.com/for-families), [Vene consumer experience](https://www.venehealth.com/consumer).

The non-obvious product insight: all the individual errands can be completed correctly while the overall arrangement remains exhausting. A calendar with four confirmed appointments can still be a poor outcome for the person who has to travel to them. CareDays makes the patient's available time, stamina preferences, and accompanying person's availability part of the outcome.

This is also why a generic pre-visit readiness feature did not survive. Vene already describes checking referral receipt, authorization, missing records, and visit instructions. [Vene's referral guide](https://www.venehealth.com/guides/follow-up-on-a-medical-referral).

**A realistic before-and-after**

The following is a fictional demonstration scenario, not an observed Vene case or a promised savings result. Assume the relevant offices permit the proposed dates, the lab's required processing interval is preserved, and the pharmacy confirms the pickup timing is appropriate.

| Arrangement | Patient experience |
|---|---|
| Before | An ordered lab visit, a pharmacy pickup, a cardiology follow-up, and an eye appointment occupy four separate outings. Each is already correctly arranged. |
| After | Tuesday: lab plus pharmacy. Friday: cardiology plus eye appointment, with realistic travel and rest buffers. Four errands, two outings. |
| When two mornings are infeasible | Vene explains the binding constraint and offers the best feasible alternatives. It does not quietly delay required care or pack an intolerable day. |

The patient can say, “Two short mornings is better than one long day,” or “Keep my current cardiologist.” Vene retrieves actual options, checks institutional requirements, presents a small choice, and executes the selected changes. The patient receives a brief confirmed itinerary with any remaining uncertainty stated plainly.

Clinicians and offices supply clinical timing, prerequisites, and permitted alternatives. Vene does not decide whether a test is necessary, combine blood orders, infer medication changes, or independently decide a delay is medically safe. If an applicable timing rule is missing, it must obtain it before moving that care. A proposed optimization can always leave an uncertain task unchanged.

**What the evidence does—and does not—establish**

1. A 2024 study using 2019 traditional Medicare data examined 6,619 older adults. Weighted mean use was 17.3 ambulatory contact days and 20.7 total contact days per year; roughly half of test and imaging days were separate from office visits. This establishes a substantial time burden, not the fraction safely combinable. [Ganguli et al., Annals of Internal Medicine](https://www.ishaniganguli.com/wp-content/uploads/2024/01/ganguli-et-al-2024-health-care-contact-days-among-older-adults-in-traditional-medicare.pdf).

2. A Danish quasi-experiment reported a 19% relative reduction in hospital visit days for its aligned-appointment intervention. It found no improvement in measured treatment burden or care integration. Allocation depended on alignment being feasible; the intervention also included multidisciplinary care conferences. It is encouraging evidence for fewer trips, not a causal estimate of this proposed software's benefit. [Bell et al., International Journal of Integrated Care, 2024](https://ijic.org/articles/10.5334/ijic.7535).

3. A July 2026 mixed-methods evaluation included detailed study of ten selected health systems. Eight excluded linked appointments from automated waitlist offers; five excluded visits requiring prior authorization. This helps identify why improving one slot can be insufficient. The sample was purposive, outcomes largely reported by administrators, and the study did not establish causality or gather patient opinions. It does not describe every scheduling system. [JMIR, 2026](https://www.jmir.org/2026/1/e90091/).

4. A 2026 scoping review describes caregiver work involving scheduling, communication, transport, insurance, and paperwork. It supports designing for the caregiver's whole experience, but is not evidence of adoption or benefit for CareDays. [Health Affairs Scholar](https://pubmed.ncbi.nlm.nih.gov/42317286/).

For the second finalist, UnitedHealthcare's own transfer guide describes separate provider, records, pharmacy, and medication transition tasks. A 2025 study of involuntary Medicaid plan replacement found disruptions in utilization; that setting cannot stand in for every insurance change. Rightway already markets proactive PBM transition support. [UnitedHealthcare](https://e-i.uhc.com/transferringcare), [Journal of Health Economics](https://www.sciencedirect.com/science/article/pii/S0167629625000566), [Rightway](https://www.rightwayhealthcare.com/resources/blog/4-proven-ways-to-keep-members-happy-during-a-pbm-transition).

For the third finalist, an estimate is not a guaranteed final bill. The feature would have to distinguish negotiated prices, cash offers, patient-specific estimates, and included professional/facility charges. It would execute an approved alternative without selecting a treatment. Existing tools make this a crowded direction. [Turquoise personalized estimates](https://turquoise.health/api/docs/personalized-estimates/), [Amino's guidance model](https://help.amino.com/hc/en-us/articles/360020881773-Amino-s-approach-to-guidance), [MDsave pricing explanation](https://www.mdsave.com/healthcare-prices-explained).

**The closest competition changes how we should pitch it**

EliseAI explicitly advertises sequential appointment bundling with travel time and patient convenience. China's Yuxi People's Hospital describes automatic grouping of multiple examinations and conflict-aware alternatives. The American College of Radiology has also published a patient-facing use case for coordinating imaging and clinic appointments. Bundling is therefore neither undiscovered nor uniquely enabled by 2026. [EliseAI](https://health.eliseai.com/online-scheduling), [Yuxi hospital, February 2026](https://www.yxhospital.com/c/2026/02/28/29328.shtml), [ACR use case](https://www.acr.org/Data-Science-and-Informatics/AI-in-Your-Practice/AI-Use-Cases/Use-Cases/Optimize-Scheduling-of-radiology).

The proposed execution for Vene is a patient's whole set of errands across independent offices, with accompanying-family constraints, optional pharmacy coordination, and bookings confirmed through the channels each institution actually accepts. This is a feature-level positioning hypothesis. The cited competitor pages do not establish that no competitor can already deliver that combination.

A founder would reasonably prefer existing software if it already covers Vene's actual setting. Demonstrate the experience and integration fit rather than claim a technical moat.

**What the global and adjacent research contributed**

Native-language searches included Chinese examination bundling and appointment flows, Japanese transport and hospital-visit support, and Korean booking, caregiver, and hackathon projects. Several searches produced poor results; the conclusions below rely on the specific primary sources and inspected files, not on search breadth alone.

| Source | Inspection and concrete finding | Implication |
|---|---|---|
| China: SHDC appointment MCP | Read `src/flows/appointmentFlow.ts` at commit `232901bc062b84c1521ee57e8133e55aae4e9ad1`. It progresses through slot, patient, mobile, CAPTCHA, SMS verification, and explicit confirmation, and builds a reservation payload. | A conversation can lead into a real booking protocol, but an MCP wrapper is not universal hospital access. No root license verified; reference only. [Repository](https://github.com/rirko/shdc-appointment-mcp). |
| Japan: MLIT shared facility transport | Read route grouping, directions, and timing services at `7dd7eb29f567f78afedfa0f105aba7421a8931f7`. The grouping service uses nearest/farthest and greedy geographic ordering; another service calls Google Directions. Root MIT license verified. | Group connected stops before optimizing the route. Do not mistake a distance heuristic for a complete appointment or accessibility feasibility check. No proposal to run a transport marketplace. [Repository](https://github.com/COMmmmONS-MLIT/shuttle-management-system). |
| South Korea: DoctorPet | Read waitlist promotion and slot release services at `934e403496e1bddea5b1a900fa3a24b1cd7c4127`. They implement FIFO offers, expiry limits, transactional state updates, and release conditions. | An offered opportunity and a confirmed arrangement are different. Its veterinary booking domain and locally controlled inventory do not solve distributed human-health scheduling. No root license verified; reference only. [Repository](https://github.com/yyb0702-spec/DoctorPet). |
| Travel: TripGuard-AI | Read decision engine and server at `172cdaee91f7cf3fb4474e93a728fab1b6e574cf`. Alternate selection sorts by delay and then checks policy; “rebooking” changes in-memory scenario data. | The multi-service disruption story is useful. The code does not substantiate live airline/hotel execution. Its hackathon affiliation is self-described; completed-event status was not independently established. No root license verified. [Repository](https://github.com/DKarthikeya31/TripGuard-AI). |
| Commerce: Amazon Day | Official description of grouping eligible orders into a selected delivery day. | Borrow the interaction of stating a preferred day once and coordinating several transactions around it. Healthcare timing cannot be treated like a delivery preference. [Amazon](https://business.amazon.com/en/blog/sustainable-purchasing-financial-sense). |
| Travel research, September 2026 | Read the comparison of full replanning, hierarchical repair, and local edits. Its full-replanning adapter lacks a plan-preservation objective; results therefore do not prove general superiority of repair. | Preserve unaffected commitments when feasible, and assess disruption cost as well as completion. Use the lesson, not its headline benchmark as healthcare evidence. [Paper](https://arxiv.org/html/2609.19654v1). |

Public snapshots and SHA-256 hashes are saved in `research/feature-sources/manifest.json`. Source inspection was selective and did not constitute a security audit or runtime validation.

**Completed hackathons were checked separately from repositories' claims**

The YC × Medplum organizer confirms its August 1, 2026 event and lists CareLoop pre-visit voice, LinkaChart action planning, and MedTrace among recognized projects. Prologue's intake and clinical code was inspected in the preceding research; it is another reason not to pitch basic chart-aware intake as a new contribution. This does not claim Prologue was an award winner. [Organizer recap](https://www.medplum.com/blog/yc-medplum-hackathon-2026-recap), [Prologue](https://github.com/mayu99/prologue-health).

Korea's September 30 final is confirmed by organizer RaonSecure. The Pascal winning project used phone access for older adults and verified delegation for welfare services. No source implementation for that winning project was verified here. It reinforces Vene's low-friction access pattern, while its identity infrastructure is outside the requested feature pitch. [Organizer report, Korean](https://www.raon.com/ko/about/news_list/view/573).

Denmark's completed Disability Tech event documents caregiver and accessible navigation projects, including CALMPATH and TrolleyBuddy. The useful design lesson is to account for a person's ability to manage the outing. Public project summaries do not establish effectiveness or reusable code. [Organizer's team catalogue, Danish](https://disabilitytech.dk/hackathon/).

**Why now, without manufacturing a 2026 breakthrough**

The scheduling mathematics is established. The current opportunity is economical execution of the phone, message, and records work surrounding a joint schedule. Vene already advertises those channels. Medplum's August 2026 release work adds a scheduling package and mountable booking workspace, making an independent working sandbox easier to build. This reduces demonstration effort; it does not grant production access to external clinics. [Medplum update](https://www.medplum.com/blog/august-2026-update).

**A small implementation that actually delivers the feature**

1. Read existing tasks and appointments. Record each task's provider, location, source, clinical timing supplied by the office, prerequisites, and whether the current booking is protected. Ask only for preferences not already available: acceptable days, maximum outing length, rest and travel preferences, and permitted changes.
2. Retrieve feasible alternatives through accepted APIs or authorized calls. Treat availability as time-stamped and potentially stale. The system can optimize only over options it actually knows.
3. Enumerate a few acceptable arrangements with conventional constraint programming. Each required task must be retained; source-supplied timing, dependencies, locations, patient availability, and travel buffers are hard constraints. Optimize the user's stated priorities: outings, longest day, accompanying-person time, and changes to existing commitments. Do not universally minimize days at the expense of exhaustion.
4. Present two or three plain-language options. Explain the actual tradeoff, such as one longer outing versus two shorter mornings. Label them proposed until confirmed.
5. Execute the approved plan, rechecking permissions and availability at each write. Confirm each institution's result. A shared SQL transaction cannot make independent clinic calls atomic. Keep existing bookings where possible; when an office requires cancellation first, expose that specific risk and obtain the relevant decision. Do not hoard duplicate appointments.
6. Send the finished itinerary. If something changes, preserve unaffected arrangements and offer the smallest feasible adjustment. Do not claim a complete care day while a required part remains unconfirmed.

| Building block | Use | Verified public repository license |
|---|---|---|
| [Google OR-Tools](https://github.com/google/or-tools) | CP-SAT feasibility and a small set of preference-ranked schedules. | Apache-2.0 |
| [Medplum](https://github.com/medplum/medplum) | Controlled FHIR records and appointment calendars for the prototype. | Apache-2.0 |
| [Synthea](https://github.com/synthetichealth/synthea) | Synthetic patient context; manually author and label realistic scheduling fixtures. | Apache-2.0 |
| [LiveKit Agents](https://github.com/livekit/agents) | A working voice channel to consenting demo participants; compatible with Vene's disclosed stack. | Apache-2.0 |

Repository licenses were checked through public GitHub metadata on the research date. Cloud services, maps, models, datasets, and telephony have separate terms and costs. Use one application service and persistent storage; a new multi-agent framework is unnecessary. A phone-first presentation is sufficient; a calendar display is useful for the demonstration, not an additional required patient app.

**The founder demonstration**

Start with four valid existing arrangements—not a deliberately broken baseline. Display their four separate outings, and the patient's actual availability and maximum outing length. Send the natural-language request through the phone or message interface.

Use a live local FHIR scheduling backend for two fictional offices and a real telephony connection to a consenting participant playing an office or pharmacy. The participant must act from independently held slot availability and rules, not recite the agent's intended answer. All patient data and institutional identities are visibly fictional; the booking writes and phone interaction are real within that sandbox.

Let the founder choose a preference and remove a slot. Show the system obtaining a feasible alternative, retaining required care, making the booking mutations, and producing confirmations. Include a no-solution case where the two-morning target is impossible. The memorable result is the patient receiving two confirmed manageable outings, not watching internal agent messages.

This proves implementation and an interaction, not patient benefit, clinic acceptance, or savings in production. Never present scenario arithmetic as a clinical or operational study.

**The competent-agent objection is valid**

A capable agent with the same tools and good instructions may achieve the same schedules. There is no need to invent a superior planner. Use the simplest successful implementation; the product hypothesis concerns packaging, execution, and reduced family work.

Compare against a capable rule-aware navigator explicitly told to reduce outings, given the same calendars, preferences, timing requirements, calls, and information budget. Include a straightforward constraint-solver implementation. Comparing only against earliest-slot booking would be an artificially weak test.

Measure retained required care, timing violations, confirmed outing count, total and maximum time away, patient decisions requested, accompanying-person availability, unnecessary rebooking, calls, and elapsed resolution time. Report infeasible cases and ties. An equal-completion result can still be valuable if the family demonstrably does less work. If ordinary prompting inside Vene already delivers the same experience, the proposed extension adds little.

The next adoption test can use consenting patients/caregivers recruited independently of Vene and de-identified or synthetic schedules, without contacting the founder. Determine whether participants prefer the proposed arrangements at all. A supervised real-world pilot would then need to establish actual slot flexibility and provider acceptance; public research cannot substitute for it.

**Why previous directions lose this particular decision**

| Earlier direction | Comparison |
|---|---|
| CareCommit | Closest technical relative. Its reported synthetic test concerns negotiation efficiency and equal completion. CareDays concerns a different output: how the already required care occupies a person's life. Reuse CareCommit only where it helps execute that feature. The different objective does not rescue an unnecessarily elaborate planner. |
| Forge | Recovery can support booking changes. The user-reported benchmark did not justify making it the product pitch. |
| Relay / Handshake | The available context describes coordination and authorization handoff themes but does not include complete separate specifications. Those themes can support execution; there is insufficient detail to rank every implementation claim. |
| Action-aware speech repair | Useful possible engineering work, but patients cannot request it as the desired new care outcome. |
| Rehearsal / voice stress tests | Suitable validation support; not the feature the founder is being asked to adopt. |

The prior Forge and CareCommit experiments are user-reported. Their code and results were not reproduced here.

Other discarded directions: generic visit readiness (public Vene overlap), intake and visit summaries (crowded and partly overlapping), shared caregiver dashboards and handovers (existing care-circle overlap), simple cancellation alerts (widespread), and medication-shortage calling (close to existing refill execution). Clinical triage, diagnosis, devices, and new transport marketplaces were excluded by scope.

**Reasons to stop or narrow CareDays**

- Vene may already provide equivalent joint scheduling; absence from a landing page is weak evidence.
- The relevant cohort may have too few flexible tasks. Specialty scarcity and clinical intervals can eliminate bundling opportunities.
- Fewer outings may be less desirable than shorter days or an earlier visit. Patient preference must decide.
- Offices may not expose options or accept agent-mediated changes, and distributed bookings may fail partway through.
- Additional calls and staff intervention can cost more than the value users perceive.
- A retrospective calculation of fewer possible trips is not proof that those slots could have been obtained.
- Existing scheduling products may solve the actual deployment better. Integration or a smaller feature would then be the right choice.

**The pitch I would take into a demonstration:** “I built a feature that uses Vene's existing care tasks to arrange fewer manageable trips for the family. Here is a working example: the same care, the actual booking changes, and two mornings instead of four separate outings. You can change the constraints and try it.”
