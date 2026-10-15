# Phase 2 — preparation, evidence and audience controls

Checked on 13 October 2026 (Asia/Calcutta). Synthetic local fixture only.

## Delivered behavior

- Patient, clinician and family memberships exist on the server. Single-use opaque invitations expire after 15 minutes. Tokens are hashed in Postgres; session cookies are HttpOnly and SameSite=Strict, with an eight-hour server expiry. The same-origin proxy checks mutation origins; authenticated writes also require a per-session CSRF token.
- The explicit local development launcher uses the same invitation redemption path. Fixture admission is disabled by default and unavailable in live mode. Application defaults use Secure cookies; the loopback HTTP launcher explicitly disables that attribute.
- Maria selects and edits questions, chooses each audience and approves the list. Changing a question invalidates list approval. Sources and existing next-step context have separate sharing controls. Accepting a family suggestion creates a private draft; rejecting one leaves the list unchanged.
- ContextAdapter constructs private and shared inputs independently. Guest views and evidence lookups contain only permitted records. Quoted source text cannot grant permissions.
- Authenticated SSE publishes a filtered initial snapshot and filtered replacement updates. It never exposes the private event journal, including on reconnection. Full replacements remove withdrawn records and their source references from cached UI state. Open source dialogs close when their source disappears.
- Membership withdrawal revokes all existing sessions and unused invitations. A new explicit invitation can restore membership without resurrecting old credentials. Audience changes and membership revocation/restoration advance the consent epoch.
- Migration 0002 adds persistent membership, invitation and session tables, indexed foreign keys and actor binding for command replay. Seed updates preserve existing selections and sharing choices.

Primary application files: services/backend/src/bring_vene/{auth.py,main.py,domain/context.py,domain/service.py,domain/contracts.py}, apps/web/src/components/{access-gate.tsx,preparation-controls.tsx,visit-workspace.tsx}, and the generated contracts under packages/contracts.

## Checks actually run

| Check | Result |
|---|---|
| scripts/check.ps1 -Phase 2 | Passed: real Postgres migrations/tests, contract drift, TypeScript, production build, Chromium |
| Backend tests | 33 passed: 18 audience/auth scenarios plus 15 foundation regressions |
| Chromium against isolated production frontend | 10 passed: five audience/invitation/sign-out scenarios plus five foundation regressions |
| Follow-up backend test run after final authorization changes | 33 passed |
| Follow-up production Chromium run against restarted final backend | 9 passed, before the final sign-out addition |
| Final full Phase 2 check including sign-out | 33 backend + 10 Chromium; contracts/type/build passed |
| Final browser runner with its own API and dedicated test database | 10 passed; working-preview data unaffected |
| Local developer launcher used through the browser | Passed |
| Desktop/mobile preparation, visit, next steps and source dialog | Inspected; no horizontal overflow or normal-page errors |
| Actual owned API/web process restart | Session membership, approved preparation and saved version persisted; original approval restored |

The multi-role test approved two questions for Dr. Chen, kept the private canary unshared, rejected Elena's suggestion, revoked a source with its dialog open, and withdrew Elena's membership while her window remained open. Captured guest REST and actual EventSource messages contained zero canary leaks. Direct private-source lookup returned 404; role spoofing did not expand the view. Expired, replayed and revoked invitations are covered in backend tests; an actually expired invitation and a replayed link were also exercised in Chromium. Concurrent redemption admits exactly one session. Sign-out removes the cookie and denies further visit access; its client refreshes the session CSRF token before ending the session.

Browser testing found and repaired an internal localhost/browser 127.0.0.1 origin mismatch and an equal-version SSE snapshot that could overwrite an optimistic selection. Scope checkboxes await the server before displaying a changed permission; browser tests assert the saved result.

Evidence:

- phase-02-network-review.json — captured guest payload checks and live revocation results.
- phase-02-browser-review.json — normal-page errors, viewport and launcher results.
- phase-02-restart.json — actual process restart results.
- phase-02-{patient,clinician,family}-desktop.png, phase-02-patient-mobile.png, phase-02-revoked.png — multi-role scenario.
- phase-02-{prepare,visit,follow-up}-review.png, phase-02-mobile-review.png, phase-02-source-dialog.png, phase-02-launcher.png — visual review.

Screenshots were opened and inspected using the image viewer. Chromium/Playwright performed the local browser checks. The Codex preview-open request returned queued; this is not evidence that the visible Codex tab was inspected. The earlier unavailable Codex browser-control kernel was not needed for these tests.

## Reuse and references

No upstream application source was copied. Phase 2 reuses the existing UI primitives, source dialog, generated API types, FastAPI, SQLAlchemy, Alembic and Playwright. No new dependency or unrelated memory product was imported. ContextAdapter is an integration boundary for future Vene/Zep retrieval, not a claim that either integration is connected.

[OWASP session guidance](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) informed opaque tokens and cookie attributes; [OWASP CSRF guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) informed the mutation-origin and token checks. These are design references, not copied source.

## Limits and next phase

The preview runs at http://127.0.0.1:3000/dev; API 8001 and project-local Postgres 5432. Local membership roles are fictional invitation assignments, not verification of a clinician's professional identity. Source sharing is role-based within this seeded visit. Already delivered information cannot be recalled; the next stream publication checks current access and clears withdrawn UI state. SSE is a bounded polling transport for this local phase, not a measured high-scale deployment.

One nonblocking Starlette/httpx TestClient deprecation warning remains in test output. No voice/model provider gate is required for Phase 2. Calls, media consent, transcription and live model processing belong to Phase 3 onward and have not been claimed as connected. No deployment, real-patient data, healthcare-service calls or founder messaging occurred.

Next: Phase 3, authenticated multiparty media and the consent/pause/resume lifecycle.

