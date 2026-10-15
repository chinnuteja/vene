# Bring Vene workspace instructions

## Task and scope

The user accepted Bring Vene and authorized Codex in this chat to implement it using IMPLEMENTATION_PLAN.md. Do not reopen idea selection or ask for routine permission between phases. Do not delegate to subagents unless the user subsequently asks.

Read BUILD_STATUS.md first, then the relevant phase in IMPLEMENTATION_PLAN.md. VENE_COMPANY_CONTEXT.md distinguishes company facts from our hypotheses. Earlier research proposals are historical; the current accepted product is patient-controlled participation in a healthcare conversation with practical follow-through.

## Execution

- Preserve existing research and user changes. Inspect the checkout before editing.
- Build the actual product in the planned workspace layout; do not create a disconnected throwaway demonstration.
- Use the same domain services in fixture and live configurations. Never silently turn a failing live integration into a scripted success.
- Implement, run meaningful tests, start the local app, inspect it in a browser and fix observed failures before marking a phase passed.
- Record commands/results, local browser evidence, provider configuration and missing checks in BUILD_STATUS.md and docs/qa.
- Continue independent work when a specific credential or environment gate is unavailable; do not claim that gate passed.
- No deployment, founder messaging, real-patient data or real healthcare calls during the local flagship phases.
- Do not claim production, clinical or regulatory readiness from passing prototype tests.

## Code reuse

Prefer maintained SDK/library dependencies and selective adaptation of audited examples. Record copied source origins, exact commits, licenses/notices and changes in reuse-manifest.json and THIRD_PARTY_NOTICES.md.

The research/bring-vene-sources snapshots are reference material, not executable application code. Do not copy example authentication, transcript logging, broad transcript publishing or public default-agent settings unchanged. Follow the repository audit's license limitations.

## Product invariants

- Server-authorized participant identity and scope control retrieval, views, speech and dispatch.
- Private data must be absent from unauthorized API/SSE payloads, not merely hidden in the UI.
- Clinical decisions remain with the responsible human; evidence, interpretation, approval, required order and external completion remain distinct.
- Transcript/model outputs are proposals, not authorization.
- Corrections invalidate dependent pending proposals/actions. Do not pretend a local rollback reverses an external booking.
- Pause stops the intended processing path; a silenced voice alone is not a processing pause.
- Keep raw audio unrecorded by default and sensitive transcript content out of ordinary logs.
- Clearly label sandbox integrations and preserve actual receipts/status.

## Local operation

Use project-owned launchers, isolated test databases and the verified local runtimes. Never terminate unrelated processes or stop unrelated containers to free a port. On Windows, launch background helpers hidden when Start-Process is used.

Future test and startup commands in IMPLEMENTATION_PLAN.md are requirements to implement, not evidence that scripts already exist.

