# Phase 9 — walk-out follow-through

Date: 16–19 October 2026. Plan: IMPLEMENTATION_PLAN_PHASES_9-12.md, Phase 9.

## Outcome

One conversation can now produce several real sandbox errands: lab, imaging, a specialist referral and a prescription pickup. Each step is checked with the sandbox office that handles it and confirmed by the clinician, who sends that office's own sandbox document. The patient then approves all ready steps with one action. Each errand is still sent, confirmed, rejected and reconciled on its own, and a live **Before you leave** checklist fills in from actual receipts. The patient can ask a family member for help with a confirmed step; the family member sees only what it is for, when and where, and answers for themselves.

## Implemented

| Area | Change | Files |
|---|---|---|
| Plan kinds | `PlanItem.kind` (`lab`, `imaging`, `referral`, `prescription`, `other`); extraction topics extended; prompt `visit-extraction-v5` forbids proposing or comparing medicines. The fixture interpreter recognizes imaging and prescription turns. Eligibility uses kind; only steps saved before kinds existed fall back to the old lab text match. | `domain/contracts.py`, `understanding/{contracts,gateway,service}.py`, `fixtures/maria.json` |
| Errand registry | One table of kinds: institution, offered resource, clinician document, locations, days and wording. Every kind reuses the Phase 6 scope → fingerprint → digest → outbox → lease → reconcile pipeline. | `execution/errands.py`, `execution/service.py` |
| Sandbox institutions | The local office now hosts four institutions with separate state rows, slots, scenarios and document receipts. The lab keeps its original state row, slot IDs, request shape and approval digest, so Phase 6–8 data and tests are unchanged. A document issued for one institution cannot satisfy another. Pharmacy requests reject any extra field, including medicine names or doses. | `execution/office.py`, `execution/contracts.py`, `scripts/reset-demo.py` |
| Bundle approval | `POST /execution/approve-ready` takes exact digests. Each errand is queued, held for a named prerequisite or refused independently in one locked decision. A changed step's digest no longer matches and is refused; nothing is rolled back across institutions. | `execution/service.py`, `execution/router.py` |
| Care circle | Migration `0010_care_circle`. A patient may ask an invited family member about a confirmed, shared errand. The family payload contains only purpose, when and where. The ask disappears from the family payload when sharing, the reservation or membership changes. A "yes" is the family member's own commitment, not a booking. | `circle/*`, `persistence/models.py`, `main.py` |
| UI | The office panel became **Before you leave**: a checklist with one plain sentence per step about what it is waiting on, an **Approve the ready steps (N)** action, per-kind clinician buttons, care-circle asks and family answers, and a sandbox-office selector for development scenarios. Sent or confirmed steps hide their request form and show the booked slot and receipt. | `components/execution-panel.tsx`, `globals.css`, `lib/api/client.ts` |

## Defects found during this phase

1. A clinician-prerequisite change read an action after its database session closed (`DetachedInstanceError`); caught by the existing continuity test and fixed.
2. Generalizing messages changed the lab's established wording ("No booking dispatched.", "sandbox office found no morning slot"); restored for the lab so recorded behavior and Phase 6 tests stay valid.
3. The first walk-out browser test assumed empty encounters. Earlier scenarios legitimately add steps and reservations, and the sandbox offices form one shared fictional calendar, so a second encounter asking for the same slot is honestly told none is free. The test now asserts its own steps and uses other locations for the second encounter.

## Tests

- Backend: 16 new tests (`test_errands.py`, `test_circle.py`) covering:
  - each kind end to end at its own institution;
  - refusal before any office call for unclassified steps or wrong locations;
  - institution isolation, cross-institution documents and medicine fields;
  - bundles with mixed outcomes, a changed step, only stale digests, guest attempts and three concurrent bundles;
  - guest scoping;
  - care-circle privacy, unsharing, withdrawal and revocation.
- Two tests were mutation-checked: removing the cross-institution document guard, or the family payload filter, makes them fail.
- Browser (`zz_walkout.spec.ts`), with real browsers and the actual local HTTP sandbox:
  - **James:** imaging, prescription and the seeded referral. The clinician sends each document in their own browser context, the patient approves the 3 ready steps at once, all three confirm with distinct receipts, Nina receives a scoped ask and answers yes, the patient sees the answer, and the family payloads omit receipts, orders, digests and sessions. Desktop and 390 px mobile, no horizontal overflow, no page errors.
  - **Asha:** the imaging center rejects and the pharmacy times out after its write. One approval leads to imaging rejected and the pharmacy going `unknown` then `confirmed` through reconciliation, with neither rolled back.

## Results

See the "Final verification" section below.

## Not done or not verified

- **Execution state still uses 750 ms polling.** The plan proposed moving it into the SSE stream. That would put an extra locked query on every stream tick, while the visible latency is already well under a second, so the move is deferred rather than claimed.
- **Live gate not run.** The live-model gate for prompt v5 has not been run with DeepSeek or OpenAI; only the fixture interpreter is verified.
- **Windows and macOS not re-run** after these changes.
- **Not real integrations:** no real office, pharmacy or plan integration exists; every institution is a labelled local sandbox.
