**Vene: a fresh challenge to CareDays**

Research date: 11 October 2026. This is a product decision memo, not a claim about Vene's private roadmap or a completed prototype. Public implementations were read but not executed. No founders, patients, providers, or service operators were contacted.

**Decision: keep CareDays as the first build. Covered Support is the strongest new challenger.**

The new search did not establish a clearly better standalone feature. It did expose a useful improvement to the recommendation: optimize for outings the patient can actually manage, with their stated support needs accounted for. A schedule with fewer dates can still be a worse experience.

This is a refinement of CareDays, not a newly named invention. Do not combine every idea below into the first prototype.

**The company boundary**

Vene describes approved administrative follow-through across appointments, referrals, prescriptions, insurance, records, and family coordination. Its workflow combines record context with practical information from conversation, then performs bounded errands and distinguishes confirmed results from open steps. Clinical decisions remain with clinicians. This makes patient-side coordination a natural addition; a new insurer, escort marketplace, monitoring device, diagnostic product, or clinical recommendation engine would change the business. [How Vene works](https://www.venehealth.com/how-vene-works), [Care organizations](https://www.venehealth.com/for-care-organizations).

The original voice stress-test document and the user's product-feature brief were revisited. The voice document is another AI's proposal, not authoritative company information. Its speculative clinical gates and assumptions about the user's language abilities are not adopted. The known original attachment is VENE_VOICE_STRESS_TEST.md; this research did not establish a separate .tm attachment.

**Three strongest candidates after this challenge**

| Rank | Feature | User-visible result | Why it belongs here | Main reservation |
|---|---|---|---|---|
| 1 | CareDays | Required care fits into fewer, manageable outings, with bookings and prerequisites confirmed. | Uses Vene's existing patient context, calls, paperwork and family coordination. | Real-world scheduling flexibility may be too limited. Bundling already exists elsewhere. |
| 2 | Covered Support | Help already available through a patient's existing plan is verified and arranged for a specific care need. | Extends insurance errands into fulfilled practical assistance. | Accurate member-specific eligibility, remaining allowances and actual local supply are difficult; competition is substantial. |
| 3 | A Visit That Works for Me | The office confirms the particular assistance needed for the patient to use the visit. | Extends appointment coordination into access arrangements. | Narrower cohort; depends on institutional acceptance and available resources. |

This is a ranking for an independent candidate's first demonstrable addition to Vene. It is not a ranking of societal importance. A cohort with severe transport or communication barriers could reverse it.

**What native-language research added**

China: Shanghai's June 2026 elder accompaniment policy treats assistance with movement, administrative procedures and clinician communication as connected parts of getting through care. It also describes linking accompaniment organizations with mobility resources. The mechanism worth borrowing is responsibility for the whole outing, rather than treating booking as the complete result. It does not imply that software can replace a physical companion. [Official Chinese policy](https://www.shanghai.gov.cn/gwk/search/content/b5d7b569f014474a862c818ec54c2671).

China: government descriptions of 免申即享 describe certain benefits becoming available without a repeated application, using institutional information flows. This is a useful interaction pattern: existing context can reveal help a person did not know to request. A private US assistant does not inherit those governments' data access or authority, and should still obtain task-specific approval. [Official example, June 2026](https://www.shangyou.gov.cn/syxrmzfw/c124522gmq/202606/d71f13c97a844bc4828b3116d9719ab1.shtml).

South Korea: the health ministry's June 2026 explanation of 복지멤버십 describes personalized welfare notices through KakaoTalk, covering 163 central and local services at that time. The lesson is proactive discovery in a familiar communication channel. A notice is not enrollment, eligibility adjudication, or a delivered service. [Official Korean explanation](https://www.korea.kr/news/policyNewsView.do?newsId=148966205).

Japan: the completed August 6, 2026 Hoken no Katachi competition awarded first prize to TCS's かぞくパルス. TCS describes monitoring, taxi assistance and insurance benefits triggered under predefined conditions. The useful connection is delivering a concrete service at a moment of need. Its wearables, inferred health deterioration and new insurance product are outside Vene's requested scope. The organizer explicitly describes working mockups; the award is not evidence of deployed effectiveness. No winner source repository was verified. [Organizer](https://hokennokatachi.main.jp/), [TCS's account](https://www.tcs.com/jp-ja/notice/0915-tcs-japan-wins-top-award-for-hoken-no-katachi-2026).

Japan: Sugiyama Jogakuen University and Loftwork describe a browser-based communication aid for deaf patients, using selectable questions and phrases. It highlights that being able to book care and being able to participate in the visit are different problems. This is not presented as a new 2026 invention. [Project account in Japanese](https://loftwork.com/jp/project/sugiyama_web_application).

England provides a useful implementation comparison: the NHS Reasonable Adjustment Flag records and shares accommodation needs. Its 2026 roadmap discusses expanding integration. Recording a need does not itself reserve the interpreter, longer slot, or equipment required for an individual appointment. UK infrastructure is a design reference, not a US integration entitlement. [NHS service](https://digital.nhs.uk/services/patient-flags-service/reasonable-adjustment-flag).

Additional French, German, Portuguese and Dutch searches were less productive. They did not yield a sufficiently verified stronger product mechanism, and are not counted as evidence for a winner.

**New challenger 1: Covered Support**

One sentence: Vene finds support in your existing coverage that can help you complete your care, verifies that you can use it, and arranges it.

A fictional example: a daughter cannot take her father to an already ordered appointment. With his approval, Vene checks the actual plan and member circumstances, verifies whether a suitable transport benefit exists, confirms remaining trips and booking requirements, and arranges both directions through the accepted operator. If he needs accompaniment, a vehicle booking alone is not represented as solving that need. If there is no eligible benefit or suitable service, Vene says so.

The contribution is the transition from a plan document to usable assistance. An insurance summary, directory link, likely-eligibility score, or application submitted is not the completed result.

Start with one support category and one plan/vendor workflow. Avoid building a universal benefits database, a new provider network, or a system that changes the person's insurance. Other examples, such as existing post-discharge support, require their own actual plan terms and eligibility checks.

Why it could matter: it may turn an otherwise unusable appointment into an attendable one, and may spare a family an expense or work interruption. Those are measurable practical outcomes. They are hypotheses for the proposed feature, not demonstrated savings.

The evidence is mixed. A 2026 study of plans adding non-emergency transport coverage in 2019 found no meaningful first-year change in measured care utilization for its low-income and disabled Medicare Advantage population. It could not observe actual transport benefit use or generosity. This does not prove underuse caused the null result. It means neither coverage discovery nor more benefits can automatically be advertised as improved health outcomes. [Ianni et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC12932071/).

A second 2026 study found no general reduction in acute care utilization across all non-dual or dual-eligible enrollees offered expanded benefits, with reductions in certain highly frail non-dual subgroups. Again, it studied offerings rather than observed individual benefit use. [Jung et al.](https://onlinelibrary.wiley.com/doi/10.1111/1475-6773.70136).

Competition is direct. Havn advertises matching patients to assistance and initiating referrals or enrollment actions. Careway explicitly describes finding covered transport, handling enrollment, checking available local programs, and establishing recurring arrangements. The latter also mentions consolidating visits. Their marketing establishes overlap; it does not independently verify efficacy. Havn's headline savings and awareness percentages were not independently validated here and are not used to score the idea. [Havn](https://www.care-havn.com/), [Careway](https://www.careway.health/advocacy-for/transportation/).

Why second: useful, aligned, and worth considering later, but a convincing prototype depends on more plan-specific and operator-specific facts than CareDays. A polished demonstration can conceal that the help is not actually available. A competent navigator with a good checklist is also a strong baseline. There is no verified unique algorithmic advantage.

**New challenger 2: A Visit That Works for Me**

One sentence: tell Vene what you need to manage a visit, and it gets that arrangement confirmed with the office before you arrive.

Examples are a patient-requested communication aid, interpreter, accessible examination arrangement, appropriate appointment length agreed by the practice, or permission for a chosen support person to participate. These are requests to the institution, not promises that every accommodation is available or a clinical judgment about what the patient needs.

A fictional before-and-after: the patient says, “I struggle to hear the doctor and cannot rely on my daughter coming.” Vene asks the patient's preferred communication arrangement, checks it with the office, and coordinates whatever that office agrees to provide. It reports the specific arrangement and remaining limits. “Your needs have been added to a note” does not become “the assistance is booked.”

This is consequential for the right patient. A nationally representative cross-sectional analysis of 5,954 Medicare beneficiaries used 2015 NHATS data and found that communication disabilities were associated with use of a communication support person. More than half of older adults with communication disabilities did not use one at visits; use varied by social factors. This supports an access concern, not a claim that everyone without a companion needs one or that this proposed feature improves outcomes. [Study](https://pubmed.ncbi.nlm.nih.gov/38826064/).

Why third: potentially distinctive as an executed patient-side workflow, but the concept overlaps accessibility coordination and appointment preparation. It is difficult to claim it is absent from Vene's actual practice, and a demo can only prove coordination if the recipient confirms a real arrangement. Keep clinical interpretation and decisions with qualified professionals.

**What the source code actually does**

The idea shortlist preceded repository selection. The following new inspections distinguish calculation, recommendation, record exchange and fulfillment.

| Project | Files and observed behavior | Reuse judgment |
|---|---|---|
| Japan: OpenFisca-Japan-MCP, created April 2026 | server.py exposes input-attribute discovery and calculation tools. sdk.py creates household/person entities, sets inputs and invokes OpenFisca calculations. Missing age or income can default to zero; several input errors are silently ignored. | Useful pattern for separating conversation from explicit rules. It is not an application or fulfillment system. Do not treat defaulted or invalid inputs as verified facts. Wrapper is Apache-2.0; underlying OpenFisca-Japan license read as AGPL-3.0. Japanese benefit rules are not US health-plan rules. |
| Korea: Bokji-mate, created September 2024 | PolicyService.java matches interests/categories, then adds random policies if fewer than ten were found. PolicyRepository.java implements that random query. | Actual recommendation code, but the inspected path does not establish personal eligibility. No root license was found. Reference only, and not a 2026 breakthrough. |
| England-related community POC: patient-flag, June 2026 | client.py performs read-only GET /PatientFlag against an NHS sandbox; production authentication is explicitly a future extension. | MIT. Helpful for understanding the record interface. It neither grants production access nor confirms an accommodation has been supplied. This is not represented as an official NHS SDK. |
| China: yibao-guide, August 2026 | index.html is a sales page for a reimbursement guide; script.js copies a contact identifier to the clipboard. | Rejected as implementation evidence for a benefits-execution feature. Public code is not automatically a substantive working product. No root license found. |

Pinned code links: [Japan server](https://github.com/project-inclusive/OpenFisca-Japan-MCP/blob/d9730381ab96b5418677a2f56ad8ab8bedd3e979/src/openfisca_japan_mcp/server.py), [Japan calculation](https://github.com/project-inclusive/OpenFisca-Japan-MCP/blob/d9730381ab96b5418677a2f56ad8ab8bedd3e979/src/openfisca_japan_mcp/sdk.py), [Korea recommendation](https://github.com/rlaxxwls13/Bokji-mate/blob/baddc7fc6bc8b82475de4c6a7311cd9042ddc88a/bokji-mate/src/main/java/mover/bokji_mate/Service/PolicyService.java), [Patient flag client](https://github.com/enricogasparini/patient-flag/blob/ccacdda6b5d17a4885234ba3d35a2468d9c19164/src/patient_flag/client.py), [Chinese page](https://github.com/zczx168-web/yibao-guide/blob/3cbe7d375ede6ae13bf39815e04e749f24bb1e7b/index.html).

Local copies of six code files and three licenses are in research/challenge-sources, with their source URLs in manifest.json. The Chinese HTML was also inspected through the connector but was not copied into the local code snapshot set. No runtime tests or production integrations were attempted. OpenFisca-Japan's core license was read from main; the MCP and patient-flag code links are pinned.

Previously inspected practical references remain relevant: [Japan's shared transport project](https://github.com/COMmmmONS-MLIT/shuttle-management-system), [China's appointment flow](https://github.com/rirko/shdc-appointment-mcp), and [Korea's DoctorPet booking services](https://github.com/yyb0702-spec/DoctorPet). Their exact file findings and license limitations remain in VENE_FEATURE_DECISION_2026-10-09.md. None is a complete implementation of the proposed Vene feature.

**Why CareDays still wins**

One sentence: Vene arranges the care you already need into fewer, manageable outings, then completes the bookings and paperwork to make them happen.

It has a concrete patient-facing outcome and relatively direct use of Vene's advertised capabilities. The initial proof need not depend on gaining access to an insurer's member allowances or creating a physical service network. It can demonstrate the full workflow with synthetic records, controlled office calendars and consenting actors.

The insight is that every individual appointment can already be correct while the combined arrangement is poor for the family. A joint plan can preserve the care and improve the experience. Clinical timing, order prerequisites and permitted alternatives must come from the responsible office; the assistant does not decide what care can be skipped or delayed.

There is supportive evidence for fewer visits, with an important limit. A Danish quasi-experiment reported a 19% relative reduction in hospital visit days from aligned appointments plus multidisciplinary conferences, but no measured benefit in patient-reported treatment burden or integration. Assignment depended on feasible alignment. This supports testing the idea; it does not establish that CareDays will save a given percentage or improve clinical outcomes. [Bell et al.](https://ijic.org/articles/10.5334/ijic.7535).

Novelty is limited. EliseAI already advertises multiple sequential appointments with travel time and convenience considered. The new Careway finding overlaps both transport arrangements and visit consolidation. The recommendation therefore rests on useful execution inside Vene, not a claim of worldwide invention or proof that Vene has not built it. [EliseAI](https://health.eliseai.com/online-scheduling), [Careway](https://www.careway.health/advocacy-for/transportation/).

**The concrete improvement to the first build**

Keep the narrow goal: make one older adult's existing set of errands easier to complete.

Record the patient's own acceptable days, maximum outing length, travel preferences, accompaniment availability and any relevant support requirements. A time slot that needs unavailable assistance is not a feasible option. Neither age nor a diagnosis should automatically imply incapacity or a particular accommodation.

Only add a support check where it changes the example's feasibility. Do not put benefits discovery, an accessibility passport, a transport marketplace and a family dashboard into the first build.

An optional later extension can run Covered Support when a specific outing is blocked by a practical need. That dependency is a reason to keep the modules separate during implementation, not a reason to market a bundle of unrelated features.

**A founder demo with a falsifiable result**

Use a fictional patient with four already valid arrangements: a lab visit, pharmacy pickup, cardiology follow-up and eye appointment. The offices explicitly permit alternatives, and the lab-to-follow-up interval is supplied as an office requirement.

1. Show the four outings already scheduled and the caregiver's limited availability. The system starts from a successful ordinary care plan.
2. The patient asks for two manageable mornings and sets a maximum time away from home.
3. Retrieve availability from separate calendar services. Use one real call to a consenting actor whose office facts are independent of the planner's initial context.
4. Present two feasible options. For one relevant constraint, obtain explicit office confirmation rather than merely recording the patient's request.
5. Execute the selected bookings in the sandbox systems and show the confirmed itinerary. Mark proposed or outstanding parts plainly.
6. Let the founder change a slot or remove caregiver availability. Preserve unaffected arrangements where possible; explain honestly when no better feasible plan exists.

The four-to-two example is a demonstration setup, not observed savings. The impressive moment is the completed arrangement and the response to a surprise constraint. A rewritten calendar image alone proves little.

Use ordinary constraint programming, such as [OR-Tools](https://github.com/google/or-tools), over source-backed permissible options. A [Medplum](https://github.com/medplum/medplum) sandbox can hold synthetic FHIR records and appointments; [Synthea](https://github.com/synthetichealth/synthea) can supply fictional records; [LiveKit Agents](https://github.com/livekit/agents) can support the controlled call. These components were checked in the prior memo. Production clinic access remains separate.

Treat external bookings as non-atomic. Recheck availability and scoped approval before each change. Keep existing appointments when the institution permits; if cancellation must precede replacement, surface that risk. A failed move must not become a false confirmation.

**The competent-agent challenge**

Compare against a strong agent explicitly instructed to reduce outings and respect every stated constraint, with the same tools, records, institution facts and permission to use ordinary scheduling code. Include an ordinary deterministic planner where appropriate.

Measure retained required care, timing violations, trips, longest outing, caregiver time, unresolved arrangements, confirmation errors, unnecessary booking changes and patient decisions. Do not use number of model calls as the main benefit.

Include cases with no room to improve and cases where combining trips would be worse. If the strong baseline produces the same result, report that. The artifact may still demonstrate product execution and integration, but it would not establish a new planning advantage.

The supplied accounts of Forge and CareCommit found limited or no task-completion advantage over competent baselines; those accounts were not reproduced here. CareDays changes the objective to practical burden while preserving care. Speech repair and rehearsal remain supporting engineering, not the feature's main pitch.

**Reasons to abandon or reduce the recommendation**

- The relevant users rarely have multiple flexible errands.
- Slot scarcity prevents meaningful improvement without unacceptable changes.
- Users prefer separate shorter visits, so fewer days is the wrong objective.
- Institutions cannot confirm the arrangements, or the workflow creates more staff work than it saves.
- Vene already provides the experience well.
- The impressive result only occurs in handpicked calendars.
- A simpler agent delivers the same experience with less integration or maintenance.

No public research can determine which of these applies to Vene's private cohort. The best available decision is a bounded working proof, with visible outcomes and an honest comparison, rather than a guarantee that the founders will want it.

**What would impress me as the founder**

An engineer who can demonstrate a useful new experience in the company's actual channels, make the institutional constraints visible, and substantiate the result would earn attention. In this case the credible claim is: “Here is how Vene can give a family time back while keeping all their required care arranged.” The code, confirmations and limitations should support that sentence.

