from __future__ import annotations

import asyncio
import datetime
import json

import httpx
import pytest

from onlyfans_sdk import (
    AsyncOFAuthClient,
    OFAuthAPIError,
    OFAuthClient,
    OFAuthError,
    models,
)
from tests.conftest import Recorder, json_response


def make_client(handler, **kwargs) -> tuple[OFAuthClient, Recorder]:
    recorder = Recorder(handler)
    kwargs.setdefault("access_token", "tok_123")
    client = OFAuthClient(http_client=recorder.sync_client(), base_url="https://api.test", **kwargs)
    return client, recorder


def test_bearer_and_linked_account_header():
    client, rec = make_client(lambda r: json_response(200, {"id": 1}), linked_account_id="acct_default")
    assert client.access.profile.get() == {"id": 1}
    req = rec.last
    assert req.method == "GET"
    assert str(req.url) == "https://api.test/v3/access/profile"
    assert req.headers["authorization"] == "Bearer tok_123"
    assert req.headers["x-linked-account-id"] == "acct_default"
    assert req.headers["accept"] == "application/json"


def test_linked_account_override_and_with_linked_account():
    client, rec = make_client(lambda r: json_response(200, {}), linked_account_id="acct_default")
    client.access.profile.get(linked_account_id="acct_other")
    assert rec.last.headers["x-linked-account-id"] == "acct_other"
    other = client.with_linked_account("acct_third")
    other.access.profile.get()
    assert rec.last.headers["x-linked-account-id"] == "acct_third"
    assert other.linked_account_id == "acct_third"


def test_missing_linked_account_raises_locally():
    client, rec = make_client(lambda r: json_response(200, {}))
    with pytest.raises(OFAuthError, match="needs a linked account"):
        client.access.chats.list()
    assert rec.requests == []


def test_linked_accounts_ops_do_not_send_linked_account_header():
    client, rec = make_client(lambda r: json_response(200, {"id": "acct_1"}), linked_account_id="acct_default")
    client.linked_accounts.get(id="acct_1")
    assert rec.last.url.path == "/v3/linked-accounts/acct_1"
    assert "x-linked-account-id" not in rec.last.headers


def test_path_query_and_body_serialization():
    client, rec = make_client(lambda r: json_response(200, {"ok": True}), linked_account_id="a")
    client.access.chats.messages.send(user_id="12/3", body={"text": "hi", "price": None})
    req = rec.last
    assert req.method == "POST"
    assert req.url.raw_path == b"/v3/access/chats/12%2F3/messages"
    assert req.headers["content-type"] == "application/json"
    assert json.loads(req.content) == {"text": "hi", "price": None}

    client.access.chats.list(limit=5, cursor=None, order="recent")
    assert dict(rec.last.url.params) == {"limit": "5", "order": "recent"}

    client.access.analytics.timeseries.engagement.messages.get(
        start_date=datetime.date(2024, 1, 1), with_total=True
    )
    assert dict(rec.last.url.params) == {"startDate": "2024-01-01", "withTotal": "true"}
    assert rec.last.content == b""


def test_pydantic_body_is_dumped_by_alias_without_none():
    client, rec = make_client(lambda r: json_response(200, {}), linked_account_id="a")
    body = models.MessageContent(text="hello")
    client.access.chats.messages.send(user_id=1, body=body)
    sent = json.loads(rec.last.content)
    assert sent["text"] == "hello"
    assert None not in sent.values()


def test_no_content_returns_none():
    client, _ = make_client(lambda r: httpx.Response(204), linked_account_id="a")
    assert client.access.chats.delete(user_id=1) is None


def test_invalid_token_retries_once_with_forced_refresh():
    calls: list[bool] = []

    def source(force_refresh: bool) -> str:
        calls.append(force_refresh)
        return "fresh" if force_refresh else "stale"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers["authorization"] == "Bearer stale":
            return json_response(401, {"error": "invalid_token", "recovery": {"action": "refresh_token"}})
        return json_response(200, {"ok": True})

    client, rec = make_client(handler, access_token=source, linked_account_id="a")
    assert client.access.profile.get() == {"ok": True}
    assert calls == [False, True]
    assert len(rec.requests) == 2


def test_invalid_token_with_provider_object():
    class Provider:
        def __init__(self) -> None:
            self.forced = 0

        def get_access_token(self, force_refresh: bool = False) -> str:
            self.forced += force_refresh
            return "new" if force_refresh else "old"

    provider = Provider()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers["authorization"] == "Bearer old":
            return json_response(401, {"error": "invalid_token"})
        return json_response(200, {})

    client, _ = make_client(handler, access_token=provider, linked_account_id="a")
    client.access.profile.get()
    assert provider.forced == 1


def test_static_token_is_not_retried():
    client, rec = make_client(lambda r: json_response(401, {"error": "invalid_token"}), linked_account_id="a")
    with pytest.raises(OFAuthAPIError) as info:
        client.access.profile.get()
    assert info.value.status == 401
    assert len(rec.requests) == 1


def test_other_401_is_not_retried():
    calls: list[bool] = []
    client, rec = make_client(
        lambda r: json_response(401, {"error": "authentication_required"}),
        access_token=lambda force: calls.append(force) or "t",
        linked_account_id="a",
    )
    with pytest.raises(OFAuthAPIError):
        client.access.profile.get()
    assert calls == [False]


