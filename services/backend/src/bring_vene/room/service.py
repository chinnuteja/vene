"""One phone in the room.

The patient's own authenticated device carries the room microphone. Before any processing,
the patient declares who is present, gives the disclosure, and records each person's spoken
agreement; all of that is patient-attested and labelled so. Diarization labels become names
only when the patient maps them, and a mapped name is attribution for the transcript, never
that person's authority: a clinician's spoken words cannot confirm a step or issue an order.
"""
import re
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from bring_vene.domain.contracts import EncounterView
from bring_vene.domain.service import DomainError, utc_now
from bring_vene.execution.service import access, patient
from bring_vene.persistence.models import (CallConnectionRecord, CallRecord, EncounterRecord, EvidenceRecord, MembershipRecord,
    RoomSessionRecord, SpeakerAttributionRecord, SpeechDeliveryRecord, TranscriptSourceRecord)
from bring_vene.room.contracts import Person, RoomView, SpeakerView

MAX_PEOPLE = 6
SELF_SPEECH_WINDOW = 8  # seconds after Vene's last audio during which an echo can still finalize


def disclosure(patient_name):
    return ('Hello, I am Vene, ' + patient_name + "'s assistant. With everyone's agreement I will listen to help " +
            patient_name + ' keep track of questions and next steps. No audio is recorded. You can ask me to stop at any time.')


def lock(session, visit_id):
    encounter = session.scalar(select(EncounterRecord).where(EncounterRecord.id == visit_id).with_for_update())
    if not encounter:
        raise DomainError(404, 'Visit not found.')
    return encounter, EncounterView.model_validate(encounter.projection), session.get(RoomSessionRecord, visit_id)


def is_active(room):
    return bool(room and room.state == 'active')


def gate_open(session, visit_id):
    """Room mode closes the processing gate until every declared person agreed after the disclosure."""
    room = session.get(RoomSessionRecord, visit_id)
    return room is None or room.state in {'active', 'off'}


def settle(room):
    people = room.content['people']
    if any(p['agreed'] is False for p in people):
        room.state = 'declined'
    elif room.content.get('disclosure_at') and people and all(p['agreed'] is True for p in people):
        room.state = 'active'
    else:
        room.state = 'setting_up'


def changed(session, encounter, view, room):
    """Who is present or what they agreed changed: a consent change for every processing path."""
    room.revision += 1
    room.updated_at = utc_now()
    call = session.get(CallRecord, view.id)
    from bring_vene.voice.service import bump
    if call:
        # Pause the intended processing path, not just the voice; resuming needs the current room.
        call.manual_pause = True
        bump(encounter, call)
    else:
        projection = dict(encounter.projection)
        projection['consent_epoch'] = projection.get('consent_epoch', 0) + 1
        projection['updated_at'] = utc_now().isoformat()
        encounter.projection = projection
        encounter.updated_at = utc_now()


def start(engine, visit_id, token, csrf, request):
    with Session(engine) as session, session.begin():
        encounter, view, room = lock(session, visit_id)
        _, _, member, credential = access(session, visit_id, token, csrf)
        patient(member)
        people = [{'id': str(uuid4()), 'name': p.name.strip(), 'role': p.role, 'agreed': None, 'attested_at': None}
                  for p in request.people]
        if not room:
            room = RoomSessionRecord(encounter_id=visit_id, session_hash=credential.token_hash, state='setting_up',
                                     content={}, revision=0, updated_at=utc_now())
            session.add(room)
        room.session_hash = credential.token_hash
        room.content = {'people': people, 'disclosure_at': None, 'suppressed': room.content.get('suppressed', 0)}
        room.state = 'setting_up'
        changed(session, encounter, view, room)


def add_person(engine, visit_id, token, csrf, request):
    with Session(engine) as session, session.begin():
        encounter, view, room = lock(session, visit_id)
        _, _, member, _ = access(session, visit_id, token, csrf)
        patient(member)
        if not room or room.state == 'off':
            raise DomainError(409, 'Start in-room mode first.')
        if len(room.content['people']) >= MAX_PEOPLE:
            raise DomainError(409, 'In-room mode supports up to six people.')
        # A new arrival needs the disclosure and their own agreement before processing resumes.
        room.content = {**room.content, 'people': [*room.content['people'], {'id': str(uuid4()), 'name': request.name.strip(),
            'role': request.role, 'agreed': None, 'attested_at': None}], 'disclosure_at': None}
        settle(room)
        changed(session, encounter, view, room)


