# Phase 7 continuity and recovery QA

Date: 14 October 2026. Configuration: original synthetic records, real project-local PostgreSQL/LiveKit/WebRTC and independent HTTP office. Model/STT are finite/unconnected fixtures; TTS is the installed Windows offline voice. No deployment, provider call, real patient or external healthcare contact.

## Implemented

Signed result callbacks have freshness, replay fencing, business correlation and duplicate/late receipt handling. A separate leased callback sender retries lost acknowledgement with a fresh nonce. Field-selected family drafts require explicit digest approval, current scope and membership before dispatch, and actual sandbox receiver acknowledgement/reconciliation. The receiver retains no message text.

Machine-readable PDF/text ingestion has bounded private extraction, original provenance/pages/quotes, limited discrepancy detection and explicit clinician review. Clinical correctness is not inferred. Related unreviewed documents invalidate pending bookings; completed external receipts survive correction. A next visit copies only selected private preparation and no guests/approvals. Deletion blocks unresolved external work and purges derived local data. Operational traces contain allowlisted metadata only, with nonce/trace pruning.

API/execution/voice recovery is tested with an authenticated loopback controller owning exact isolated ChildProcess trees. Persisted follow-through survives; a new worker instance marks interrupted processing and requires manual resume. A delayed heartbeat alone does not falsely pause. Routine cancelled native joins finish their handshake before cleanup, addressing the SDK cancellation hazard referenced in reuse-manifest.json.

## Commands and outcomes

- `uv run --frozen pytest`: final 133 backend tests passed, including 17 continuity and 17 execution cases. A Starlette/httpx TestClient deprecation warning remains; no failed test.
- Contracts, TypeScript and optimized Next.js build passed. Final complete browser gate passed; provider/hardware/performance limits remain explicit.
- The original PDF was generated with bundled ReportLab, rendered using bundled Poppler and visually inspected: one readable fictional page, no clipping. Parser negative cases include malformed, oversized, encrypted and blank/scanned inputs.
- Targeted failures found and fixed: parent/child FK flush ordering; new-document approval fencing; nonce/callback correlation; slow-heartbeat false gaps; worker process-tree ownership. Browser discovery also found local mDNS media negotiation instability; local transport changes are recorded in Phase 8.

Reused package: pypdf 6.20.1 BSD-3-Clause, pinned in uv.lock, with installed license retained. All continuity/outbox/application code is original; existing domain/SDK services are reused. `reuse-manifest.json` and THIRD_PARTY_NOTICES.md record sources.

## Final browser evidence

Focused final two-scenario run passed: workflow (44.4 s) and continuity (24.5 s), 2 passed. phase-07-browser-evidence.json records actual signed HTTP callbacks, no duplicate action, original PDF review without clinical state change, selected-field acknowledged family delivery, owned API/execution restart preserving data, private new-visit credentials/404 for the previous family session, disposable deletion and preserved original visit. Desktop/mobile screenshots were inspected; no horizontal overflow or page errors. Final complete browser suite passed on 15 October: 25 scenarios passed, 2 explicit live/timing gates skipped. See phase-08-final-checks.json.

## Open boundaries

Family delivery is an acknowledged local sandbox inbox, not real messaging or proof of reading. PDF discrepancy matching is limited and requires human review; OCR and clinical correctness are not established. No live provider, physical acoustic or production/clinical gate is claimed passed.

Native SDK recovery is contained with per-room owned process lifetimes (standard Python multiprocessing, maximum four local runtimes). Hard native failure cannot strand another room; domain authority, processing consent, visible gaps and manual resume remain unchanged. Exact old-generation room cleanup preserves end/revocation semantics. Actual server-loss/rejoin passed after the mid-join isolation repair.

Final lifecycle verification also covers the shared log destination across owned child restarts, unique native assistant runtime identities and a 15-second stalled-startup watchdog. Source authority and manual resume remain unchanged. The saved development preview is reviewed separately; no development reset was used.
