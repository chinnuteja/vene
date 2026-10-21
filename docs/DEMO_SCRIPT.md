# The three-minute tour

Open `/demo` and choose **Start demo**. Maria's phone and Dr. Chen's window each have their own server session. Tick **Show Elena's view** at any point to add her family pane. The chapter bar moves between the four moments of one visit; **Next** always leads to the following one.

## 1. Before · 30 seconds

“Vene read Maria's July visit and her pharmacy message and found what is still open.”

- Maria's phone opens with *Vene found 3 things worth bringing up*. Each item says where it came from.
- Choose **Add 3 to my visit list**, then **Approve my visit list**.
- Dr. Chen's window now shows the approved questions, and only those. Her optional morning note is not sent.

## 2. During · 60 seconds

“The obstacle usually shows up after the visit. Here it shows up while the doctor can still help.”

1. Maria allows private checks.
2. Dr. Chen chooses **Say this**: “Please get labs done within three days. We can send the lab order today.”
   - In local live mode, say it into the agreed microphone instead. Never describe typed sample words as speech recognition.
3. Only Maria sees: “Riverside Lab has no slot before Friday — Northside has Thursday 9am.” Dr. Chen's session does not contain her preference or the cue.
4. **Raise this with Dr. Chen**, then **Confirm & send lab order** in Dr. Chen's window. An extracted instruction is not an order; the clinician still decides.
5. Maria taps **Book Thursday 9am** and opens the receipt.

## 3. Before you leave · 60 seconds

“Later in the visit, an MRI and a new prescription come up.”

1. Dr. Chen chooses **Say this** on the later line.
2. Only Maria sees the cue: “Evergreen Basic requires prior authorization for this imaging.” She chooses **Ask Dr. Chen now**.
3. Dr. Chen answers **The office will submit prior authorization**. This prepares a health-plan submission; Maria still approves it.
4. Maria chooses **Check all with the offices**. Dr. Chen confirms and sends the imaging order and the prescription.
5. Maria approves the ready steps. The MRI waits for the plan's approval, then follows.
6. Every row ends with its own office receipt: *All set before you leave.*

## 4. After · 30 seconds

“Elena gets only what Maria sends.”

- Maria can review the supporting notes Elena will be allowed to open. **Send to Elena** shares the booked steps and those notes, then sends an update containing the step, timing and office outcome. Other private questions and preferences remain unshared.
- **Ask Elena to drive** sends the time and place. Elena answers yes in her own pane.
- *Still unanswered today* lists what Vene will bring to the next visit's preparation.

## Notes

All people, dates, institutions, plans and bookings are fictional. If a provider fails, show the failure honestly.

Select the guided configuration explicitly, or play the recorded walkthrough under `.local/evidence/bring-vene-walkthrough.webm`. The recording is actual UI interaction, not evidence of live-provider performance.

`DEMO_REHEARSALS=3 node scripts/rehearse-demo.mjs` drives all four chapters against a running preview and checks four receipts and the clinician/family payloads for private facts. Add `DEMO_PACE_MS=9000` for reading pauses in the first recording, or `DEMO_VIDEO=0` where Playwright's ffmpeg is not installed. The new 21 October recording is in `.local/evidence/review-local-warm-2026-10-21/`; the uncut recording is preserved alongside a founder copy with initial navigation/loading removed.
