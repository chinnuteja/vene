# Bring Vene

**Vene in the visit, on the patient's side.**

*Unofficial concept, not affiliated with or endorsed by Vene. All people, health information, offices, health plans and bookings are fictional.*

| | |
|---|---|
| **Live demo** | https://bring-vene-concept.onrender.com/demo |
| **Complete workspace** | https://bring-vene-concept.onrender.com/dev (opens the full app for each role) |
| **Code** | https://github.com/chinnuteja/vene, branch `claude/venehealth-codebase-review-hop817` |
| **Run locally** | `./scripts/dev.sh` (Linux/macOS) or `scripts\dev.ps1` (Windows), then open http://127.0.0.1:3000/demo |

The hosted demo runs on Render's free plan and sleeps when idle. Open it a minute before showing it; the first load can take 30–60 seconds.

---

## 1. The problem

Vene already handles the hard part after a visit: referrals, refills, coverage, bills and keeping family informed, by phone and text. But it starts from what the patient *remembers* the doctor said, and it usually discovers problems *after* everyone has left the room:

- The doctor says "labs within three days". The patient's usual lab has nothing until Friday. Nobody finds out until the patient calls.
- The doctor orders an MRI. The patient books it, shows up, and learns at the front desk that insurance needs prior authorization.
- Instructions are half-remembered, so the follow-through is built on a guess.

Each of these turns into phone tag that Vene, the patient or the family has to fix later, if they catch it at all.

## 2. The idea

Put Vene *in the visit*, working for the patient. With everyone's agreement, Vene:

1. **brings what was left unfinished** from earlier visits, as a list the patient approves;
2. **listens to the actual conversation** and turns what the doctor said into sourced next steps;
3. **privately checks whether those steps will work** (calendars, coverage, documents) and tells only the patient, while the doctor can still change the plan;
4. **starts every errand before the patient leaves**, each with its own approval and office receipt;
5. **hands off** to the follow-through Vene already does: family updates, rides, and open questions carried into the next visit.

The new part is steps 2–3: catching the obstacle *in the room*. Steps 4–5 show how it feeds what Vene already sells.

## 3. How we thought about it

These product rules shaped every screen and every API:

- **The patient owns it.** Vene works for the patient. The clinician and family see only what the patient chooses to share, and the server enforces it: unshared data is absent from their API and live-update payloads, not just hidden on screen.
- **Nothing happens without agreement.** Vene processes audio only after the people present agree. Pause stops processing itself, not just the voice. Raw audio is never recorded.
- **Humans make the decisions.** What Vene heard is a *proposal*. The clinician's order, the patient's approval and the office's confirmation are separate facts, and each is recorded on its own.
- **Private first, then shared.** When Vene finds a problem, it tells the patient privately first. She decides whether to raise it, and what to share to do so.
- **Proof, not promises.** Every errand ends with a real receipt from the office. A booking is shown as confirmed only when the office has confirmed it, and "confirmed" never means "the appointment happened".
- **Corrections propagate.** If what was heard is corrected, everything built on it is invalidated. A local undo never pretends to cancel an external booking.
- **Honest labels.** Sample words are labelled as typed, not spoken. Sandbox offices are labelled as sandbox. A failing live provider is shown as failing, never quietly replaced by a script.

## 4. The demo, chapter by chapter

`/demo` shows one fictional visit (Maria Alvarez with Dr. Chris Chen, Monday 19 October 2026) on a single screen:

- **left:** Maria's phone, in a phone frame;
- **right:** Dr. Chen's window;
- **optional third pane:** her daughter Elena, via **Show Elena's view**.

Each pane is a real, separately authenticated session. A chapter bar at the top moves through the visit, with **Next** leading the way. Each chapter has a one-line explanation. Every **Start demo** creates a fresh visit with its own calendars and history.

### Chapter 1 · Before: "Bring what was left unfinished"

- Maria's phone opens with **"Vene found 3 things worth bringing up"**, from her July visit and a pharmacy message:
  - fasting labs that were never done;
  - an unanswered question about her blood-pressure log;
  - a pending refill.

  Each shows where it came from and how long ago.
- She taps **Add 3 to my visit list**, then **Approve my visit list**.
- Dr. Chen's window updates live, showing only the approved questions. Her private note about morning availability never reaches his session.

