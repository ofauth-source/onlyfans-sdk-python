from __future__ import annotations

import asyncio
import json

import pytest

from onlyfans_sdk import WebhookRouter, parse_webhook_event, verify_webhook
from onlyfans_sdk.events import LIFECYCLE_EVENT_TYPES, REALTIME_EVENT_TYPES
from onlyfans_sdk.testing import (
    create_test_event,
    deliver_webhook,
    deliver_webhook_async,
    generate_webhook_secret,
    sign_webhook,
)
from onlyfans_sdk.webhooks import WebhookVerificationError

SECRET = generate_webhook_secret()
ALL_TYPES = sorted(LIFECYCLE_EVENT_TYPES | REALTIME_EVENT_TYPES)


def test_sign_webhook_headers_and_body_verify():
    signed = sign_webhook({"type": "x", "n": 1}, SECRET, id="msg_1", timestamp=1_700_000_000)
    body, headers = signed
    assert body == '{"type":"x","n":1}'
    assert headers["webhook-id"] == "msg_1"
    assert headers["webhook-timestamp"] == "1700000000"
    assert headers["webhook-signature"].startswith("v1,")
    with pytest.raises(WebhookVerificationError) as old:
        verify_webhook(*signed, SECRET)
    assert old.value.code == "TIMESTAMP_OUT_OF_TOLERANCE"
    fresh = sign_webhook('{"a":1}', SECRET)
    assert verify_webhook(*fresh, SECRET) == {"a": 1}
    with pytest.raises(WebhookVerificationError):
        verify_webhook(*fresh, generate_webhook_secret())


@pytest.mark.parametrize("event_type", ALL_TYPES)
def test_create_test_event_is_valid_for_every_type(event_type):
    event = create_test_event(event_type)
    assert event["type"] == event_type
    assert event["eventId"].startswith("evt_test_")
    model = parse_webhook_event(event)
    assert getattr(model.type, "value", model.type) == event_type


def test_create_test_event_deep_merges_and_fresh_ids():
    assert len(ALL_TYPES) == 17
    a = create_test_event("authorization.revoked")
    b = create_test_event("authorization.revoked")
    assert a["eventId"] != b["eventId"]
    merged = create_test_event(
        "authorization.revoked",
        {"eventId": "evt_fixed", "authorizationId": "authz_9", "data": {"reason": "user_revoked"}},
    )
    assert merged["eventId"] == "evt_fixed"
    assert merged["authorizationId"] == "authz_9"
    assert merged["data"]["reason"] == "user_revoked"
    assert merged["data"]["linked_account_ids"] == a["data"]["linked_account_ids"]  # kept
    merged["data"]["linked_account_ids"].append("mutated")
    assert "mutated" not in create_test_event("authorization.revoked")["data"]["linked_account_ids"]
    with pytest.raises(KeyError):
        create_test_event("nope")


def test_router_handle_with_signed_event_and_deliver_helpers():
    router = WebhookRouter(SECRET)
    seen: list[str] = []
    router.on("realtime.chat_message.received", lambda e: seen.append(e["eventId"]))
    event = create_test_event("realtime.chat_message.received", {"linkedAccountId": "acct_1"})
    handled = router.handle(*sign_webhook(event, SECRET))
    assert handled == json.loads(json.dumps(event))
    assert deliver_webhook(router, event)["linkedAccountId"] == "acct_1"
    assert seen == [event["eventId"], event["eventId"]]

    async def run() -> None:
        async def handler(e: dict) -> None:
            seen.append("async")

        router.on("authorization.granted", handler)
        await deliver_webhook_async(router, create_test_event("authorization.granted"))

    asyncio.run(run())
    assert seen[-1] == "async"
    with pytest.raises(WebhookVerificationError):
        deliver_webhook(router, event, secret=generate_webhook_secret())
