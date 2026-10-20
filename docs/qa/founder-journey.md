# Founder journey: the whole visit in one tab

Date: 20 October 2026. Branch `claude/venehealth-codebase-review-hop817`.

## Why

Before this work, `/demo` showed only the lab moment. Everything from Phases 9–12 was behind `/dev`, a developer launcher that asked for three browser profiles:

- open-loop memory;
- several errands and prior authorization;
- the family update and the care-circle ride.

A founder opening the link would not have seen most of the product.

## What changed

**Four chapters in the same side-by-side frame.** Each chapter uses the panes' existing authenticated sessions and the ordinary services:

| Chapter | Maria's phone | Dr. Chen | Elena |
|---|---|---|---|
| Before | The real preparation screen: *Vene found 3 things worth bringing up* from her July visit, then she approves her list. | Only the approved questions. | Nothing until Maria shares. |
| During | The existing lab-deadline catch. Its view stays mounted, so a live call survives moving between chapters. | Sample words, then the order. | No private cue. |
| Before you leave | A private prior-authorization cue, then one checklist across lab, imaging, pharmacy and health plan, approved in bundles. | Answers the coverage question; confirms and sends each order. | — |
| After | Sends Elena what's booked, asks her for a ride, and lists what carries into the next visit. | What Maria is leaving with, with receipts. | The update and the ride ask; answers for herself. |

**Seeding.** Each demo now gets its own copy of Maria's July visit, so memory works per run. A second allow-listed clinician line adds the MRI and the prescription; the server accepts only `labs` or `errands`. Maria's standing checks now include coverage.

**Copy.** Removed developer words from the guided demo: *Guided fixture*, *FIXTURE INPUT*, *Try the sample instruction*. The honesty stays, in plain language: *Sample visit · no microphone* and *Typed, not spoken: this preview does not test speech recognition.* The pane banners no longer repeat the host's unofficial-concept line.

## Product defects found and fixed

1. **More conversation silently unshared everything.** Each re-interpretation rebuilt every step with a new revision and no audience, even when nothing about the step changed. In a live visit, each new sentence withdrew what Maria had shared with Dr. Chen and retired her confirmed bookings.
   - Fix: an identical reading now keeps the existing step. Any changed detail still resets sharing and approvals as before.
   - Test: `test_more_conversation_leaves_an_unchanged_step_and_its_sharing_alone` (mutation-checked).
2. **Sharing a booked step made its receipt stale.** The step fingerprint includes audiences, so telling family after booking caused three failures:
   - Elena's update read "No current office completion has been verified".
   - Dr. Chen lost the booking.
   - The ride ask was refused.

   Fix: each request now also records an audience-free intent fingerprint. A *confirmed* receipt stays current when only sharing changed. Pending work keeps the strict fingerprint, so the worker still re-checks after any sharing change (Phase 10 design). Any change to the step or its sources still retires the receipt.

   Tests: `test_sharing_a_booked_step_later_keeps_its_receipt_but_a_changed_step_does_not` and `test_a_step_shared_with_family_after_booking_can_still_be_asked` (both mutation-checked).
3. **Prescription pickup before the visit.** The pharmacy calendar offered Oct 15–16 and the demo visit is Oct 19. It now offers Oct 22–23, after both fictional visits. Saved local calendars pick this up at office start-up.
4. **Family update text was unreadable.** It was one run-on line per step: "Step 1 · Step: … · Office: Sandbox: …". It is now one short block per step, with the same fields and allow-list.
5. **Approving right after adding found questions.** This could fail with a stale version. The found-questions card now refreshes the visit as soon as its add succeeds.
7. **Pause and resume used a moment-old call revision.** If anything moved the revision between polls, resume failed with "Everyone in the room needs to agree…". Controls now read the current call first, as *End* already did. The server still checks agreement, worker readiness and the room gate.
6. **Connection exhaustion in the demo (found in browser).** Each pane opened a live stream per chapter. With three panes, six streams used every HTTP/1.1 connection the browser allows per host, and later requests hung. Each pane now holds one shared stream that every chapter reads.

## Verification

- **Backend:** 225 tests, including the new ones above.
- **New browser test** `zz_n_demo_journey.spec.ts`, run in the standard WebRTC configuration:
  - Before, Before you leave and After chapters;
  - clinician and family payloads checked for private facts;
  - receipts stay current after sharing.
  - Passed on its own; full-suite result below.
- **Guided rehearsal** (`scripts/rehearse-demo.mjs`): all four chapters, with private-payload checks in the clinician and family frames.
  - Local preview: 3 of 3 passed.
  - The hosted single-process runner (`bring_vene.hosted_fixture` with `next start`), run locally: 3 of 3 passed, 21–25 s per complete tour.
- **Screen sizes:** desktop at 1440 px and phone at 390 px reviewed in screenshots. No horizontal overflow.
- **Full suite:** `scripts/check.sh --all` on Linux (`.local/logs/check-all-journey2.log`), exit 0.
  - 225 backend tests passed.
  - Browser: 31 passed, 6 skipped. The skips are the explicit live-provider, speech-timing and Firefox/WebKit smoke gates.
  - The first full run failed two call-control tests that pass on their own:
    - Device-loss cleanup: the test helper's end request raced the page's own end. The helper now accepts a conflict only when the call has ended.
    - Room resume: the client sent a stale call revision. This is defect 7 below.

## Not verified

- **Hosted deployment.** The hosted Render service has automatic deploys off. It still runs the previous build until someone selects **Manual Deploy** in the Render dashboard. This container cannot reach Render.
- **Live voice, chapters 3 and 4.** The second instruction was not spoken through Deepgram, DeepSeek and Cartesia here. Live mode shows "say this into the agreed microphone" and never falls back to sample words.
- **Walkthrough video.** Not re-recorded: Playwright's ffmpeg is not installed in this container. The earlier video shows only the lab chapter.
- **Platforms.** Windows and macOS were not re-run after these changes.