### Chapter 2 · During: "Catch the obstacle while everyone is still here"

- Maria taps **Allow private checks**.
- Dr. Chen says: *"Please get labs done within three days. We can send the lab order today."* In the hosted demo this is a labelled **Say this** button; locally with live providers it is spoken into the microphone.
- Vene turns it into a sourced step: *Labs, within three days*. It checks the lab calendars against Maria's usual lab.
- **Only Maria sees:** *"There's a way to get this done on time. Riverside Lab has no slot before Friday — Northside has Thursday 9am."* Dr. Chen's session contains neither her preference nor this cue.
- Maria taps **Raise this with Dr. Chen**. This shares just the instruction and her lab preference, and lets Vene raise the fact aloud.
- Dr. Chen sees *"Northside is in time"* and taps **Confirm & send lab order**. That is his decision; the model cannot issue an order.
- Maria taps **Book Thursday 9am**. *"One less thing to chase"* appears, with the lab's actual receipt.

### Chapter 3 · Before you leave: "Start every errand before you reach the car"

- Later in the visit, Dr. Chen mentions an MRI at Lakeside Imaging and a new prescription at Main Street Pharmacy.
- **Only Maria sees:** *"Your plan needs to approve this first. Evergreen Basic requires prior authorization for this imaging."* Without this she would find out at the front desk.
- She taps **Ask Dr. Chen now**. He answers **The office will submit prior authorization**, which prepares a health-plan submission; Maria still approves sending it.
- Maria taps **Check all with the offices**. One checklist shows lab, imaging, pharmacy and health plan, each with its own status:
  - *Waiting for Dr. Chen's imaging order*
  - *Ready for your approval*
  - *Confirmed · receipt from the pharmacy*
- Dr. Chen confirms and sends the imaging order and the prescription.
- Maria approves the ready steps. The MRI waits for the plan's approval, then follows.
- It ends with **"All set before you leave."**: four receipts.

### Chapter 4 · After: "Keep the thread after the door closes"