def test_error_parsing():
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            429,
            {"error": "rate_limited", "recovery": {"action": "retry_later"}, "message": "Slow down"},
            headers={"retry-after": "7", "x-request-id": "req_hdr"},
        )

    client, _ = make_client(handler, linked_account_id="a")
    with pytest.raises(OFAuthAPIError) as info:
        client.access.profile.get()
    error = info.value
    assert error.status == 429
    assert error.code == "rate_limited"
    assert error.recovery_action == "retry_later"
    assert error.request_id == "req_hdr"
    assert error.retry_after == 7
    assert error.message == "Slow down"
    assert error.body["error"] == "rate_limited"
    assert "rate_limited: Slow down" in str(error)


def test_error_request_id_from_body_and_non_json():
    client, _ = make_client(
        lambda r: json_response(409, {"error": "linked_account_reconnect_required", "requestId": "req_body",
                                      "recovery": {"action": "reconnect_linked_account"}},
                                headers={"x-request-id": "req_hdr"}),
        linked_account_id="a",
    )
    with pytest.raises(OFAuthAPIError) as info:
        client.access.profile.get()
    assert info.value.request_id == "req_body"
    assert info.value.recovery_action == "reconnect_linked_account"

    client2, _ = make_client(lambda r: httpx.Response(502, text="Bad gateway"), linked_account_id="a")
    with pytest.raises(OFAuthAPIError) as info2:
        client2.access.profile.get()
    assert info2.value.code == "http_502"
    assert info2.value.body == "Bad gateway"


def test_pagination_page_style():
    pages = {
        None: {"items": [1, 2], "page": {"nextCursor": "c2", "hasMore": True}},
        "c2": {"items": [3], "page": {"nextCursor": "c3", "hasMore": False}},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(200, pages[request.url.params.get("cursor")])

    client, rec = make_client(handler, linked_account_id="a")
    assert list(client.access.chats.iterate(limit=2)) == [1, 2, 3]
    assert [r.url.params.get("cursor") for r in rec.requests] == [None, "c2"]
    assert all(r.url.params["limit"] == "2" for r in rec.requests)


def test_pagination_stops_on_empty_page_and_max_items():
    def handler(request: httpx.Request) -> httpx.Response:
        cursor = request.url.params.get("cursor")
        if cursor is None:
            return json_response(200, {"items": [1, 2, 3], "page": {"nextCursor": "x", "hasMore": True}})
        return json_response(200, {"items": [], "page": {"nextCursor": "y", "hasMore": True}})

    client, rec = make_client(handler, linked_account_id="a")
    assert list(client.access.chats.iterate(max_items=2)) == [1, 2]
    assert len(rec.requests) == 1
    rec.requests.clear()
    assert list(client.access.chats.iterate()) == [1, 2, 3]
    assert len(rec.requests) == 2


def test_pagination_data_style_linked_accounts():
    pages = {
        None: {"data": [{"id": "a"}], "has_more": True, "next_cursor": "n1"},
        "n1": {"data": [{"id": "b"}], "has_more": False, "next_cursor": None},
    }
    client, rec = make_client(lambda r: json_response(200, pages[r.url.params.get("cursor")]))
    assert [a["id"] for a in client.linked_accounts.iterate(limit=1)] == ["a", "b"]
    assert all("x-linked-account-id" not in r.headers for r in rec.requests)


def test_pagination_flat_style_vault_plus():
    pages = {
        None: {"items": [1], "nextCursor": "n1"},
        "n1": {"items": [2], "nextCursor": None},
    }
    client, _ = make_client(lambda r: json_response(200, pages[r.url.params.get("cursor")]), linked_account_id="a")
    assert list(client.vault_plus.media.iterate()) == [1, 2]


def test_async_client_request_retry_and_pagination():
    pages = {
        None: {"items": [1], "page": {"nextCursor": "c2", "hasMore": True}},
        "c2": {"items": [2], "page": {"nextCursor": None, "hasMore": False}},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers["authorization"] == "Bearer stale":
            return json_response(401, {"error": "invalid_token"})
        return json_response(200, pages[request.url.params.get("cursor")])

    async def source(force_refresh: bool) -> str:
        return "fresh" if force_refresh else "stale"

    async def run() -> None:
        rec = Recorder(handler)
        async with AsyncOFAuthClient(
            access_token=source, linked_account_id="a", http_client=rec.async_client(), base_url="https://api.test"
        ) as client:
            page = await client.access.chats.list()
            assert page["items"] == [1]
            items = [item async for item in client.access.chats.iterate()]
            assert items == [1, 2]
        assert rec.requests[1].headers["x-linked-account-id"] == "a"
        assert rec.requests[1].headers["authorization"] == "Bearer fresh"

        no_account = AsyncOFAuthClient(access_token="t", http_client=rec.async_client())
        with pytest.raises(OFAuthError, match="needs a linked account"):
            await no_account.access.chats.list()

    asyncio.run(run())


def test_realtime_factory_uses_client_token_and_account():
    client, _ = make_client(lambda r: json_response(200, {}), linked_account_id="acct_1")
    conn = client.realtime()
    assert conn.linked_account_id == "acct_1"
    assert conn._stream_url() == "https://api.test/v3/realtime/events?linkedAccountId=acct_1"
    with pytest.raises(OFAuthError):
        make_client(lambda r: json_response(200, {}))[0].realtime()