def give_disclosure(engine, visit_id, token, csrf):
    with Session(engine) as session, session.begin():
        encounter, view, room = lock(session, visit_id)
        _, _, member, _ = access(session, visit_id, token, csrf)
        patient(member)
        if not room or room.state == 'off':
            raise DomainError(409, 'Start in-room mode first.')
        room.content = {**room.content, 'disclosure_at': utc_now().isoformat()}
        settle(room)
        changed(session, encounter, view, room)


def attest(engine, visit_id, token, csrf, request):
    with Session(engine) as session, session.begin():
        encounter, view, room = lock(session, visit_id)
        _, _, member, _ = access(session, visit_id, token, csrf)
        patient(member)
        if not room or room.state == 'off':
            raise DomainError(409, 'Start in-room mode first.')
        if not room.content.get('disclosure_at'):
            raise DomainError(409, 'Give the disclosure before recording agreement.')
        people = [dict(p) for p in room.content['people']]
        person = next((p for p in people if p['id'] == request.person_id), None)
        if not person:
            raise DomainError(404, 'Person not found.')
        person['agreed'] = request.agreed
        person['attested_at'] = utc_now().isoformat()
        room.content = {**room.content, 'people': people}
        settle(room)
        changed(session, encounter, view, room)


def end(engine, visit_id, token, csrf):
    with Session(engine) as session, session.begin():
        encounter, view, room = lock(session, visit_id)
        _, _, member, _ = access(session, visit_id, token, csrf)
        patient(member)
        if room and room.state != 'off':
            room.state = 'off'
            changed(session, encounter, view, room)


def names(room, member_name):
    people = {p['id']: p for p in (room.content['people'] if room else [])}
    def name(person_id, label):
        if person_id == 'patient':
            return member_name
        if person_id in people:
            return people[person_id]['name']
        return 'Unattributed speaker ' + str(int(label[1:]) + 1)
    return people, name


def speaker_for(session, visit_id, room, label, member_name):
    mapping = session.get(SpeakerAttributionRecord, (visit_id, label))
    _, name = names(room, member_name)
    person_id = mapping.person_id if mapping else None
    attribution = 'session' if person_id == 'patient' else 'patient_attested' if person_id else 'unattributed'
    return name(person_id, label), attribution


def words(text):
    return re.findall(r"[a-z0-9']+", text.lower())


def self_speech(session, visit_id, text):
    """The phone's speaker can play Vene into its own microphone. Browser echo cancellation is the
    first defence; this drops a finalized turn that mostly repeats what Vene was just saying."""
    heard = set(words(text))
    if len(heard) < 3:
        return False
    since = utc_now().timestamp() - SELF_SPEECH_WINDOW
    for delivery in session.scalars(select(SpeechDeliveryRecord).where(SpeechDeliveryRecord.encounter_id == visit_id,
                                                                       SpeechDeliveryRecord.first_audio_at.is_not(None))):
        end = (delivery.stopped_at or utc_now()).timestamp()
        if end < since:
            continue
        spoken = set(words(delivery.content.get('text', '')))
        if spoken and len(heard & spoken) / len(heard) >= 0.6:
            return True
    return False


def ingest(session, visit_id, member, label, text, origin, settings, utterance_id=None):
    """A finalized room turn. Called with the visit locked, after the processing gate admitted it."""
    from bring_vene.understanding.service import lock as understanding_lock, add_source
    encounter, row, view = understanding_lock(session, visit_id)
    room = session.get(RoomSessionRecord, visit_id)
    if not is_active(room):
        return None
    if self_speech(session, visit_id, text):
        room.content = {**room.content, 'suppressed': room.content.get('suppressed', 0) + 1}
        return None
    speaker, attribution = speaker_for(session, visit_id, room, label, member.name)
    return add_source(session, encounter, row, view, member, text, origin, settings, utterance_id,
                      speaker=speaker, label=label, attribution=attribution)


def fixture_utterance(engine, visit_id, token, csrf, request, settings):
    if not (settings.bring_vene_development and settings.bring_vene_mode == 'fixture'):
        raise DomainError(404, 'Not found.')
    with Session(engine) as session, session.begin():
        _, view, member, _ = access(session, visit_id, token, csrf)
        patient(member)
        room = session.get(RoomSessionRecord, visit_id)
        if not is_active(room):
            raise DomainError(409, 'Everyone in the room needs to agree before Vene can process what is said.')
        ingest(session, visit_id, member, request.label, request.text, 'fixture', settings)


