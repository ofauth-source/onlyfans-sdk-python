"""Realtime over Server-Sent Events, against a fake streaming response."""

from __future__ import annotations

import asyncio
import dataclasses
import json
from collections.abc import AsyncIterator, Callable
from typing import Any

import httpx
import pytest

from onlyfans_sdk import (
    AsyncOFAuthClient,
    OFAuthAPIError,
    OFAuthClient,
    OFAuthConnectionError,
    OFAuthError,
    RealtimeCloseInfo,
    RealtimeStreamUrl,
)
from onlyfans_sdk.realtime import RealtimeConnection, SseMessage, SseParser
from tests.conftest import Recorder, json_response

EVENT = {
    "eventId": "evt_1",
    "type": "realtime.chat_message.received",
    "schemaVersion": "1",
    "order": 1,
    "receivedAt": "2026-04-23T14:30:15.143Z",
    "environment": "live",
    "integrationId": "int_1",
    "linkedAccountId": "acct_1",
    "test": False,
    "data": {"id": 5},
}


def event(event_id: str, order: int, type_: str = "realtime.chat_message.received") -> str:
    """One SSE frame for a Realtime event."""
    body = {**EVENT, "eventId": event_id, "order": order, "type": type_}
    return f"id: {order}\nevent: {type_}\ndata: {json.dumps(body)}\n\n"


def closed(reason: str) -> str:
    return f'event: closed\ndata: {{"reason":"{reason}"}}\n\n'


class Script(httpx.AsyncByteStream):
    """A response body: str/bytes chunks, float pauses (seconds), exceptions; then ends or hangs."""

    def __init__(self, items: tuple[Any, ...], hang: bool) -> None:
        self.items = items
        self.hang = hang
        self.closed = False

    async def __aiter__(self) -> AsyncIterator[bytes]:
        for item in self.items:
            if isinstance(item, (int, float)):
                await asyncio.sleep(item)
            elif isinstance(item, BaseException):
                raise item
            else:
                yield item.encode() if isinstance(item, str) else item
        if self.hang:
            await asyncio.Event().wait()

    async def aclose(self) -> None:
        self.closed = True


def sse(*items: Any, hang: bool = False, headers: dict[str, str] | None = None) -> httpx.Response:
    return httpx.Response(
        200,
        headers={"content-type": "text/event-stream", "x-realtime-session-id": "rts_1", **(headers or {})},
        stream=Script(items, hang),
    )


class Server:
    """Answers each stream request with the next scripted response (a Response, an exception,
    or a callable); once the script runs out, every request gets a stream that stays open."""

    def __init__(self, *responses: Any) -> None:
        self.responses = list(responses)
        self.requests: list[httpx.Request] = []

    async def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        item = self.responses.pop(0) if self.responses else sse(hang=True)
        if callable(item) and not isinstance(item, httpx.Response):
            item = item(request)
            if asyncio.iscoroutine(item):
                item = await item
        if isinstance(item, BaseException):
            raise item
        return item

    def http(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(self))


def make(server: Server, token: Any = "tok", **options: Any) -> RealtimeConnection:
    client = AsyncOFAuthClient(token, linked_account_id="acct_1", base_url="https://api.test", http_client=server.http())
    options.setdefault("max_reconnect_delay", 0.001)
    return client.realtime(**options)


class Record:
    """Collects what a connection reports."""

    def __init__(self, conn: RealtimeConnection) -> None:
        self.events: list[dict] = []
        self.closes: list[RealtimeCloseInfo] = []
        self.errors: list[BaseException] = []
        self.opens = 0
        self.resyncs = 0
        conn.on_event(self.events.append)
        conn.on_close(self.closes.append)
        conn.on_error(self.errors.append)
        conn.on_open(lambda: self._open())
        conn.on_resync(lambda: self._resync())

    def _open(self) -> None:
        self.opens += 1

    def _resync(self) -> None:
        self.resyncs += 1

    @property
    def reasons(self) -> list[tuple[str, bool]]:
        return [(c.reason, c.will_reconnect) for c in self.closes]


