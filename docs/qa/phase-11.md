# Phase 11 — preparation that writes itself

Date: 19 October 2026. Plan: IMPLEMENTATION_PLAN_PHASES_9-12.md, Phase 11.

## Outcome

Maria opens preparation and sees **"Vene found 2 things worth bringing up"**: a question she asked in July that was never answered (3 months ago), and a pharmacy message saying her refill needs a new prescription (8 days ago). Each item shows where it came from and how old it is. She keeps or drops each one, marks one "Already done", adds the rest with one action and approves her list. She reaches an approved list in three interactions. The July lab work is not proposed because a lab was confirmed after July, so that loop is already closed.

When a next visit is prepared, it inherits this memory:

- a loop marked done stays closed;
- a question carried today replaces its July original instead of appearing twice;
- loops that cite the same source become one item, keeping the patient's own wording.

## Implemented

| Area | Change | Files |
|---|---|---|
| Memory port | `MemoryPort` with `open_loops`, `history` and `record_outcome`. The Postgres implementation reads this prototype's own records, shaped so Vene's existing memory service could implement the same interface. | `memory/port.py`, `memory/postgres.py` |
| Open-loop rules | Deterministic; each cites a stored source. **Unfinished step:** a planned lab, imaging, referral or prescription with no confirmed errand. **Unanswered question:** a selected question from an earlier visit that was never answered. **Office waiting:** an office message within 60 days saying something is still waiting. **Unknown completion:** a request sent in an earlier visit and never confirmed. | `memory/postgres.py` |
| Closing loops | A loop closes when any of these happens: a later confirmed errand of the same kind; a carried question is answered; the patient records "Already done" or "not relevant". Loops citing the same source merge, in preference order: patient's question, unconfirmed request, planned step, message. A carried question replaces its original. | `memory/postgres.py` |
| Carrying | Only keys of currently open loops are accepted, so unknown keys cannot inject questions. Sources are copied into the visit as private imported records, so they are never re-detected as new messages. Draft questions default to the clinician audience and are visible only after the patient approves the list; family is never a default. Carrying invalidates an earlier approval. | `memory/service.py`, `domain/contracts.py` (`Priority.loop_key`) |
| History data | A fictional July visit plus a recent pharmacy message for Maria, James and Asha. History visits have no memberships: they are reached only through memory. | `fixtures/maria-history.json`, `seed.py`, `fixtures.py` |
| Continuity | Next-visit preparations inherit coverage. Deleting a visit purges loop outcomes recorded from it but keeps unrelated earlier visits. | `continuity/service.py` |
| UI | A drafted-agenda card at the top of preparation: keep/drop, age, "Why Vene suggested this" with quoted sources, "Already done", and one add action. Added questions appear in the normal list with Dr. Chen pre-selected and family not. The long source-sharing list is now collapsed by default. | `components/drafted-agenda.tsx`, `preparation-controls.tsx`, `visit-workspace.tsx` |

Not implemented: the plan's optional model phrasing of drafted questions. All wording is deterministic templates or the patient's own earlier question, so the citation rule is satisfied trivially and nothing can be added by a model.

## Defects found during this phase

1. **Imported copies were re-detected as new messages.** Copied sources kept their "office message" type, so the copy showed up as a fresh loop. Copies are now typed as imported records.
2. **Test isolation.** Loop outcomes are stored per patient, not per encounter, so they survived each test's encounter reset and leaked between tests. The backend fixture, browser reset and demo reset now clear them.
3. **Deletion scope.** The deletion test assumed a patient has a single encounter. With history, deleting today's visit correctly keeps the separate July record; outcomes recorded from the deleted visit are purged, and a test now covers this.
4. **Duplicates in the next visit.** A carried question and its July original both appeared. The carried copy now replaces the original.
5. **Noise, found in screenshot review.** The next visit listed three items for one referral problem, and source lines showed two dates. Loops sharing a source now merge, and the source line names the visit once.

## Tests

- **Backend:** 12 tests in `test_memory.py`:
  - sources cited with correct ages;
  - already-listed items are skipped;
  - memory is patient-only;
  - private drafts with clinician default and no family, and nothing visible to the clinician before approval;
  - unknown keys refused;
  - outcomes and later completions close loops;
  - unconfirmed errands become completion questions;
  - an injected instruction in an old message stays data and changes no audience or approval;
  - an honest empty state;
  - the next visit inherits memory and keeps the closed loop closed;
  - deletion purges outcomes recorded from the deleted visit;
  - a carried question replaces its original;
  - loops citing the same source merge into the patient's own question.
- **Mutation checks:** each of these breaks a test:
  - family as a default audience;
  - ignoring recorded outcomes;
  - ignoring later completion;
  - dropping the carried-question rule.
- **Browser** (`zz_y_memory.spec.ts`), run with real browsers:
  - the drafted card loads, with sources and age;
  - "Already done" removes the pharmacy loop;
  - add and approve take 3 interactions in total;
  - Dr. Chen is pre-selected and Family is not;
  - the clinician and family receive nothing new before approval;
  - after approval the clinician sees the question but not its private source, and family sees nothing;
  - a next visit opened from a new invitation shows the closed loop absent and the carried question once;
  - 390 px mobile has no overflow;
  - a keep-checkbox can be toggled with the keyboard;
  - no page errors.
- **Regression:** the audience test now opens the collapsed sources list first; the existing deletion test asserts the July history remains.

## Final verification

`scripts/check.sh --all` (Phases 1–11, Linux, 19 October), third full run after the fixes below:

| Check | Result |
|---|---|
| Backend (pytest, real Postgres) | 185 passed (173 earlier + 12 new) |
| Child-log regression, contract drift, TypeScript, production build | Passed |
| Browser (Chromium, real local WebRTC and HTTP sandboxes) | 28 passed, 4 skipped |
| Phase 10 latency inside the suite | p95 940 ms turn → obstacle; 855 ms finalized turn → private cue |

The skipped scenarios are the same explicit gates as in earlier phases.

The first two full runs did not pass. Their failures and what was done:

1. **Workflow (Phase 6 test), with continuity and memory failing as a consequence.** This was a latent race in the test, not a product defect. The readiness check only waited for a lab step to exist. Earlier scenarios leave a lab step on Maria's visit, sometimes human-corrected, so an interpretation still in flight could change answers mid-edit. The test now waits until understanding has processed the latest revision. The memory test also read the first source quote on the card instead of the blood-pressure item's own source; it now reads that item's.
2. **Packaging recovery (Phase 8 test), first run only.** After a hard voice-worker restart, the call reported unavailable for more than the 10-second wait after resume. The recorded timeline shows the new worker reporting ready early, then failing to come back to active, which is consistent with the WebRTC reconnection limitation recorded in Phase 8. It passed in 2 of 2 isolated runs and in both later full runs. **The root cause is not established**; this is recorded as an intermittent voice-recovery failure, not as passing evidence.

## Not done or not verified

- **Optional model phrasing:** not implemented (see above).
- **Real memory not connected:** the port is not connected to Vene's real memory service, and nothing has been ingested from real records.
- **Real-patient questions untested:** the 60-day message window and the age thresholds are product choices, not validated with patients.
- **Platforms:** Windows and macOS were not re-run.
