"""Read-only client for the NHS England Patient Flags Service (FHIR R4).

Scope for this POC is the read half only: ``GET /PatientFlag``. The sandbox is
open-access (no OAuth), so this client sends only the NHS context headers and a
correlation id. The auth header injection (CIS2 / signed-JWT token broker) is a
deliberate future seam, marked below, so the lift to INT/Production is additive
rather than a rewrite.
"""

from __future__ import annotations

import uuid
from urllib.parse import urlsplit

import requests

from .config import SANDBOX_BASE_URL, UserContext
from .models import FHIRResource

# Scheme + host of the sandbox, derived from the configured URL so the
# placeholder-identity guard tracks the configured sandbox rather than a literal.
_SANDBOX_ORIGIN = f"{urlsplit(SANDBOX_BASE_URL).scheme}://{urlsplit(SANDBOX_BASE_URL).netloc}"


class PatientFlagsClient:
    def __init__(
        self,
        base_url: str = SANDBOX_BASE_URL,
        user_context: UserContext | None = None,
        timeout: float = 20.0,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        # Refuse to send placeholder identity headers to non-sandbox environments:
        # INT/Production calls must carry a real CIS2-derived UserContext (one with
        # is_placeholder=False). This guards the default context too.
        context = user_context or UserContext()
        if context.is_placeholder and not self.base_url.startswith(_SANDBOX_ORIGIN):
            raise ValueError(
                "A real UserContext (CIS2-derived, is_placeholder=False) is required for "
                "non-sandbox environments; refusing to send placeholder identity headers."
            )
        self.user_context = context
        self.timeout = timeout
        self.session = session or requests.Session()

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/fhir+json",
            # Correlation id; NHS APIs echo this for tracing.
            "X-Request-ID": str(uuid.uuid4()),
        }
        headers.update(self.user_context.headers())
        # FUTURE (INT/Prod): inject Authorization: Bearer <token> and apikey
        # here via a token broker (CIS2 user-restricted or signed-JWT app-
        # restricted). No-op against the open-access sandbox.
        return headers

    def get_patient_flags(self, nhs_number: str, code: str | None = None) -> FHIRResource:
        """GET /PatientFlag for a patient.

        :param nhs_number: 10-digit NHS number.
        :param code: optional flag category (e.g. ``NRAF`` for Reasonable
            Adjustment). Omit to return flag indicators only.
        :returns: the parsed FHIR ``Bundle`` on success, or an
            ``OperationOutcome`` resource on an API-level error.
        """
        params = {"patient": nhs_number}
        if code:
            params["code"] = code
        response = self.session.get(
            f"{self.base_url}/PatientFlag",
            params=params,
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