async def until(condition: Callable[[], bool], timeout: float = 2.0) -> None:
    async def wait() -> None:
        while not condition():
            await asyncio.sleep(0.001)

    await asyncio.wait_for(wait(), timeout)


def run(coro: Any) -> Any:
    return asyncio.run(coro)


# ============================================================================
# Parser
# ============================================================================


def messages(parser: SseParser, *chunks: str) -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    for chunk in chunks:
        out.extend(parser.push(chunk))
    return out


def test_parser_handles_chunks_split_anywhere():
    text = "﻿id: 7\r\nevent: realtime.x\r\ndata: {\"a\":\r\ndata: 1}\r\n\r\n: heartbeat\r\nretry: 2500\r\n"
    expected = [
        ("message", SseMessage("realtime.x", '{"a":\n1}', "7")),
        ("comment", "heartbeat"),
        ("retry", 2500),
    ]
    # Whole, one character at a time (splits every \r\n), and in uneven pieces.
    assert messages(SseParser(), text) == expected
    assert messages(SseParser(), *text) == expected
    assert messages(SseParser(), text[:5], text[5:17], text[17:18], text[18:40], text[40:]) == expected


def test_parser_line_endings_fields_and_id_persistence():
    parser = SseParser("3")
    out = messages(
        parser,
        "data:no space\rdata:  two spaces\r\r",  # bare CR line endings; only one space is stripped
        "event: a\nid\ndata\n\n",  # `id` with no value resets it; `data` with no colon is an empty line
        "id: 9\nunknown: x\nretry: 10s\nretry: -1\ndata: b\n\n",  # unknown field and invalid retry ignored
        "id: bad\0id\ndata: c\n\n",  # an id with NUL is ignored
        "event: lonely\n\n",  # no data: nothing dispatched, the type resets
        "data: d\n\n",
        "data: never dispatched\n",
    )
    assert out == [
        ("message", SseMessage("message", "no space\n two spaces", "3")),
        ("message", SseMessage("a", "", "")),
        ("message", SseMessage("message", "b", "9")),
        ("message", SseMessage("message", "c", "9")),
        ("message", SseMessage("message", "d", "9")),
    ]
    parser.end()
    assert parser.push("\n") == []
    assert parser.last_event_id == "9"


def test_parser_comment_without_space_and_bom_only_at_start():
    parser = SseParser()
    assert parser.push(":ping\n") == [("comment", "ping")]
    assert parser.push("﻿data: x\n\n") == []  # a BOM later on is part of the field name
    assert parser.push("data: y\n\n") == [("message", SseMessage("message", "y", ""))]


# ============================================================================
# Streaming, typed events, hooks
# ============================================================================


def test_stream_request_typed_events_and_hooks():
    async def main() -> None:
        server = Server(sse("retry: 3000\n\n", event("evt_1", 1), ": heartbeat\n\n", event("evt_2", 2, "realtime.post.published"), hang=True))
        requests, responses, logs = [], [], []
        client = AsyncOFAuthClient(
            "tok_secret",
            linked_account_id="acct_1",
            base_url="https://api.test",
            headers={"CF-Access-Client-Id": "cf_id"},
            http_client=server.http(),
            on_request=requests.append,
            on_response=responses.append,
            debug=logs.append,
        )
        conn = client.realtime()
        record = Record(conn)
        typed: list[dict] = []

        @conn.on("realtime.chat_message.received")
        async def on_message(e: Any) -> None:
            typed.append(e)

        await conn.connect()
        await conn.connect()  # no-op while connected
        await until(lambda: len(record.events) == 2)
        assert conn.connected
        assert [e["eventId"] for e in typed] == ["evt_1"]
        assert [e["type"] for e in record.events] == ["realtime.chat_message.received", "realtime.post.published"]
        assert conn.last_event_id == "2"
        assert record.opens == 1

        request = server.requests[0]
        assert len(server.requests) == 1
        assert str(request.url) == "https://api.test/v3/realtime/events?linkedAccountId=acct_1"
        assert request.method == "GET"
        assert request.headers["authorization"] == "Bearer tok_secret"
        assert request.headers["accept"] == "text/event-stream"
        assert request.headers["cache-control"] == "no-cache"
        assert request.headers["cf-access-client-id"] == "cf_id"
        assert "last-event-id" not in request.headers

        assert requests[0].method == "GET"
        assert requests[0].url == "https://api.test/v3/realtime/events?linkedAccountId=acct_1"
        assert requests[0].headers["authorization"] == "[REDACTED]"
        assert requests[0].attempt == 1
        assert (responses[0].status, responses[0].request_id, responses[0].attempt) == (200, "rts_1", 1)
        assert logs[0].startswith("[ofauth] SSE /v3/realtime/events -> 200 (") and logs[0].endswith("ms, rts_1)")
        assert "tok_secret" not in repr([requests, responses, logs])

        await conn.close()
        assert record.reasons == [("client_closed", False)]
        assert not conn.connected
        await conn.wait_closed()

    run(main())