def map_label(engine, visit_id, token, csrf, request, settings):
    """Attribute a diarization label. Re-attribution corrects every source with that label and
    invalidates interpretations built on it, exactly as a source correction does."""
    from bring_vene.understanding.service import lock as understanding_lock, invalidate, stamp
    with Session(engine) as session, session.begin():
        encounter, row, view = understanding_lock(session, visit_id)
        _, _, member, _ = access(session, visit_id, token, csrf)
        patient(member)
        room = session.get(RoomSessionRecord, visit_id)
        if not room or room.state == 'off':
            raise DomainError(409, 'Start in-room mode first.')
        people, _ = names(room, member.name)
        if request.person_id not in (None, 'patient') and request.person_id not in people:
            raise DomainError(404, 'Person not found.')
        mapping = session.get(SpeakerAttributionRecord, (visit_id, request.label))
        if mapping and mapping.person_id == request.person_id:
            return
        if not mapping:
            mapping = SpeakerAttributionRecord(encounter_id=visit_id, label=request.label, person_id=None, attested_at=utc_now())
            session.add(mapping)
        mapping.person_id = request.person_id
        mapping.attested_at = utc_now()
        speaker, attribution = speaker_for(session, visit_id, room, request.label, member.name)
        changed_sources = False
        for source in session.scalars(select(TranscriptSourceRecord).where(TranscriptSourceRecord.encounter_id == visit_id)):
            if source.content.get('speaker_label') != request.label or source.content.get('speaker') == speaker:
                continue
            evidence = next(e for e in view.evidence if e.id == source.id)
            source.history = [*source.history, source.content]
            source.version += 1
            evidence.speaker = speaker
            evidence.attribution = attribution
            evidence.title = evidence.title.rsplit(' · ', 1)[0] + ' · ' + speaker
            evidence.version = source.version
            source.content = evidence.model_dump(mode='json')
            session.get(EvidenceRecord, source.id).content = source.content
            invalidate(view, source.id)
            changed_sources = True
        if changed_sources:
            row.revision += 1
            row.state = 'queued' if row.enabled else 'off'
            view.consent_epoch += 1
            stamp(encounter, row, view, settings)


def state(engine, visit_id, token, settings):
    with Session(engine) as session, session.begin():
        _, view, member, _ = access(session, visit_id, token)
        room = session.get(RoomSessionRecord, visit_id)
        current = room.state if room else 'off'
        text = disclosure(view.patient.preferred_name)
        if member.role != 'patient':
            # Guests learn only whether in-room mode is on; names, attestations and labels stay with the patient.
            return RoomView(state=current, disclosure=text)
        people = [Person.model_validate(p) for p in (room.content['people'] if room else [])]
        _, name = names(room, member.name)
        speakers = {}
        for source in session.scalars(select(TranscriptSourceRecord).where(TranscriptSourceRecord.encounter_id == visit_id)
                                      .order_by(TranscriptSourceRecord.finalized_at)):
            label = source.content.get('speaker_label')
            if label:
                speakers[label] = source.content['text'][:120]
        mappings = {m.label: m for m in session.scalars(select(SpeakerAttributionRecord).where(
            SpeakerAttributionRecord.encounter_id == visit_id))}
        views = []
        for label in sorted(set(speakers) | set(mappings)):
            person_id = mappings[label].person_id if label in mappings else None
            views.append(SpeakerView(label=label, person_id=person_id, name=name(person_id, label),
                                     attributed=bool(person_id), last_heard=speakers.get(label)))
        return RoomView(state=current, people=people, disclosure=text,
            disclosure_at=room.content.get('disclosure_at') if room else None, speakers=views,
            suppressed_self_speech=room.content.get('suppressed', 0) if room else 0,
            fixture_input_enabled=settings.bring_vene_development and settings.bring_vene_mode == 'fixture')


def room_track(engine, visit_id, connection_id):
    """True when this connection is the patient's device carrying the room microphone."""
    with Session(engine) as session:
        room = session.get(RoomSessionRecord, visit_id)
        connection = session.get(CallConnectionRecord, connection_id)
        member = session.get(MembershipRecord, connection.membership_id) if connection else None
        return bool(is_active(room) and connection and connection.session_hash == room.session_hash and member
                    and member.role == 'patient')
