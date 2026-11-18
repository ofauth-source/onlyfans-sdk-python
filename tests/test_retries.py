from __future__ import annotations

import asyncio
import datetime
from email.utils import format_datetime

import httpx
import pytest

from onlyfans_sdk import (
    AsyncOFAuthClient,
    OFAuthAPIError,
    OFAuthClient,
    OFAuthConnectionError,
    OFAuthTimeoutError,
    RequestInfo,
    ResponseInfo,
    _runtime,
)
from tests.conftest import Recorder, json_response


def make_client(responses, **kwargs) -> tuple[OFAuthClient, Recorder]:
    """A client answering from a list of responses / exceptions, in order."""
    queue = list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    recorder = Recorder(handler)
    kwargs.setdefault("access_token", "tok_123")
    kwargs.setdefault("linked_account_id", "acct_1")
    client = OFAuthClient(http_client=recorder.sync_client(), base_url="https://api.test", **kwargs)
    return client, recorder


def error(status: int, code: str, headers: dict[str, str] | None = None, action: str | None = None) -> httpx.Response:
    body: dict = {"error": code}
    if action:
        body["recovery"] = {"action": action}
    return json_response(status, body, headers=headers)


def ok() -> httpx.Response:
    return json_response(200, {"ok": True})


def test_get_retries_5xx_with_backoff_then_succeeds(sleeps, monkeypatch):
    monkeypatch.setattr(_runtime.random, "uniform", lambda a, b: b)  # deterministic jitter: the cap
    client, rec = make_client([error(502, "bad_gateway"), error(504, "timeout"), ok()])
    assert client.access.profile.get() == {"ok": True}
    assert len(rec.requests) == 3
    assert sleeps == [0.5, 1.0]


def test_backoff_has_full_jitter_and_8s_cap(monkeypatch):
    calls: list[tuple[float, float]] = []
    monkeypatch.setattr(_runtime.random, "uniform", lambda a, b: calls.append((a, b)) or 0.0)
    for retry in range(6):
        _runtime._backoff(retry)
    assert calls == [(0.0, 0.5), (0.0, 1.0), (0.0, 2.0), (0.0, 4.0), (0.0, 8.0), (0.0, 8.0)]


def test_post_is_not_retried_on_502_and_attempts_is_exposed(sleeps):
    client, rec = make_client([error(502, "transient_provider_failure"), ok()])
    with pytest.raises(OFAuthAPIError) as info:
        client.access.chats.messages.send(user_id=1, body={"text": "hi"})
    assert info.value.attempts == 1
    assert len(rec.requests) == 1
    assert sleeps == []


def test_post_retries_429_and_authorization_temporarily_unavailable(sleeps):
    client, rec = make_client(
        [
            error(429, "rate_limited", {"retry-after": "2"}),
            error(503, "authorization_temporarily_unavailable", {"retry-after": "1"}),
            ok(),
        ]
    )
    assert client.access.chats.messages.send(user_id=1, body={"text": "hi"}) == {"ok": True}
    assert sleeps == [2.0, 1.0]
    assert len(rec.requests) == 3


def test_retry_after_http_date_and_ratelimit_reset(sleeps, monkeypatch):
    now = 1_700_000_000.0
    monkeypatch.setattr(_runtime.time, "time", lambda: now)
    when = format_datetime(datetime.datetime.fromtimestamp(now + 5, tz=datetime.timezone.utc), usegmt=True)
    client, _ = make_client(
        [error(429, "rate_limited", {"retry-after": when}), error(429, "rate_limited", {"ratelimit-reset": "3"}), ok()]
    )
    client.access.profile.get()
    assert sleeps == [5.0, 3.0]


def test_server_delay_above_max_retry_delay_raises(sleeps):
    client, rec = make_client([error(429, "quota_exhausted", {"retry-after": "3600"}), ok()])
    with pytest.raises(OFAuthAPIError) as info:
        client.access.profile.get()
    assert info.value.code == "quota_exhausted"
    assert info.value.retry_after == 3600
    assert len(rec.requests) == 1 and sleeps == []

    client2, rec2 = make_client([error(429, "rate_limited", {"retry-after": "30"}), ok()], max_retry_delay=10)
    with pytest.raises(OFAuthAPIError):
        client2.access.profile.get()
    assert len(rec2.requests) == 1


def test_max_retries_exhausted_and_disabled(sleeps):
    client, rec = make_client([error(503, "unavailable")] * 3)
    with pytest.raises(OFAuthAPIError) as info:
        client.access.profile.get()
    assert info.value.attempts == 3
    assert len(rec.requests) == 3

    client0, rec0 = make_client([error(503, "unavailable"), ok()], max_retries=0)
    with pytest.raises(OFAuthAPIError) as info0:
        client0.access.profile.get()
    assert info0.value.attempts == 1 and len(rec0.requests) == 1