def test_hooks_and_debug_can_be_turned_off_per_connection():
    async def main() -> None:
        server = Server(sse(closed("replaced")))
        requests, logs = [], []
        client = AsyncOFAuthClient(
            "tok", linked_account_id="acct_1", base_url="https://api.test", http_client=server.http(),
            on_request=requests.append, debug=logs.append,
        )
        conn = client.realtime(on_request=None, debug=False)
        await conn.connect()
        await conn.wait_closed()
        assert requests == [] and logs == []

    run(main())


def test_bad_events_report_errors_and_listener_errors_do_not_stop_the_stream():
    async def main() -> None:
        server = Server(sse("id: 1\ndata: not json\n\n", 'id: 2\ndata: {"no":"type"}\n\n', event("evt_3", 3), hang=True))
        conn = make(server)
        record = Record(conn)

        def broken(_: Any) -> None:
            raise RuntimeError("listener bug")

        conn.on("realtime.chat_message.received", broken)
        await conn.connect()
        await until(lambda: len(record.events) == 1)
        assert isinstance(record.errors[0], ValueError)
        assert isinstance(record.errors[1], OFAuthError)
        assert isinstance(record.errors[2], RuntimeError)
        assert conn.last_event_id == "3"
        await conn.close()

    run(main())


def test_resync_and_dedupe():
    async def main() -> None:
        server = Server(
            sse(
                event("evt_1", 1),
                "event: resync\ndata: {}\n\n",
                event("evt_2", 2),
                event("evt_1", 3),  # a repeat: dropped, and the resume point stays at 2
                hang=True,
            )
        )
        conn = make(server)
        record = Record(conn)
        await conn.connect()
        await until(lambda: record.resyncs == 1 and len(record.events) == 2)
        await asyncio.sleep(0.01)
        assert [e["eventId"] for e in record.events] == ["evt_1", "evt_2"]
        assert conn.last_event_id == "2"
        await conn.close()

    run(main())


def test_dropped_stream_resumes_with_last_event_id_and_retry():
    async def main() -> None:
        server = Server(
            sse("retry: 5\n\n", event("evt_1", 7)),  # ends without `closed`: dropped
            sse(event("evt_1", 7), event("evt_2", 8), hang=True),  # the replay repeats evt_1
        )
        conn = make(server, last_event_id="6", max_reconnect_delay=30)
        record = Record(conn)
        await conn.connect()
        await until(lambda: len(record.events) == 2)
        assert server.requests[0].headers["last-event-id"] == "6"
        assert server.requests[1].headers["last-event-id"] == "7"
        assert [e["eventId"] for e in record.events] == ["evt_1", "evt_2"]
        assert record.reasons == [("dropped", True)]
        # The backoff starts from the stream's `retry: 5` (ms), with up to 50% jitter.
        assert 0.005 <= record.closes[0].retry_in <= 0.0075
        assert record.opens == 2
        await conn.close()

    run(main())


def test_read_error_is_a_drop():
    async def main() -> None:
        server = Server(sse(event("evt_1", 1), httpx.ReadError("reset")))
        conn = make(server)
        record = Record(conn)
        await conn.connect()
        await until(lambda: len(server.requests) == 2)
        assert record.reasons == [("dropped", True)]
        assert isinstance(record.errors[0], httpx.ReadError)
        await conn.close()

    run(main())


