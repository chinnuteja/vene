**Vene company context — public-source baseline**

Last checked: 12 October 2026. This file separates company statements from our product hypotheses. The existing research memos contain recommendations and should not be treated as company facts.

**Mission and users**

Vene describes a proactive healthcare coordination assistant for patients, family caregivers and sponsoring care organizations. Patients use familiar calls and texts; the product also uses secure browser links. Its value proposition is reducing the work of carrying out care and keeping authorized people informed. [Homepage](https://www.venehealth.com/).

**Publicly advertised capabilities**

- Connect to authorized provider, pharmacy and insurance context; retain conversation history and personal preferences.
- Identify open work and reach out proactively.
- Handle approved appointment, referral, refill, coverage, claim and paperwork errands.
- Work through calls and patient portals; report results and open dependencies.
- Maintain a care circle with scoped access and updates.
- Support care-organization programs with named staff owners and escalation routes.

The consumer page also advertises cancellation searches, billing follow-through and explaining recorded information. These must not be proposed as new discoveries. Public descriptions are evidence of advertised scope, not independent verification of performance. [Consumer offering](https://www.venehealth.com/consumer), [Company workflow](https://www.venehealth.com/how-vene-works), [Organization offering](https://www.venehealth.com/for-care-organizations).

**Operating boundaries**

Clinical decisions remain with clinicians. Vene says it does not diagnose, prescribe, change medication, decide medical necessity or provide emergency services. Patients can decline, stop or change the scope of a task. Some steps require a patient, authorized caregiver or clinician. A new feature can improve communication and administrative follow-through without taking over those decisions. [Company workflow](https://www.venehealth.com/how-vene-works).

**Relevant technical disclosures**

The privacy policy lists LiveKit for real-time audio, Twilio for telephone connectivity, Photon for iMessage, Deepgram and Cartesia for patient voice, ElevenLabs for third-party calls, and Zep for memory. It says audio is processed live without being stored; transcripts persist. These disclosures suggest possible integration seams, but do not expose implementation details or guarantee access to them. [Privacy policy](https://www.venehealth.com/privacy).

Dedicated callback lines and task-scoped authority are already described in the terms. Generic callback continuity and permission management are therefore poor headline inventions. [Terms](https://www.venehealth.com/terms).

**What is unknown**

We have not inspected the authenticated product, private source, current roadmap or customer outcomes. The user believes Vene is around V1 or early V2. The public changelog was last updated June 30 and still has no versioned release entries; it cannot establish October product maturity. Use V3/V4 only as a product-planning analogy. [Changelog](https://www.venehealth.com/changelog).

**Current user brief**

The user has accepted Bring Vene and authorized Codex in this chat to build it. IMPLEMENTATION_PLAN.md defines eight implementation phases with source reuse, tests and local browser checks; BUILD_STATUS.md records actual progress. Do not reopen idea selection. The user explicitly rejected treating the earlier simple-agent objection as a demand for a minimal product. Choose architecture for the complete experience and its requirements; agent count is not the product. Stay within Vene's existing coordination business. Do not contact or ask the founders. CareDays remains rejected.

**Current research hypothesis**

The accepted direction is Bring Vene: patient-controlled participation in an actual healthcare conversation, carrying approved context and questions into the encounter and bringing clarified next steps back to existing Vene follow-through. It remains a hypothesis about opportunity, not a confirmed roadmap gap or world-first invention. See BRING_VENE_BUILD_BLUEPRINT_2026-10-12.md for the current implementation recommendation and BRING_VENE_REPO_AUDIT_2026-10-12.md for repository findings. VENE_NEXT_CAPABILITY_2026-10-11.md is the earlier proposal; its minimal-implementation framing is superseded by the user's correction.