def test_other_4xx_never_retried(sleeps):
    for status, code in [(400, "invalid_request"), (403, "missing_scope"), (404, "not_found"), (409, "conflict")]:
        client, rec = make_client([error(status, code), ok()])
        with pytest.raises(OFAuthAPIError):
            client.access.profile.get()
        assert len(rec.requests) == 1
    assert sleeps == []


def test_network_errors_retry_idempotent_only(sleeps):
    client, rec = make_client([httpx.ConnectError("refused"), httpx.ReadTimeout("slow"), ok()])
    assert client.access.profile.get() == {"ok": True}
    assert len(rec.requests) == 3 and len(sleeps) == 2

    client2, _ = make_client([httpx.ConnectError("refused"), ok()])
    with pytest.raises(OFAuthConnectionError) as info:
        client2.access.chats.messages.send(user_id=1, body={"text": "x"})
    assert info.value.attempts == 1
    assert isinstance(info.value.__cause__, httpx.ConnectError)
    assert info.value.is_retryable

    client3, _ = make_client([httpx.ReadTimeout("slow")] * 3)
    with pytest.raises(OFAuthTimeoutError) as timeout:
        client3.access.profile.get()
    assert timeout.value.attempts == 3
    assert timeout.value.operation == "access.profile.get"


def test_invalid_token_refresh_does_not_count_against_max_retries(sleeps):
    tokens = iter(["stale", "fresh", "fresh"])
    seen: list[bool] = []

    def source(force: bool) -> str:
        seen.append(force)
        return next(tokens)

    client, rec = make_client(
        [error(401, "invalid_token"), error(503, "unavailable"), ok()], access_token=source, max_retries=1
    )
    assert client.access.profile.get() == {"ok": True}
    assert seen == [False, True, False]
    assert len(rec.requests) == 3


def test_timeout_per_attempt_and_with_options():
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.extensions["timeout"])
        return ok()

    rec = Recorder(handler)
    client = OFAuthClient(access_token="t", linked_account_id="a", http_client=rec.sync_client(), timeout=12)
    client.access.profile.get()
    assert seen[-1]["read"] == 12
    fast = client.with_options(timeout=3, max_retries=0)
    fast.access.profile.get()
    assert seen[-1]["read"] == 3
    assert fast.max_retries == 0 and fast.linked_account_id == "a"
    assert client.timeout == 12 and client.max_retries == 2
    with pytest.raises(TypeError):
        client.with_options(nope=1)


def test_upload_part_put_uses_at_least_300s_timeout():
    timeouts: dict[str, float] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        timeouts[request.url.path] = request.extensions["timeout"]["read"]
        if request.url.path.endswith("/start"):
            return json_response(
                200,
                {
                    "status": "needs_upload",
                    "uploadId": "up_1",
                    "parts": [{"uploadUrl": "https://api.test/v3/access/uploads/up_1/parts/1",
                               "byteRange": {"start": 0, "end": 2}}],
                },
            )
        return json_response(200, {"ok": True})

    rec = Recorder(handler)
    client = OFAuthClient(access_token="t", linked_account_id="a", http_client=rec.sync_client(),
                          base_url="https://api.test", timeout=20)
    client.upload_media(b"abc", filename="upload.png", content_type="image/png")
    assert timeouts["/v3/access/uploads/start"] == 20
    assert timeouts["/v3/access/uploads/up_1/parts/1"] == 300


def test_hooks_receive_redacted_info_and_failures_are_ignored(sleeps):
    requests: list[RequestInfo] = []
    responses: list[ResponseInfo] = []

    def on_request(info: RequestInfo) -> None:
        requests.append(info)
        raise RuntimeError("hook bug")

    def on_response(info: ResponseInfo) -> None:
        responses.append(info)
        raise RuntimeError("hook bug")

    client, _ = make_client(
        [error(503, "unavailable", {"x-request-id": "req_1"}), json_response(200, {}, {"x-request-id": "req_2"})],
        on_request=on_request,
        on_response=on_response,
    )
    client.access.chats.list(limit=5)
    assert [r.attempt for r in requests] == [1, 2]
    assert requests[0].headers["authorization"] == "[REDACTED]"
    assert requests[0].headers["x-linked-account-id"] == "acct_1"
    assert requests[0].url == "https://api.test/v3/access/chats?limit=5"
    assert requests[0].method == "GET" and requests[0].operation == "access.chats.list"
    assert [(r.status, r.request_id, r.attempt) for r in responses] == [(503, "req_1", 1), (200, "req_2", 2)]
    assert all(r.duration_ms >= 0 for r in responses)


