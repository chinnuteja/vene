# Phase 10 — catch the obstacle while the clinician is in the room

Date: 19 October 2026. Plan: IMPLEMENTATION_PLAN_PHASES_9-12.md, Phase 10.

## Outcome

Before the visit, the patient chooses what Vene may look up during it: scheduling, coverage, pharmacy. When a step is discussed, Vene checks it with the sandbox institution that handles it, and a real obstacle reaches the patient privately within about a second. Examples:

- the plan requires prior authorization for the MRI;
- the plan does not cover the prescription;
- the pharmacy is out of stock;
- there is no availability on the stated day;
- the specialist needs a referral packet.

The patient can raise the obstacle herself or ask Vene to say it aloud under the existing speech rules. Once she shares the step, the clinician sees the same fact and answers in their own view. "The office will submit prior authorization" prepares a submission to the sandbox plan, which is sent only after the patient approves it. An imaging booking then waits for that approval when the plan requires it.

## Implemented

| Area | Change | Files |
|---|---|---|
| Sandbox health plan | Fictional Evergreen Basic and Plus plans with member references, a prior-authorization rule for imaging, and a formulary listing covered alternatives. `/formulary` publishes medicine names only, so Vene matches locally and sends just the matched name. Prior-authorization reviews run through the existing reservation path, so a decision is a persisted receipt that is reconciled on timeout and delivered by signed callback. Pharmacy `/stock` (with an `out_of_stock` scenario) and specialist `/requirements` were added. | `execution/office.py`, `execution/contracts.py`, `execution/errands.py` |
| Coverage on file | `EncounterView.coverage` holds a fictional member reference, which the ContextAdapter strips for clinician and family views. Seeding fills it into saved visits without overwriting edits. | `domain/contracts.py`, `domain/context.py`, `seed.py`, `fixtures.py`, `fixtures/maria.json` |
| Standing permission | Read-only check kinds bound to the patient session. Changing them advances the consent epoch and supersedes obstacles that no longer apply. It never authorizes a write. | `feasibility/service.py`, migration `0011_feasibility` |
| Check worker | Runs inside the existing execution worker. It enqueues one check per step, kind, exact step version and permission revision. Before any network call it re-checks permission and pause. On return it discards results when the step version, the permission or the pause state changed. | `feasibility/service.py`, `execution/worker.py` |
| Obstacles | Derived deterministically from institution responses; no model output can create one. A person's answer is never reopened by re-checking the same step version. Guests see an obstacle only for a step and sources shared with them, at the same version; family members see none. | `feasibility/*` |
| Cues | A new obstacle creates a private cue in the same transaction. The spoken wording names no medicine and no patient. A cue stops being speakable once its obstacle is resolved, superseded or corrected. "Help me keep track" includes open obstacles. | `speech/service.py` |
| Responses | Only the named resolver answers: the clinician for prior authorization, formulary and referral packet; the patient for availability and stock. Answers are recorded with name and time and are never a care decision. "The office will submit prior authorization" creates a `resolution` plan step, shared with the clinician only, plus a prepared plan submission. | `feasibility/service.py`, `domain/contracts.py` |
| Booking gate | Imaging approval waits on an approved prior authorization whenever a current coverage check requires one. | `execution/service.py` |
| UI | A preparation card ("Catch problems while you're still in the room") with three explained permissions. A visit panel lists obstacles with source and check time, plan-listed alternatives labelled as plan facts, and response buttons for the resolver only. Open obstacles also appear on the Before you leave checklist. | `components/in-room-checks.tsx`, `execution-panel.tsx`, `visit-workspace.tsx`, `globals.css` |

## Tests

- **Backend:** 13 new tests in `test_feasibility.py`:
  - nothing leaves without permission, and only permitted kinds run;
  - private versus scoped visibility, with family absent;
  - formulary facts with no medicine in spoken text;
  - another plan and unidentified medicines raise nothing;
  - a correction supersedes the obstacle and its cue;
  - queued and in-flight checks are discarded after revocation;
  - pause holds checks and discards results that return during pause;
  - all five obstacle kinds;
  - resolver-only answers with listed choices;
  - the full prior-authorization flow, including the imaging gate;
  - a denied authorization keeps imaging blocked;
  - a resolved fact is not reopened.
- **Mutation checks:** removing the claim-time permission check, the pause hold, or the prior-authorization gate each makes its test fail.
- **Browser (`zz_x_in_room.spec.ts`)**, run with patient, clinician and family each in their own browser context:
  - preparation permission;
  - two obstacles from fixture turns;
  - a private cue for the patient only, with no medicine or patient name in any spoken text;
  - clinician and family payloads empty until shared, family always empty;
  - after sharing, the clinician answers both;
  - the cue disappears;
  - the patient approves the prepared submission and the checklist shows "Approved by the sandbox health plan";
  - 390 px mobile with no overflow, no page errors.
- **Latency:** 20 fixture turns, each changing the step's sources so the plan re-checks it:

| Span | min | median | p95 | max |
|---|---|---|---|---|
| Client-observed turn → obstacle (includes understanding and polling) | 741 ms | 881 ms | 938 ms | 971 ms |
| Server-side finalized turn → private cue | 649 ms | 802 ms | 866 ms | 892 ms |

The target was under 3,000 ms p95. These are local fixture-interpreter measurements on Linux. Live-model latency is separate and was not measured.

## Defects found during this phase

1. Granting "scheduling" correctly produced a referral-packet obstacle for Maria's seeded referral step, which four new tests had not anticipated. The tests now grant only the kinds they examine; the behavior is right.
2. Plan alternatives were repeated inside the fact and again on the plan-facts line, and the private cue showed a raw ISO timestamp. Both were found in screenshot review and fixed.
3. During mutation testing, one shell edit silently failed to apply, which made a guard look untested. The edit was repeated in Python; the test does fail without the guard.

## Final verification

See the BUILD_STATUS entry for the full `scripts/check.sh --all` result.

## Not done or not verified

- Not run against live providers: the prompt-v5 model gate and live speech of obstacle cues were exercised only with the fixture interpreter and the offline voice.
- **Plan not identified per visit:** coverage uses a fictional member reference. Real plan integration and eligibility are out of scope.
- **When obstacles reach the plan:** open obstacles appear on the checklist during and after the visit. They are not yet turned into separate follow-up tasks with their own owners.
- Windows and macOS were not re-run.