# ============================================================================
# Close reasons and statuses
# ============================================================================


def test_closed_reauth_refreshes_the_token_once_then_stops():
    async def main() -> None:
        calls: list[bool] = []

        def tokens(force_refresh: bool) -> str:
            calls.append(force_refresh)
            return f"tok_{len(calls)}"

        server = Server(sse(closed("reauth")), sse(closed("reauth")))
        conn = make(server, token=tokens)
        record = Record(conn)
        await conn.connect()
        await conn.wait_closed()
        assert calls == [False, True]
        assert [r.headers["authorization"] for r in server.requests] == ["Bearer tok_1", "Bearer tok_2"]
        assert record.reasons == [("reauth", True), ("reauth", False)]
        assert record.closes[0].retry_in == 0

    run(main())


def test_a_healthy_stream_earns_another_refresh():
    async def main() -> None:
        calls: list[bool] = []

        def tokens(force_refresh: bool) -> str:
            calls.append(force_refresh)
            return "tok"

        server = Server(sse(closed("reauth")), sse(event("evt_1", 1), closed("reauth")), sse(hang=True))
        conn = make(server, token=tokens)
        record = Record(conn)
        await conn.connect()
        await until(lambda: len(server.requests) == 3)
        assert calls == [False, True, True]
        assert record.reasons == [("reauth", True), ("reauth", True)]
        await conn.close()

    run(main())


def test_401_with_a_string_token_stops_at_once():
    async def main() -> None:
        server = Server(json_response(401, {"error": "invalid_token"}))
        conn = make(server)
        record = Record(conn)
        with pytest.raises(OFAuthAPIError) as info:
            await conn.connect()
        assert info.value.status == 401
        assert info.value.operation == "realtime"
        assert record.reasons == [("reauth", False)]
        assert record.closes[0].status == 401
        assert len(server.requests) == 1

    run(main())


def test_401_on_first_connect_refreshes_and_retries_once():
    async def main() -> None:
        calls: list[bool] = []

        async def tokens(force_refresh: bool) -> str:
            calls.append(force_refresh)
            return "fresh" if force_refresh else "stale"

        server = Server(json_response(401, {"error": "invalid_token"}), sse(hang=True))
        conn = make(server, token=tokens)
        record = Record(conn)
        await conn.connect()
        assert calls == [False, True]
        assert server.requests[1].headers["authorization"] == "Bearer fresh"
        assert record.reasons == [("reauth", True)]
        assert record.opens == 1
        await conn.close()

        # Two 401s in a row: the refresh is used up and connect() raises.
        server = Server(json_response(401, {}), json_response(401, {}))
        conn = make(server, token=tokens)
        with pytest.raises(OFAuthAPIError):
            await conn.connect()
        assert len(server.requests) == 2

    run(main())


def test_replaced_stops():
    async def main() -> None:
        server = Server(sse(event("evt_1", 1), closed("replaced"), event("evt_2", 2)))
        conn = make(server)
        record = Record(conn)
        await conn.connect()
        await conn.wait_closed()
        assert [e["eventId"] for e in record.events] == ["evt_1"]  # nothing after `closed`
        assert record.reasons == [("replaced", False)]
        assert len(server.requests) == 1

        server = Server(json_response(409, {"error": "stream_replaced"}))
        conn = make(server)
        record = Record(conn)
        with pytest.raises(OFAuthAPIError) as info:
            await conn.connect()
        assert info.value.status == 409
        assert record.reasons == [("replaced", False)]

    run(main())


def test_unavailable_backs_off_and_resumes():
    async def main() -> None:
        server = Server(
            sse(event("evt_1", 1), closed("unavailable")),
            json_response(503, {"error": "realtime_unavailable"}, {"retry-after": "0.05"}),
            json_response(429, {"error": "rate_limited"}),
            sse(event("evt_2", 2), hang=True),
        )
        conn = make(server)
        record = Record(conn)
        await conn.connect()
        await until(lambda: len(record.events) == 2)
        assert record.reasons == [("unavailable", True)] * 3
        assert [c.status for c in record.closes] == [None, 503, 429]
        assert record.closes[1].retry_in == 0.05  # at least Retry-After
        assert server.requests[3].headers["last-event-id"] == "1"
        assert [e.status for e in record.errors] == [503, 429]  # type: ignore[attr-defined]
        await conn.close()

    run(main())


