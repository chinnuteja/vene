"""Administrative errand kinds. One registry; every kind uses the same execution pipeline.

Each errand reserves something an institution offered (a lab or imaging slot, a specialist
intake appointment or a pharmacy pickup window). The institution, the clinician-issued
prerequisite document and the wording people see are the only things that differ.
Eligibility comes from the plan item's kind, never from free text, except for lab steps
saved before kinds existed.
"""
import re
from dataclasses import dataclass

WINDOWS = {'morning': 'morning', 'afternoon': 'afternoon'}


@dataclass(frozen=True)
class Errand:
    kind: str
    institution: str
    place: str            # the institution as people say it
    document: str         # what the clinician must issue before a write
    offered: str          # what the institution offers
    confirmed: str        # receipt wording once the institution confirms
    locations: tuple[str, ...]
    days: tuple[tuple[str, str], ...]  # (ISO day, label)


ERRANDS = {
    'lab': Errand('lab', 'lab', 'lab', 'lab order', 'slot', 'Lab reservation confirmed',
        ('Riverside Lab', 'Harbor Lab', 'Hilltop Lab', 'Northside'),
        (('2026-10-20', 'Tue, Oct 20'), ('2026-10-21', 'Wed, Oct 21'), ('2026-10-23', 'Fri, Oct 23'), ('2026-10-22','Thu, Oct 22'))),
    'imaging': Errand('imaging', 'imaging', 'imaging center', 'imaging order', 'slot', 'Imaging appointment confirmed',
        ('Lakeside Imaging', 'Northgate Imaging'),
        (('2026-10-21', 'Wed, Oct 21'), ('2026-10-22', 'Thu, Oct 22'))),
    'referral': Errand('referral', 'specialist', 'specialist office', 'referral packet', 'intake appointment',
        'Specialist appointment confirmed',
        ('Riverside Cardiology',),
        (('2026-10-27', 'Tue, Oct 27'), ('2026-10-28', 'Wed, Oct 28'))),
    'prescription': Errand('prescription', 'pharmacy', 'pharmacy', 'prescription', 'pickup window', 'Pickup confirmed',
        ('Main Street Pharmacy', 'Harbor Pharmacy'),
        (('2026-10-22', 'Thu, Oct 22'), ('2026-10-23', 'Fri, Oct 23'))),
    # Created only when a clinician says the office will submit it (Phase 10); never proposed by a model.
    'authorization': Errand('authorization', 'plan', 'health plan', 'authorization request', 'review',
        'Prior authorization approved', ('Evergreen Health Plan',), (('2026-10-15', 'Thu, Oct 15'),)),
}
BY_INSTITUTION = {errand.institution: errand for errand in ERRANDS.values()}
LEGACY_LAB = re.compile(r'\b(lab|laboratory|blood)\b', re.I)


def for_item(item):
    if item.kind in ERRANDS:
        return ERRANDS[item.kind]
    if item.kind is None and LEGACY_LAB.search(item.title + ' ' + item.detail):
        return ERRANDS['lab']
    return None


def for_action(content):
    # Rows written before kinds existed are lab reservations.
    return ERRANDS[content.get('kind', 'lab')]


def default_location(errand, item):
    return item.location if item.location in errand.locations else errand.locations[0]
