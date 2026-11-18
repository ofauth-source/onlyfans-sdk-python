from __future__ import annotations

import asyncio
import base64
import json
import time

import pydantic
import pytest

from onlyfans_sdk import models
from onlyfans_sdk.events import (
    LIFECYCLE_EVENT_TYPES,
    REALTIME_EVENT_TYPES,
    WEBHOOK_EVENT_MODELS,
)
from onlyfans_sdk.webhooks import (
    WebhookRouter,
    WebhookVerificationError,
    parse_webhook_event,
    sign_webhook,
    verify_webhook,
)

SECRET = "whsec_" + base64.b64encode(b"super-secret-key-material-0123456").decode()

REALTIME_EVENT = {
    "eventId": "evt_1",
    "type": "realtime.chat_message.liked",
    "schemaVersion": "1",
    "order": 3,
    "occurredAt": "2026-04-23T14:30:15.143Z",
    "environment": "live",
    "integrationId": "int_1",
    "externalOauthClientId": "client_1",
    "authorizationId": "authz_1",
    "linkedAccountId": "acct_1",
    "test": False,
    "data": {"id": 123, "isLiked": True},
}

REVOKED_EVENT = {
    **REALTIME_EVENT,
    "eventId": "evt_2",
    "type": "authorization.revoked",
    "linkedAccountId": None,
    "data": {"authorization_id": "authz_1", "linked_account_ids": ["acct_1"], "reason": "owner_revoked"},
}


def signed(event: dict, *, ts: int | None = None, secret: str = SECRET, prefix: str = "webhook") -> tuple[bytes, dict]:
    body = json.dumps(event).encode()
    ts = int(time.time()) if ts is None else ts
    headers = {
        f"{prefix}-id": "msg_1",
        f"{prefix}-timestamp": str(ts),
        f"{prefix}-signature": "v1,bm90LWl0 " + sign_webhook(body, "msg_1", ts, secret),
    }
    return body, headers


def test_verify_valid():
    body, headers = signed(REALTIME_EVENT)
    assert verify_webhook(body, headers, SECRET) == REALTIME_EVENT
    assert verify_webhook(body.decode(), headers, SECRET)["eventId"] == "evt_1"


def test_verify_case_insensitive_headers_and_svix():
    body, headers = signed(REALTIME_EVENT, prefix="svix")
    assert verify_webhook(body, headers, SECRET)["type"] == "realtime.chat_message.liked"
    body, headers = signed(REALTIME_EVENT)
    upper = {k.title(): v for k, v in headers.items()}
    assert verify_webhook(body, upper, SECRET)["eventId"] == "evt_1"


def test_bad_signature():
    body, headers = signed(REALTIME_EVENT, secret="whsec_" + base64.b64encode(b"other").decode())
    with pytest.raises(WebhookVerificationError) as info:
        verify_webhook(body, headers, SECRET)
    assert info.value.code == "SIGNATURE_MISMATCH"

    body, headers = signed(REALTIME_EVENT)
    with pytest.raises(WebhookVerificationError) as tampered:
        verify_webhook(body + b" ", headers, SECRET)
    assert tampered.value.code == "SIGNATURE_MISMATCH"


def test_old_and_invalid_timestamp():
    body, headers = signed(REALTIME_EVENT, ts=int(time.time()) - 301)
    with pytest.raises(WebhookVerificationError) as info:
        verify_webhook(body, headers, SECRET)
    assert info.value.code == "TIMESTAMP_OUT_OF_TOLERANCE"
    assert verify_webhook(body, headers, SECRET, tolerance=600)["eventId"] == "evt_1"

    headers["webhook-timestamp"] = "soon"
    with pytest.raises(WebhookVerificationError) as bad:
        verify_webhook(body, headers, SECRET)
    assert bad.value.code == "INVALID_TIMESTAMP"


def test_missing_headers_no_signatures_and_invalid_json():
    with pytest.raises(WebhookVerificationError) as missing:
        verify_webhook(b"{}", {"webhook-id": "x"}, SECRET)
    assert missing.value.code == "MISSING_HEADERS"

    body, headers = signed(REALTIME_EVENT)
    headers["webhook-signature"] = "v2,abc"
    with pytest.raises(WebhookVerificationError) as none:
        verify_webhook(body, headers, SECRET)
    assert none.value.code == "NO_VALID_SIGNATURES"

    ts = int(time.time())
    raw = b"not json"
    headers = {"webhook-id": "m", "webhook-timestamp": str(ts), "webhook-signature": sign_webhook(raw, "m", ts, SECRET)}
    with pytest.raises(WebhookVerificationError) as invalid:
        verify_webhook(raw, headers, SECRET)
    assert invalid.value.code == "INVALID_JSON"


def test_event_type_tables():
    assert len(WEBHOOK_EVENT_MODELS) == 17
    assert len(LIFECYCLE_EVENT_TYPES) == 6 and len(REALTIME_EVENT_TYPES) == 11
    assert "authorization.revoked" in LIFECYCLE_EVENT_TYPES


def test_parse_typed_events():
    typed = parse_webhook_event(REALTIME_EVENT)
    assert isinstance(typed, models.RealtimeChatMessageLikedEnvelope)
    assert typed.data.id == 123
    revoked = parse_webhook_event(REVOKED_EVENT)
    assert isinstance(revoked, models.LifecycleAuthorizationRevokedEnvelope)
    assert revoked.linkedAccountId is None
    with pytest.raises(pydantic.ValidationError):
        parse_webhook_event({**REVOKED_EVENT, "data": {"id": 1}})
    with pytest.raises(KeyError):
        parse_webhook_event({**REVOKED_EVENT, "type": "unknown.type"})


def test_router_dispatch_default_and_http_helper():
    router = WebhookRouter(SECRET)
    seen: list[str] = []

    @router.on("realtime.chat_message.liked")
    def liked(event):
        seen.append("liked:" + event["eventId"])

    router.on_default(lambda event: seen.append("default:" + event["type"]))

    body, headers = signed(REALTIME_EVENT)
    assert router.handle(body, headers)["eventId"] == "evt_1"
    body2, headers2 = signed(REVOKED_EVENT)
    assert router.handle_http(body2, headers2) == (200, {"ok": True})
    assert seen == ["liked:evt_1", "default:authorization.revoked"]

    status, payload = router.handle_http(body, {**headers, "webhook-signature": "v1,AAAA"})
    assert (status, payload) == (401, {"error": "SIGNATURE_MISMATCH"})


def test_router_typed_and_async_handlers():
    router = WebhookRouter(SECRET, typed=True)
    seen: list[object] = []

    async def handler(event):
        seen.append(event)

    router.on("realtime.chat_message.liked", handler)
    body, headers = signed(REALTIME_EVENT)
    assert asyncio.run(router.handle_http_async(body, headers)) == (200, {"ok": True})
    assert isinstance(seen[0], models.RealtimeChatMessageLikedEnvelope)

    with pytest.raises(Exception, match="handle_async"):
        router.handle(body, headers)