def test_unknown_close_reason_counts_as_unavailable():
    async def main() -> None:
        server = Server(sse('event: closed\ndata: {"reason":"maintenance"}\n\n'))
        conn = make(server, reconnect=False)
        record = Record(conn)
        await conn.connect()
        await conn.wait_closed()
        assert record.reasons == [("unavailable", False)]

    run(main())


def test_first_connect_503_raises_with_retry_after():
    async def main() -> None:
        server = Server(json_response(503, {"error": "realtime_unavailable"}, {"retry-after": "7"}))
        conn = make(server)
        record = Record(conn)
        with pytest.raises(OFAuthAPIError) as info:
            await conn.connect()
        assert (info.value.status, info.value.code, info.value.retry_after) == (503, "realtime_unavailable", 7.0)
        assert record.reasons == [("unavailable", False)]
        assert len(server.requests) == 1

    run(main())


@pytest.mark.parametrize(
    "response",
    [
        json_response(403, {"error": "access_token_in_browser"}),
        json_response(404, {"error": "not_found"}),
        json_response(200, {"not": "a stream"}),
    ],
)
def test_refusals_and_non_streams_are_rejected(response: httpx.Response):
    async def main() -> None:
        server = Server(response)
        conn = make(server)
        record = Record(conn)
        with pytest.raises(OFAuthAPIError) as info:
            await conn.connect()
        assert info.value.status == response.status_code
        assert record.reasons == [("rejected", False)]

    run(main())


def test_rejected_after_connecting_stops():
    async def main() -> None:
        server = Server(sse(event("evt_1", 1)), json_response(403, {"error": "forbidden"}))
        conn = make(server)
        record = Record(conn)
        await conn.connect()
        await conn.wait_closed()
        assert record.reasons == [("dropped", True), ("rejected", False)]
        assert record.closes[1].status == 403

    run(main())


def test_network_errors():
    async def main() -> None:
        server = Server(httpx.ConnectError("refused"))
        conn = make(server)
        with pytest.raises(OFAuthConnectionError):
            await conn.connect()

        # After the stream was open, a network failure reconnects.
        server = Server(sse(event("evt_1", 1)), httpx.ConnectError("refused"), sse(hang=True))
        conn = make(server)
        record = Record(conn)
        await conn.connect()
        await until(lambda: len(server.requests) == 3 and record.opens == 2)
        assert record.reasons == [("dropped", True), ("dropped", True)]
        await conn.close()

        # A transport that raises something else on purpose is final.
        server = Server(RuntimeError("blocked by policy"))
        conn = make(server)
        record = Record(conn)
        with pytest.raises(RuntimeError):
            await conn.connect()
        assert record.reasons == [("rejected", False)]

    run(main())


def test_reconnect_false_stops_after_a_drop():
    async def main() -> None:
        server = Server(sse(event("evt_1", 1)))
        conn = make(server, reconnect=False)
        record = Record(conn)
        await conn.connect()
        await conn.wait_closed()
        assert record.reasons == [("dropped", False)]

    run(main())


# ============================================================================
# Heartbeat timeout
# ============================================================================


def test_heartbeat_timeout_reconnects():
    async def main() -> None:
        server = Server(sse(event("evt_1", 1), hang=True), sse(event("evt_2", 2), hang=True))
        conn = make(server, heartbeat_timeout=0.05)
        record = Record(conn)
        await conn.connect()
        await until(lambda: len(record.events) == 2)
        assert record.reasons == [("heartbeat_timeout", True)]
        assert isinstance(record.errors[0], OFAuthConnectionError)
        assert server.requests[1].headers["last-event-id"] == "1"
        await conn.close()

    run(main())


