from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from bring_vene.auth import COOKIE, FIXTURE_MEMBERS, issue_invitation, redeem
from bring_vene.persistence.models import MembershipRecord


def authenticated_client(app, role="patient"):
    engine = app.state.engine
    with Session(engine) as session, session.begin():
        invite = issue_invitation(session, session.get(MembershipRecord, FIXTURE_MEMBERS[role]))
    token, viewer = redeem(engine, invite.token)
    client = TestClient(app)
    client.cookies.set(COOKIE, token)
    client.headers.update({"x-vene-intent": "mutation", "x-vene-csrf": viewer.csrf_token})
    return client