def test_debug_logger_lines_never_include_tokens(sleeps):
    lines: list[str] = []
    client, _ = make_client(
        [error(503, "unavailable"), json_response(200, {}, {"x-request-id": "req_abc"})],
        debug=lines.append,
        access_token="secret_token_value",
    )
    client.access.profile.get()
    assert lines[0].startswith("[ofauth] GET /v3/access/profile -> 503 (")
    assert lines[1].startswith("[ofauth] retrying GET /v3/access/profile in ")
    assert "(attempt 2 of 3): 503 unavailable" in lines[1]
    assert lines[2].startswith("[ofauth] GET /v3/access/profile -> 200 (") and lines[2].endswith("ms, req_abc)")
    assert not any("secret_token_value" in line for line in lines)


def test_debug_env_var_and_true_log_to_stderr(monkeypatch, capsys):
    monkeypatch.setenv("OFAUTH_DEBUG", "1")
    client, _ = make_client([json_response(200, {})])
    client.access.profile.get()
    assert "[ofauth] GET /v3/access/profile -> 200" in capsys.readouterr().err

    monkeypatch.delenv("OFAUTH_DEBUG")
    quiet, _ = make_client([json_response(200, {})])
    quiet.access.profile.get()
    assert capsys.readouterr().err == ""

    loud, _ = make_client([json_response(200, {})], debug=True)
    loud.access.profile.get()
    assert "[ofauth]" in capsys.readouterr().err


def test_async_retries_hooks_and_cancellation(sleeps):
    async def run() -> None:
        queue = [error(429, "rate_limited", {"retry-after": "1"}), httpx.ConnectError("x"), ok()]

        def handler(request: httpx.Request) -> httpx.Response:
            item = queue.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        seen: list[int] = []

        async def on_request(info: RequestInfo) -> None:
            seen.append(info.attempt)

        rec = Recorder(handler)
        client = AsyncOFAuthClient(access_token="t", linked_account_id="a", http_client=rec.async_client(),
                                   on_request=on_request)
        assert await client.access.profile.get() == {"ok": True}
        assert seen == [1, 2, 3]
        assert sleeps[0] == 1.0

        # Cancelling the caller stops retrying.
        async def slow_sleep(self, seconds: float) -> None:
            await asyncio.sleep(3600)

        rec2 = Recorder(lambda r: error(503, "unavailable"))
        client2 = AsyncOFAuthClient(access_token="t", linked_account_id="a", http_client=rec2.async_client())
        client2._sleep = slow_sleep.__get__(client2)  # type: ignore[method-assign]
        task = asyncio.ensure_future(client2.access.profile.get())
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert len(rec2.requests) == 1

    asyncio.run(run())


class PolicyRefusal(Exception):
    """Raised on purpose by a caller-supplied transport."""


def test_custom_transport_errors_propagate_unchanged_and_are_not_retried(sleeps):
    for exc in (PolicyRefusal("blocked by policy"), httpx.UnsupportedProtocol("ftp"), httpx.ProxyError("proxy")):
        client, rec = make_client([exc, ok(), ok()])
        with pytest.raises(type(exc)) as info:
            client.access.profile.get()  # GET: idempotent, still not retried
        assert info.value is exc
        assert len(rec.requests) == 1
    assert sleeps == []


def test_genuine_network_failures_are_still_retried_and_wrapped(sleeps):
    failures = [httpx.ConnectError("refused"), httpx.ReadError("reset"), httpx.WriteError("broken pipe"),
                httpx.RemoteProtocolError("peer closed"), httpx.PoolTimeout("pool")]
    for failure in failures:
        client, rec = make_client([failure, ok()])
        assert client.access.profile.get() == {"ok": True}
        assert len(rec.requests) == 2
    client, rec = make_client([httpx.ReadError("reset")] * 3)
    with pytest.raises(OFAuthConnectionError) as info:
        client.access.profile.get()
    assert info.value.attempts == 3 and isinstance(info.value.__cause__, httpx.ReadError)


def test_async_custom_transport_error_propagates_unchanged(sleeps):
    async def run() -> None:
        refusal = PolicyRefusal("no")
        calls = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            raise refusal

        rec = Recorder(handler)
        client = AsyncOFAuthClient(access_token="t", linked_account_id="a", http_client=rec.async_client())
        with pytest.raises(PolicyRefusal) as info:
            await client.access.profile.get()
        assert info.value is refusal and len(calls) == 1

        queue = [httpx.ConnectError("refused"), ok()]
        rec2 = Recorder(lambda r: (_ for _ in ()).throw(queue.pop(0)) if isinstance(queue[0], Exception) else queue.pop(0))
        client2 = AsyncOFAuthClient(access_token="t", linked_account_id="a", http_client=rec2.async_client())
        assert await client2.access.profile.get() == {"ok": True}
        assert len(rec2.requests) == 2

    asyncio.run(run())
