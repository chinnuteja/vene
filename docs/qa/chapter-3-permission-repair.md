# Chapter 3: paused checks and confusing demo input

Date: 23 October 2026 (Asia/Calcutta).

## Reproduction and cause

The actual public visit showed the confirmed Chapter 2 lab receipt, `Allow private checks in “During” to begin`, and an active clinician `Say this` button. Pressing it had left `Your visit changed in another window. Refresh and try again.` The server's sample-turn handler does not use the encounter version: it refuses when private understanding is disabled. The frontend replaced that safe 409 reason with a generic version-conflict message. This blocked the new MRI and prescription input and left Maria's checklist unchanged.

The two fixed sentences are allow-listed sample clinician conversation turns in `demo.py`. They are not generated advice, Chapter 1 questions, signed orders or completed tasks. The guided hosted profile uses no microphone. Live speech remains a separate configuration and requires its consent/admission gates.

## Repair

- Lift the existing patient-to-host permission signal into the per-pane provider so both conversation chapters use it. It conveys only the permission boolean, not private context. Server authorization remains unchanged.
- Disable Chapter 3's sample control while checks are off. Maria can explicitly allow understanding and scheduling/coverage checks from Chapter 3, without navigating to a hidden screen. This does not authorize an external write.
- Map only the known safe missing-permission error to actionable text; preserve the existing conflict fallback for other reasons.
- Identify the sample text as the doctor's next example words, explain `Say this`, and display `Sample words added` after acceptance. Configuration failures do not select sample input.

## Verification

- `.venv/Scripts/python.exe -m pytest services/backend/tests/test_demo.py -q --tb=line -x`: **4 passed**. This includes the actual server refusal, exact safe reason, no added fixture sources without permission, participant isolation and live-mode refusal.
- `pnpm typecheck`: **passed** after correcting an omitted provider-hook field during implementation.
- `NEXT_DIST_DIR=.next-check pnpm build`: **passed**.
- Project-owned `scripts/browser-check.mjs`, `DEMO_GUIDED=true`, `NEXT_DIST_DIR=.next-check`, grep `chapter three explains|demo chapters carry`: **2 passed**. The new scenario pauses in Chapter 2, enters Chapter 3, verifies disabled input, enables checks locally, checks the known 409 presentation using an explicitly intercepted response, then submits actual sample words and observes two private plan items and the coverage cue. The existing journey verifies authorization, independent institution receipts, family delivery and payload scope.
- First browser attempt did not reach tests because the database did not remain available across temporary command lifetimes. Starting the owned database and test runner in the same command resolved startup. The first executable two-test run passed the journey and failed a new test selector because it matched Next.js's empty route announcement in addition to the intended alert. Narrowing that selector produced the final **2/2** pass; application assertions were not weakened.
- Local app: `scripts/dev.ps1 -Guided`, http://127.0.0.1:3000/demo. Actual browser inspection confirms a direct Chapter 3 entry starts with a disabled clinician sample button; Maria's explicit permission enables it and the sample words then produce the MRI/prescription checklist and private prior-authorization cue.

Evidence (ignored): `.local/evidence/chapter3-backend.log`, `chapter3-typecheck.log`, `chapter3-build.log`, `chapter3-browser-final.log`, the retained first browser report, screenshots under `chapter3-fixed/` and `chapter3-fix/`. Hosted-before screenshot is an actual capture of the user's stuck state. No credentials are included in the report.

## Deployment and limits

Hosted update pending. No provider keys, real calls, clinical rules or institution integrations were changed. This is focused fixture verification, not a fresh full-suite, live-speech, hardware or production-readiness claim. Previously recorded native voice, real telephony and hosting persistence limitations remain open.
