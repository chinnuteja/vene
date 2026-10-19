"""One authorization boundary for views, retrieval and future model inputs.

Evidence text is data: it is never parsed as a permission or instruction.
"""
from bring_vene.domain.contracts import ContextView, EncounterView, Role


class ContextAdapter:
    def view(self, source: EncounterView, role: Role, membership_id=None) -> EncounterView:
        view = source.model_copy(deep=True)
        view.viewer_role = role
        if role == "patient":
            return view
        view.understanding = None
        view.coverage = None
        view.title = f"Visit with {view.clinician}"
        view.priorities = [p for p in view.priorities if
                           view.preparation_approved and p.approved and p.selected and role in p.audiences]
        visible_sources = {e.id for e in view.evidence if role in e.audiences}
        view.plan = [p for p in view.plan if role in p.audiences and
                     (p.origin == "preparation" or bool(p.evidence_refs) and set(p.evidence_refs) <= visible_sources)]
        view.evidence = [e for e in view.evidence if role in e.audiences]
        visible = {e.id for e in view.evidence}
        for item in [*view.priorities, *view.plan]:
            item.evidence_refs = [ref for ref in item.evidence_refs if ref in visible]
            item.audiences = [role]
        for priority in view.priorities:
            if priority.answer_refs and (role not in priority.answer_audiences or not set(priority.answer_refs) <= visible):
                priority.status = "open"
                priority.answer_detail = None
                priority.answer_refs = []
            priority.answer_audiences = [role] if role in priority.answer_audiences else []
        for item in view.evidence:
            item.audiences = [role]
        view.suggestions = [s for s in view.suggestions if role == "family" and s.author_id == membership_id]
        return view

    def context(self, source: EncounterView, role: Role, membership_id=None) -> ContextView:
        view = self.view(source, role, membership_id)
        return ContextView(encounter_id=view.id, consent_epoch=view.consent_epoch, audience=role,
                           priorities=view.priorities, plan=view.plan, evidence=view.evidence)


context_adapter = ContextAdapter()