- **Send to Elena:** Maria shares only the booked steps (what, when and the office's answer). Elena's pane receives *"Update from Maria"*. Nothing about Maria's questions or health goes with it.
- **Ask Elena to drive:** Elena sees *"Maria asks: can you drive? Thursday 9am, Northside"* and answers **Yes, I can** herself. Maria sees *"Elena said yes."*
- **Still unanswered today** lists questions not resolved in this visit. Vene will bring them to the next visit's preparation.
- Dr. Chen's window shows *"What Maria is leaving with"*: every step with its receipt, and no call-backs needed.

The whole tour takes about three minutes; the 104-second walkthrough video covers the same path.

## 5. What the UI looks like

- **Landing page (`/demo`).** Calm sage-green and cream palette with serif headlines: *"Don't take the whole visit home."*
  - A tilted phone mock-up shows the private cue.
  - One **Start demo** button.
  - Below it, four cards (Before, During, Before you leave, After) describe the whole product.
  - An unofficial-concept banner sits at the top.
- **Demo stage.**
  - Large chapter title and a one-line explanation.
  - A numbered chapter bar with ticks for finished chapters, and a dark-green **Next** button.
  - Maria's phone (about 400 px) beside Dr. Chen's browser-style window.
- **Cards.**
  - Private cues: soft green, or warm sand for coverage problems.
  - Clinician decisions: pale green panels with one primary button.
  - Checklists: an icon per state (empty, clock, check, alert), then the place, the title, one plain status sentence, and the slot and a short receipt ID when confirmed.
- **Phone width.** Everything stacks at 390 px with no sideways scrolling.
- **Labels stay small and plain**, for example *Sample visit · no microphone* and *Fictional offices and health plan. Nothing real is contacted.*

## 6. Beyond the demo: the complete workspace

The demo uses the same services as the full app at `/prepare`, `/visit` and `/follow-up`. Open it through `/dev`, which issues an invitation for each role. The full app adds:

- **Real voice calls:** LiveKit rooms where each participant agrees separately, Vene joins as a visible participant, and pause, mute and silence are separate controls. Speech goes through Deepgram, the model and Cartesia.
- **One phone on the table:**
  - Maria lists who is present, reads or plays a disclosure, and records each person's agreement.
  - Voices are separated anonymously; she names each ("That's Dr. Chen").
  - A name is attribution only and never gives that person authority.
  - Vene ignores its own voice.
  - When someone new arrives, Vene pauses until they agree.
- **Join by phone:** single-use, 15-minute PINs per person. Keypad: 1 agree, 2 decline, 9 pause, 0 resume (patient only). Caller ID is never used as identity.
- **Corrections:** fix a misheard date or owner, and everything built on it is invalidated.
- **After-visit documents:** paste or upload the after-visit summary. Differences from what was said are flagged for the clinician to review.
- **Next-visit preparation:** open questions carry into a new, private preparation.
- **Access control:** invitations, revocation, and live withdrawal of sharing.

## 7. How it's built

| Layer | What we use |
|---|---|
| Frontend | Next.js, React and TypeScript, with types generated from the backend's API contract |
| Backend | FastAPI (Python), Pydantic contracts that reject unknown fields, SQLAlchemy and Alembic migrations |
| Database | PostgreSQL. The visit is a versioned projection; every change is a versioned, idempotent command |
| Live updates | Server-sent events, filtered per person on the server |
| Voice | LiveKit (WebRTC) and LiveKit Agents; Deepgram for speech-to-text; an OpenAI-compatible model (DeepSeek in our tests) for understanding; Cartesia for Vene's voice |
| Offices | A sandbox "office" service with a lab, imaging centre, specialist, pharmacy and health plan, called over real HTTP with its own token, sending signed callbacks |
| Workers | Understanding, in-visit checks, errand dispatch and reconciliation, and family delivery |

**How a sentence becomes a booking:**

1. Speech becomes a sourced transcript line.
2. The model proposes a step (what, who, when, where) and must quote the source. Unsupported details are dropped and flagged for clarification.
3. The patient's standing permission lets the checks worker ask the sandbox offices (availability, coverage, stock, documents). Problems become private cues, and only the right person can answer them.
4. Office lookups need the patient's per-step permission. Each lookup creates a request fingerprinted to that exact step and its sources.
5. The clinician's order and the patient's approval are recorded separately against that fingerprint.
6. An outbox dispatches the request. Timeouts are reconciled with the office before any retry, so a booking is never made twice.
7. The office's receipt is stored and shown. If the step later changes, the old request loses its authority, but its receipt is kept.

**Privacy is enforced in one place.** A context adapter builds each person's view of the visit, and every API response and live update goes through it.

## 8. The API today

All routes are real; the full contract is in `packages/contracts/openapi.json`.

| Area | Routes |
|---|---|
| Sessions and access | `POST /auth/redeem`, `GET /auth/me`, `POST /auth/logout`; invitations, members and revocation under `/encounters/{id}/…` |
| The visit | `GET /encounters/{id}`, `POST …/commands` (choose, edit, share or approve questions; review suggestions), `GET …/stream` (live updates), `GET …/evidence/{id}`, `GET …/context` |
| Memory | `GET …/memory`, `POST …/memory/carry`, `POST …/memory/outcomes` |
| Understanding | `GET …/understanding`, `POST …/understanding/processing` (allow or pause), `…/sources/{id}/correct`, `…/plan/{id}/correct`, `…/retry` |
| In-visit checks | `GET …/feasibility`, `POST …/feasibility/standing` (patient's permission), `POST …/feasibility/obstacles/{id}/resolve` |
| Errands | `GET …/execution`, `POST …/execution/items/{id}/scope` and `…/lookup`, `POST …/execution/actions/{id}/prerequisites` (clinician), `…/approve` and `POST …/execution/approve-ready` (patient) |
| Voice call | `GET …/call`, `POST …/call/admit`, `…/consent`, `…/controls` (pause, resume, silence, end), `…/connections/{id}/verify` and `…/leave` |
| Vene speaking | `GET …/speech`, `POST …/speech/mode`, `…/agreement`, `…/approve`, `…/actions` |
| Room mode | `GET …/room`, `POST …/room/start`, `…/people`, `…/disclosure`, `…/agreements`, `…/speakers`, `…/end` |
| Phone | `POST …/dial-pins` (patient), `POST /integrations/phone/admit` (bridge, token-authenticated) |
| After the visit | `GET …/continuity`; `POST …/continuity/documents` and `…/review`; `…/family-updates` and `…/approve`; `…/next-visit`; `…/delete` |
| Care circle | `GET …/care-circle`, `POST …/care-circle/rides`, `…/rides/{id}/answer` and `…/withdraw` |
| Integrations and health | `POST /integrations/office/results` (signed office callbacks), `GET /health/live`, `GET /health/ready` |
| Demo only | `POST /dev/demo`, `GET /dev/demo-info`, `POST …/demo/turn` (two allow-listed sample lines); disabled outside the fictional configuration |

## 9. What we achieved

- **One working product:**
  - preparation from memory;
  - live, consented voice participation;
  - sourced understanding with corrections;
  - private in-visit checks;
  - lab, imaging, referral, pharmacy and prior-authorization errands with real receipts;
  - family updates and care-circle asks;
  - document comparison and next-visit carry-over;
  - phone-on-the-table room mode and PIN dial-in on the visit side.
- **Tests:**
  - 226 backend tests;
  - 31 browser scenarios, including the four-chapter journey, with checks that private facts are absent from the clinician's and family's actual API payloads;
  - contract, TypeScript and production-build checks.
- **Demo runs:** complete four-chapter tours passed repeatedly both locally and on the public link, ending with four receipts and Elena's reply.
- **Live providers:** a full run of real Deepgram, then the model, then Cartesia, then an approved sandbox booking with its receipt, passed.
  - Twenty live speech trials: Vene's audio starts within 1.62 s (p95) and stops within 243 ms when interrupted.
  - Scripted turns raise an in-visit obstacle in about a second.
- **Real bugs found and fixed while building the journey,** among them:
  - new speech silently un-sharing earlier steps;
  - receipts going stale after sharing;
  - a call-control race;
  - browser connection exhaustion.

## 10. Demo today versus the real product

| | In the demo | In a real deployment |
|---|---|---|
| Dr. Chen's words | Typed sample lines on the public link; live microphone locally | Spoken in the room, heard by Vene in the call or on the phone on the table |
| Understanding | A rule-based sample interpreter on the public link; a real model locally | A real model, with every step quoting its source |
| Offices and plan | A sandbox office service with fictional calendars and rules | Vene's real channels: portals, integrations, or Vene's own calls to offices |
| Clinician's order | A button in Dr. Chen's window | The clinician's own EHR; Vene records the confirmation and follows up |
| Family | A third pane in the browser | A text message and a reply |
| Voice | A device voice preview on the public link; Cartesia locally | Cartesia in the call |

## 11. What is still missing

- **Calls and texts.** Vene's users live on phone and SMS. Two pieces are absent:
  - the telephone bridge itself (PIN admission and keypad handling exist, but no call can come in yet);
  - SMS delivery of updates and approvals.

  This is the most important next step.
- **The clinician side in the real world.** Doctors won't use a separate window. Orders should come from the EHR, with Vene confirming and following up.
- **Real connections** to labs, imaging, pharmacies and health plans. Today these are sandbox services.
- **Live voice for chapters 3–4.** It hasn't been run with live providers. One live obstacle sample took 5 seconds, against a 3-second target.
- **Reliability on Windows.** Call admission and recovery after a media-server restart still fail intermittently.
- **Exception paths.** Cancellation, rescheduling and manual hand-off when an office refuses.
- **Real rooms.** No test with real phones, room acoustics or people talking over each other, and no clinician or patient feedback yet.
- **Production hosting.** The public link is a disposable free-plan demo that resets on restart.

Passing prototype tests does not mean clinical, regulatory or production readiness.

## 12. Running and checking it

- **Setup and run:** `./scripts/setup.sh` once, then `./scripts/dev.sh`. On Windows: `scripts\setup.ps1`, then `scripts\dev.ps1`.
  - Add `--guided` (`-Guided`) for the public-demo configuration.
  - Add `--live-providers` (`-LiveProviders`) for real Deepgram, the model and Cartesia. Keys go in `.env`; see `.env.example`.
- **Full check:** `./scripts/check.sh --all` runs backend tests, contracts, TypeScript, the production build and the browser scenarios.
- **Tour rehearsal:** `DEMO_REHEARSALS=3 node scripts/rehearse-demo.mjs` drives all four chapters against a running preview.

More detail: `README.md`, `docs/DEMO_SCRIPT.md`, `docs/INTEGRATION.md`, `docs/ONE_PAGER.md` and `BUILD_STATUS.md`.
