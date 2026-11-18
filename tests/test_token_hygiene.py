from __future__ import annotations

import asyncio

import httpx
import pytest

from onlyfans_sdk import OFAuthClient, OFAuthConnectionError, OFAuthError
import onlyfans_sdk
from onlyfans_sdk import AsyncOFAuthClient, RealtimeConnection
from onlyfans_sdk._runtime import _realtime_url_for, _redact, _sanitize_url
from tests.conftest import Recorder, json_response
from tests.test_realtime import Server, closed, sse


def make_client(handler, **kwargs) -> tuple[OFAuthClient, Recorder]:
    recorder = Recorder(handler)
    kwargs.setdefault("access_token", "tok_123")
    kwargs.setdefault("base_url", "https://api.test")
    client = OFAuthClient(http_client=recorder.sync_client(), **kwargs)
    return client, recorder


# -- header casing and redaction ------------------------------------------


@pytest.mark.parametrize("name", ["Authorization", "authorization", "AUTHORIZATION"])
def test_client_authorization_header_is_rejected(name: str) -> None:
    with pytest.raises(OFAuthError, match="SDK sends") as info:
        make_client(lambda r: json_response(200, {}), headers={name: "Bearer caller-secret"})
    assert "caller-secret" not in str(info.value)


def test_per_request_authorization_header_is_rejected_before_sending() -> None:
    client, rec = make_client(lambda r: json_response(200, {}))
    with pytest.raises(OFAuthError, match="SDK sends"):
        client.request("GET", "/v3/x", headers={"Authorization": "Bearer other"})
    assert rec.requests == []


def test_headers_merge_case_insensitively_and_sdk_headers_win() -> None:
    client, rec = make_client(
        lambda r: json_response(200, {}),
        linked_account_id="acct_1",
        headers={"X-Linked-Account-Id": "acct_spoofed", "Accept": "text/plain", "X-Trace": "abc"},
    )
    client.access.profile.get()
    sent = rec.last.headers
    assert sent.get_list("authorization") == ["Bearer tok_123"]
    assert sent.get_list("x-linked-account-id") == ["acct_1"]
    assert sent.get_list("accept") == ["text/plain"]
    assert sent["x-trace"] == "abc"


def test_sensitive_headers_are_redacted_in_hooks_whatever_their_casing() -> None:
    seen = []
    client, _ = make_client(
        lambda r: json_response(200, {}),
        access_token="secret-token",
        linked_account_id="acct_1",
        headers={
            "Cookie": "session=c1",
            "X-API-Key": "k1",
            "CF-Access-Client-Secret": "s1",
            "X-Upstream-Token": "t1",
            "X-Trace": "visible",
        },
        on_request=seen.append,
    )
    client.access.profile.get()
    headers = seen[0].headers
    for name in ("authorization", "cookie", "x-api-key", "cf-access-client-secret", "x-upstream-token"):
        assert headers[name] == "[REDACTED]"
    assert headers["x-trace"] == "visible"
    assert not any(v in repr(seen) for v in ("secret-token", "c1", "k1", "s1", "t1"))


def test_redact_matches_names_case_insensitively() -> None:
    assert _redact({"Authorization": "Bearer x", "Set-Cookie": "z", "Accept": "a"}) == {
        "authorization": "[REDACTED]",
        "set-cookie": "[REDACTED]",
        "accept": "a",
    }


# -- realtime is always the API origin -------------------------------------


def test_realtime_url_for() -> None:
    assert _realtime_url_for("https://api.ofauth.com") == "https://api.ofauth.com/v3/realtime/events"
    assert _realtime_url_for("https://api.staging.ofauth.com/") == "https://api.staging.ofauth.com/v3/realtime/events"
    assert _realtime_url_for("HTTP://localhost:8787") == "HTTP://localhost:8787/v3/realtime/events"
    with pytest.raises(OFAuthError):
        _realtime_url_for("ftp://example.com")


def _realtime_url(client: OFAuthClient | AsyncOFAuthClient, **options) -> str:
    server = Server(sse(closed("replaced")))

    async def run() -> None:
        conn = client.realtime(http_client=server.http(), reconnect=False, **options)
        await conn.connect()
        await conn.wait_closed()

    asyncio.run(run())
    return str(server.requests[0].url)


