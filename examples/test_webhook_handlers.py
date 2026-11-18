"""
Testing webhook handlers with `onlyfans_sdk.testing` (run with `pytest test_webhook_handlers.py`).

Events are built from the spec's examples and signed like real deliveries, so the
handlers run through the same verification path as in production.
"""

from __future__ import annotations

from onlyfans_sdk import WebhookRouter
from onlyfans_sdk.testing import create_test_event, deliver_webhook, generate_webhook_secret, sign_webhook

SECRET = generate_webhook_secret()
revoked: list[str] = []

router = WebhookRouter(SECRET)
router.on("authorization.revoked", lambda event: revoked.append(event["authorizationId"]))


def test_revocation_handler_runs() -> None:
    event = create_test_event("authorization.revoked", {"authorizationId": "authz_test"})
    router.handle(*sign_webhook(event, SECRET))  # (body, headers)
    assert revoked[-1] == "authz_test"


def test_one_call_helper() -> None:
    deliver_webhook(router, create_test_event("authorization.revoked", {"authorizationId": "authz_2"}))
    assert revoked[-1] == "authz_2"


def test_http_status_for_bad_signature() -> None:
    body, headers = sign_webhook(create_test_event("linked_account.expired"), generate_webhook_secret())
    assert router.handle_http(body, headers) == (401, {"error": "SIGNATURE_MISMATCH"})