def test_heartbeats_keep_the_stream_alive():
    async def main() -> None:
        beats = [x for _ in range(6) for x in (0.02, ": heartbeat\n\n")]
        server = Server(sse(*beats, hang=True))
        conn = make(server, heartbeat_timeout=0.05)
        record = Record(conn)
        await conn.connect()
        await asyncio.sleep(0.15)
        assert record.closes == []
        await conn.close()

    run(main())


def test_heartbeat_timeout_bounds_the_wait_for_headers():
    async def main() -> None:
        async def slow(_: httpx.Request) -> httpx.Response:
            await asyncio.sleep(10)
            return sse()

        server = Server(slow)
        conn = make(server, heartbeat_timeout=0.05)
        record = Record(conn)
        with pytest.raises(OFAuthConnectionError, match="no response"):
            await conn.connect()
        assert record.reasons == [("heartbeat_timeout", False)]

    run(main())


# ============================================================================
# Lifecycle
# ============================================================================


def test_close_while_backing_off_and_from_a_listener():
    async def main() -> None:
        server = Server(sse(closed("unavailable")))
        conn = make(server, max_reconnect_delay=60)
        record = Record(conn)
        await conn.connect()
        await until(lambda: len(record.closes) == 1)
        await conn.close()
        await asyncio.wait_for(conn.wait_closed(), 1)
        assert record.reasons == [("unavailable", True), ("client_closed", False)]
        assert len(server.requests) == 1

        server = Server(sse(event("evt_1", 1), event("evt_2", 2), hang=True))
        conn = make(server)
        record = Record(conn)

        async def stop(_: Any) -> None:
            await conn.close()

        conn.on("realtime.chat_message.received", stop)
        await conn.connect()
        await asyncio.wait_for(conn.wait_closed(), 1)
        assert [e["eventId"] for e in record.events] == ["evt_1"]
        assert record.reasons == [("client_closed", False)]

    run(main())


def test_connect_again_after_close_and_context_manager():
    async def main() -> None:
        server = Server(sse(hang=True), sse(hang=True))
        conn = make(server)
        await conn.connect()
        await conn.close()
        await conn.connect()
        assert len(server.requests) == 2
        await conn.close()

        server = Server(sse(event("evt_1", 1), hang=True))
        conn = make(server)
        record = Record(conn)
        async with conn:
            await until(lambda: len(record.events) == 1)
        assert record.reasons == [("client_closed", False)]

    run(main())


def test_close_before_open_fails_connect():
    async def main() -> None:
        async def slow(_: httpx.Request) -> httpx.Response:
            await asyncio.sleep(10)
            return sse()

        conn = make(Server(slow))
        task = asyncio.ensure_future(conn.connect())
        await asyncio.sleep(0.01)
        await conn.close()
        with pytest.raises(OFAuthError, match="before it opened"):
            await task

    run(main())


def test_sync_client_streams_with_its_own_or_a_given_async_client():
    async def main() -> None:
        server = Server(sse(closed("replaced")))
        client = OFAuthClient("tok", linked_account_id="acct_1", base_url="https://api.test")
        conn = client.realtime(http_client=server.http(), linked_account_id="acct_2")
        await conn.connect()
        await conn.wait_closed()
        assert str(server.requests[0].url) == "https://api.test/v3/realtime/events?linkedAccountId=acct_2"

    run(main())
    conn = OFAuthClient("tok", linked_account_id="acct_1").realtime()
    assert conn._http is None  # opens (and closes) its own httpx.AsyncClient
    with pytest.raises(OFAuthError, match="linked_account_id"):
        OFAuthClient("tok").realtime()


def test_no_websocket_names():
    import onlyfans_sdk.realtime as realtime

    assert [f.name for f in dataclasses.fields(RealtimeCloseInfo)] == ["reason", "will_reconnect", "status", "retry_in"]
    for name in ("CLOSE_CODES", "REALTIME_AUTHORITY_LOST", "REALTIME_STREAM_REPLACED", "REALTIME_SERVER_CLOSE", "RealtimeError"):
        assert not hasattr(realtime, name)


