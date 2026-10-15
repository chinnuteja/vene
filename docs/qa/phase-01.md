# Phase 1 — completed verification

Date: 12 October 2026. Configuration: fictional patient, local Postgres, no live voice/model providers.

## Result

Phase 1 passed. The application is running at http://127.0.0.1:3000/prepare. The current preview serves the production build; the backend runs on port 8001 and Postgres on 5432.

Implemented:

- Preparation, visit and next-step routes with responsive desktop/mobile layouts.
- Persistent question selection, source viewing and recoverable connection errors.
- Typed encounter, evidence, priority, plan, command and event contracts.
- Transactional projection/event updates with optimistic version checks, scoped evidence references and command idempotency.
- Real Postgres migrations and separate development/test databases.
- Generated OpenAPI and TypeScript types with a drift check.
- Owned-process launch/stop scripts and independent development, preview and verification build directories.

## Checks actually performed

| Check | Result |
|---|---|
| Migration from an empty test application schema | Passed |
| Backend/API/domain suite | 15 passed |
| Duplicate and concurrent commands | Passed against Postgres |
| Invalid/stale commands and cross-visit evidence | Rejected without partial writes |
| Database unavailable versus API alive | Passed |
| Generated API contract comparison | Passed |
| TypeScript check | Passed |
| Production build | Passed |
| Chromium interactions | 5 passed |
| Desktop/mobile visual review | Passed |
| Normal-page console/request errors | None in final capture |
| Horizontal overflow at 390px | None |
| Actual process stop/restart | Passed; visit version and selected questions preserved |
| Alternate backend port via frontend proxy | Passed on port 8001 |
| Setup re-run | Passed; existing edits preserved |
| Chromium setup helper | Verified browser launch |

The complete final command was scripts/check.ps1 -Phase 1. It exited successfully and recorded 106.39 seconds for that run. Browser scenarios ran against an isolated local production frontend. The production preview remained available while verification built to .next-check.

The five browser scenarios cover saved selection across refresh/navigation, source-dialog keyboard dismissal and focus restoration, direct routes/mobile overflow, connection-error retry and a rejected stale edit from a second isolated context.

One nonblocking test-library deprecation warning remains: current Starlette recommends httpx2 instead of httpx for TestClient. The tests pass; changing that dependency can be handled when the next phase updates test infrastructure.

## Actual restart evidence

Owned application processes were stopped using scripts/stop.ps1, then restarted with scripts/dev.ps1 -Mode fixture -Production. Backend port changed from 8000 to 8001. The frontend's runtime proxy continued working, and the saved encounter remained at version 13 with the same selected question IDs at that verification moment. Subsequent browser tests legitimately advanced the event version.

Structured evidence: phase-01-restart.json, phase-01-browser-review.json and the successful ignored .local/check-phase-01.json.

## Source reuse and environment

The pinned LiveKit Meet dependency manifest informed the React 18 / Next.js 15 baseline. Next was resolved to 15.5.27. No upstream application source was copied into the product in this phase; selected LiveKit code adaptation begins with the media phase. reuse-manifest.json records the compatibility reference, and dependency-licenses.json records resolved package license metadata.

Docker Desktop's engine remained unavailable despite startup attempts. The official EDB Postgres 17.11 Windows archive was downloaded, pinned by URL and SHA-256, and extracted into ignored project-local tools. The database was initialized and tested directly. No SQLite substitute was used.

Verified runtime: Node 24.19.0, Python 3.12.14, uv 0.12.13, pnpm 11.25.0, Postgres 17.11, Next 15.5.27, React 18.3.1, FastAPI 0.143.0 and SQLAlchemy 2.0.54. Exact dependency resolutions are in pnpm-lock.yaml and uv.lock.

## Browser evidence

Captured and visually inspected:

- phase-01-prepare-desktop.png
- phase-01-prepare-mobile.png
- phase-01-visit-desktop.png
- phase-01-follow-up-desktop.png
- phase-01-source.png
- phase-01-unavailable-mobile.png

Desktop viewport: 1440 × 1040. Mobile viewport: 390 × 844. Page screenshots include full pages; the modal screenshot captures the visible viewport. The mobile source-button focus outline is intentional keyboard focus.

The ordinary pages had no console/request errors in the final capture. The error screenshot deliberately aborted API traffic; that expected browser resource error is recorded separately from normal-page failures.

The Codex browser-control entrypoint could not initialize its kernel assets. Browser verification used the installed local Chromium through Playwright and direct screenshot inspection. A Codex preview-open request was queued; this report does not claim the user-visible panel was observed.

## Current scope and next work

This is a local synthetic-data foundation. Participant admission, private/shared access, live calls, AI interpretation and administrative execution are subsequent phases. Phase 1's loopback API is intentionally a fictional-data development interface and is not a patient-data deployment.

Next: Phase 2 — server-authorized identities, invitations, audience-scoped context and evidence, preparation approval and role-isolated view tests.

