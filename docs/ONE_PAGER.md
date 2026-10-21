**Unofficial concept — not affiliated with or endorsed by Vene**

# Bring Vene: leave with the next step underway

A clinical conversation can be clear while its next step is impossible in practice. “Labs within three days” becomes a Friday-only calendar, an unsigned order and another round of calls after the patient goes home.

Bring Vene extends practical follow-through into the conversation. With patient permission, it compares a sourced instruction with private preferences and administrative facts, catches an obstacle privately, and helps the patient bring it up while the clinician can still resolve their part.

Maria usually uses Riverside Lab. The sandbox calendar has nothing there before Friday; Northside has Thursday 9am, inside the clinician's three-day window. Maria chooses to share the relevant instruction and preference and invites Vene to raise the exact fact. Dr. Chen confirms clinical intent and sends the required order. Maria approves the reservation in one tap. An actual office receipt confirms it.

## How it fits

- **LiveKit** carries the permission-controlled room and approved public audio, without broad transcript publication.
- **Deepgram** supplies live finalized speech locally. Attributed notes remain private until shared.
- **Model interpretation** proposes sourced next steps. It cannot grant permission, make clinical decisions or book a slot.
- **Cartesia** supplies approved contributions locally; current scope is checked before provider generation and audio delivery.
- **Administrative adapters** check availability, coverage and documents, then dispatch after the required human approvals. Each action confirms or reconciles independently.

Separate authenticated patient, clinician and family views make the privacy boundary visible. Source corrections invalidate dependent pending proposals. Local rollback never pretends to reverse an external booking.

The hosted demo uses fictional people and offices, sample-text input and labelled device speech. It demonstrates the same domain services and approvals; it does not test STT or contact a real lab. Actual live voice runs locally. Physical acoustics, production operations and clinical/regulatory readiness remain outside the demonstrated claims.

See [INTEGRATION.md](INTEGRATION.md) for ports, contracts and adapter boundaries, and the [three-minute tour](DEMO_SCRIPT.md).