def test_client_realtime_uses_the_api_origin() -> None:
    staging = OFAuthClient("tok", linked_account_id="acct_1", base_url="https://api.staging.ofauth.com")
    assert _realtime_url(staging) == "https://api.staging.ofauth.com/v3/realtime/events?linkedAccountId=acct_1"
    prod = OFAuthClient("tok", linked_account_id="acct_1")
    assert _realtime_url(prod) == "https://api.ofauth.com/v3/realtime/events?linkedAccountId=acct_1"
    loopback = AsyncOFAuthClient("tok", linked_account_id="acct_1", base_url="http://127.0.0.1:8787/")
    assert _realtime_url(loopback) == "http://127.0.0.1:8787/v3/realtime/events?linkedAccountId=acct_1"
    # with_options re-derives from the new base_url.
    moved = prod.with_options(base_url="https://api.staging.ofauth.com")
    assert _realtime_url(moved) == "https://api.staging.ofauth.com/v3/realtime/events?linkedAccountId=acct_1"


def test_realtime_cannot_point_elsewhere() -> None:
    # No client option and no realtime() option sets the Realtime URL.
    with pytest.raises(TypeError):
        OFAuthClient("tok", realtime_url="https://rt.test/v3/realtime/events")  # type: ignore[call-arg]
    client = OFAuthClient("tok", linked_account_id="acct_1", base_url="https://api.staging.ofauth.com")
    with pytest.raises(TypeError):
        client.realtime(url="https://rt.test/v3/realtime/events")  # type: ignore[call-arg]
    with pytest.raises(OFAuthError, match="not an http"):
        OFAuthClient("tok", linked_account_id="acct_1", base_url="ftp://api.test").realtime()


def test_realtime_connection_cannot_be_created_without_a_client() -> None:
    with pytest.raises(TypeError, match="client.realtime"):
        RealtimeConnection(access_token="tok", linked_account_id="acct_1")
    with pytest.raises(TypeError, match="client.realtime"):
        RealtimeConnection()
    assert not hasattr(onlyfans_sdk, "DEFAULT_REALTIME_URL")
    assert not hasattr(onlyfans_sdk._runtime, "DEFAULT_REALTIME_URL")
    assert not hasattr(onlyfans_sdk._runtime, "realtime_url_for")
    # The type stays public for annotations.
    conn: RealtimeConnection = OFAuthClient("tok", linked_account_id="acct_1").realtime()
    assert isinstance(conn, RealtimeConnection)


# -- sanitized URLs ---------------------------------------------------------


def test_sanitize_url() -> None:
    assert (
        _sanitize_url(
            "https://user:pw@api.test/v3/x?X-Amz-Signature=abc&X-Amz-Credential=cred&token=t&sig=s&key=k&limit=10&cursor=c2#frag"
        )
        == "https://api.test/v3/x?X-Amz-Signature=REDACTED&X-Amz-Credential=REDACTED&token=REDACTED&sig=REDACTED&key=REDACTED&limit=10&cursor=c2"
    )
    assert _sanitize_url("https://api.test/v3/access/profile") == "https://api.test/v3/access/profile"


def test_hooks_get_sanitized_urls_but_the_request_keeps_the_signature() -> None:
    requests, responses = [], []
    client, rec = make_client(lambda r: json_response(200, {}), on_request=requests.append, on_response=responses.append)
    signed = "https://api.test/v3/access/uploads/u/parts/1?X-Amz-Signature=deadbeef&partNumber=1"
    client.request("PUT", "/v3/access/uploads/u/parts/1", url=signed, content=b"x")
    assert str(rec.last.url) == signed
    assert requests[0].url == "https://api.test/v3/access/uploads/u/parts/1?X-Amz-Signature=REDACTED&partNumber=1"
    assert responses[0].url == requests[0].url
    assert "deadbeef" not in repr([requests, responses])


def test_connection_errors_do_not_include_signed_query_values() -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    client, _ = make_client(fail, max_retries=0)
    with pytest.raises(OFAuthConnectionError) as info:
        client.request("GET", "/v3/x", url="https://api.test/v3/x?token=deadbeef")
    assert "deadbeef" not in str(info.value)


def test_realtime_hooks_get_sanitized_urls() -> None:
    requests, responses = [], []
    server = Server(sse(closed("replaced")))
    client = OFAuthClient("tok", linked_account_id="acct_1", base_url="https://user:deadbeef@rt.test")

    async def run() -> None:
        conn = client.realtime(
            http_client=server.http(),
            reconnect=False,
            on_request=requests.append,
            on_response=responses.append,
        )
        await conn.connect()
        await conn.wait_closed()

    asyncio.run(run())
    assert server.requests[0].url.password == "deadbeef"
    assert requests[0].url == "https://rt.test/v3/realtime/events?linkedAccountId=acct_1"
    assert responses[0].url == requests[0].url
