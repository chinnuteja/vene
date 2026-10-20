# Bring Vene

**Unofficial concept — not affiliated with or endorsed by Vene.**

The visit ends with “get labs done within three days.” Then the patient gets home and discovers their usual lab has nothing until Friday.

Bring Vene catches that practical obstacle while the patient and clinician are still together. It privately compares the deadline, sourced preferences and office calendars, offers an alternative, and helps the patient raise it. The clinician sends the order. The patient approves the reservation. Everyone leaves with the same concrete next step.

Try the [fictional hosted demo](https://bring-vene-concept.onrender.com/demo). It uses sample text and a labelled device voice preview. Actual live voice runs locally.

## Try it in three minutes

Open `/demo`, then **Start demo**. Maria's phone and Dr. Chen's window have separate authenticated server sessions. Tick **Show Elena's view** to add her family pane; she sees only what Maria sends.

The chapter bar walks through one visit:

1. **Before.** Vene reads Maria's July visit and finds what was left open: unfinished labs, an unanswered question and a pharmacy message. She approves her list; Dr. Chen sees only the approved questions.
2. **During.** Dr. Chen asks for labs within three days. Only Maria sees “Riverside Lab has no slot before Friday — Northside has Thursday 9am.” She raises it, Dr. Chen sends the order, and she books it.
3. **Before you leave.** An MRI and a new prescription come up. Vene privately finds that her plan requires prior authorization; Dr. Chen's office takes it on. Every errand checks with its own office, waits for the clinician's part and Maria's approval, and returns its own receipt.
4. **After.** Maria sends Elena only what's booked and asks her for a ride; Elena answers in her own pane. Unanswered questions carry into the next visit.

The fictional visit is Monday, October 19, 2026. Every fresh demo has its own calendars and history. [The three-minute script](docs/DEMO_SCRIPT.md) has the exact clicks.

## Run locally

After the one-time dependency/runtime setup (`scripts/setup.ps1` on Windows or `./scripts/setup.sh` on Linux), use one launch command:

```powershell
scripts\dev.ps1
```

```sh
./scripts/dev.sh
```

Open [the demo](http://127.0.0.1:3000/demo). The launcher prints the configured port. Windows starts and migrates the saved project-owned PostgreSQL cluster without clearing saved visits. Stop this app with `scripts\stop.ps1` / `./scripts/stop.sh`.

For actual Deepgram → model → Cartesia, configure the server-only fields in `.env.example`, then run `scripts\dev.ps1 -LiveProviders` / `./scripts/dev.sh --live-providers`. Provider failures never silently become fixture successes.

For the hosted-style guided experience, use `scripts\dev.ps1 -Guided`. It uses sample text and a labelled device voice preview, with no microphone or claim of LiveKit delivery.

## Real implementation and sandbox boundaries

**Real:** invitation redemption, isolated HttpOnly sessions, server-side audience filtering including SSE, sourced extraction, correction/permission fences, deadline comparisons, independent clinician/order/patient approvals, HTTP sandbox requests, persisted receipts, idempotency and timeout reconciliation.

**Fictional:** people, health information, dates, institutions, availability, orders and reservations. Hosted mode uses the labelled sample-text fixture and browser synthetic voice; actual voice providers run locally. Hosted data is disposable and resets on service restart. No real institution or telephone bridge is connected. A playback receipt does not prove human hearing.

Passing prototype tests does not establish clinical, regulatory or production readiness. Physical acoustics and human acceptance remain unverified. See [BUILD_STATUS.md](BUILD_STATUS.md) for actual results, measured speech speed and the remaining live obstacle-latency limit.

## For the Vene team

[One-page overview](docs/ONE_PAGER.md) · [Integration seams](docs/INTEGRATION.md) · [Three-minute script](docs/DEMO_SCRIPT.md) · [Hosted operation](docs/HOSTING.md)

The integration boundaries fit LiveKit, Deepgram and Cartesia, while permissions and external completion remain in domain services. The demo chapters use the same services as the complete workspace at `/prepare`, `/visit` and `/follow-up` (opened through `/dev` invitations), which adds phone-on-the-table room mode, dial-in, document comparison and next-visit preparation.

Historical research and plans are preserved under [docs/background](docs/background). [Third-party notices](THIRD_PARTY_NOTICES.md) and [reuse manifest](reuse-manifest.json) record adapted code origins and licenses.

## Verification

`scripts\check.ps1 -All` / `./scripts/check.sh --all` runs the isolated database regression, contracts, TypeScript, production build and browser scenarios. Live gates are separate. `DEMO_REHEARSALS=10` with `node scripts/rehearse-demo.mjs` rehearses all four guided chapters against a running preview, saving actual results, screenshots and a video under ignored `.local/evidence`.