# ============================================================================
# create_stream_url
# ============================================================================

STREAM_URL = {"url": "https://api.test/v3/realtime/events?linkedAccountId=acct_1&streamToken=st_1", "expiresAt": "2026-04-23T14:40:15.143Z"}


def test_create_stream_url_sync(sleeps: list[float]):
    answers = [json_response(429, {"error": "rate_limited"}, {"retry-after": "1"}), json_response(201, STREAM_URL)]
    rec = Recorder(lambda r: answers.pop(0))
    client = OFAuthClient("tok", linked_account_id="acct_1", base_url="https://api.test", http_client=rec.sync_client())
    result = client.realtime.create_stream_url()
    assert isinstance(result, RealtimeStreamUrl)
    assert result.url == STREAM_URL["url"]
    assert result.expires_at.isoformat() == "2026-04-23T14:40:15.143000+00:00"
    assert sleeps == [1.0]
    request = rec.last
    assert (request.method, str(request.url)) == ("POST", "https://api.test/v3/realtime")
    assert json.loads(request.content) == {"linkedAccountId": "acct_1"}
    assert request.headers["authorization"] == "Bearer tok"

    rec = Recorder(lambda r: json_response(200, STREAM_URL))
    client = OFAuthClient("tok", base_url="https://api.test", http_client=rec.sync_client())
    client.realtime.create_stream_url(linked_account_id="acct_9")
    assert json.loads(rec.last.content) == {"linkedAccountId": "acct_9"}
    with pytest.raises(OFAuthError, match="linked_account_id"):
        client.realtime.create_stream_url()


def test_create_stream_url_async_and_errors():
    async def main() -> None:
        rec = Recorder(lambda r: json_response(200, STREAM_URL))
        client = AsyncOFAuthClient("tok", linked_account_id="acct_1", base_url="https://api.test", http_client=rec.async_client())
        result = await client.realtime.create_stream_url()
        assert result.url == STREAM_URL["url"]
        assert json.loads(rec.last.content) == {"linkedAccountId": "acct_1"}

        rec = Recorder(lambda r: json_response(403, {"error": "realtime_not_enabled"}))
        client = AsyncOFAuthClient("tok", linked_account_id="acct_1", base_url="https://api.test", http_client=rec.async_client())
        with pytest.raises(OFAuthAPIError) as info:
            await client.realtime.create_stream_url()
        assert (info.value.status, info.value.operation) == (403, "realtime.createStreamUrl")

        rec = Recorder(lambda r: json_response(200, {"url": 1}))
        client = AsyncOFAuthClient("tok", linked_account_id="acct_1", base_url="https://api.test", http_client=rec.async_client())
        with pytest.raises(OFAuthError, match="no url"):
            await client.realtime.create_stream_url()

    run(main())

@pytest.mark.asyncio
async def test_initial_cursor_survives_disconnect_over_http() -> None:
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from threading import Thread

    cursors: list[str | None] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            cursors.append(self.headers.get("last-event-id"))
            if len(cursors) == 1:
                body = "retry: 1\n\nid: 10\n\n"
            elif len(cursors) == 2:
                event = {**EVENT, "eventId": "evt_11", "order": 11}
                body = f"id: 11\ndata: {json.dumps(event)}\n\nid: 9\ndata: {json.dumps(event)}\n\nevent: closed\ndata: {{\"reason\":\"unavailable\"}}\n\n"
            else:
                body = 'event: closed\ndata: {"reason":"replaced"}\n\n'
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, *_args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    async with AsyncOFAuthClient(access_token="tok", linked_account_id="conn_1", base_url=f"http://127.0.0.1:{server.server_port}") as client:
        realtime = client.realtime(max_reconnect_delay=0.005)
        events: list[Any] = []
        realtime.on_event(events.append)
        try:
            await realtime.connect()
            await asyncio.wait_for(realtime.wait_closed(), 2)
            assert cursors == [None, "10", "11"]
            assert realtime.last_event_id == "11"
            assert len(events) == 1
        finally:
            await realtime.close()
            server.shutdown()
            server.server_close()
            thread.join()
