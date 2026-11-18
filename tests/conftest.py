from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest


class Recorder:
    """An httpx.MockTransport that records requests and answers from a handler."""

    def __init__(self, handler: Callable[[httpx.Request], httpx.Response]) -> None:
        self.requests: list[httpx.Request] = []
        self._handler = handler

    def __call__(self, request: httpx.Request) -> httpx.Response:
        request.read()
        self.requests.append(request)
        return self._handler(request)

    def sync_client(self) -> httpx.Client:
        return httpx.Client(transport=httpx.MockTransport(self))

    def async_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(self))

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]


def json_response(status: int, body: Any, headers: dict[str, str] | None = None) -> httpx.Response:
    return httpx.Response(
        status,
        content=json.dumps(body).encode(),
        headers={"content-type": "application/json", **(headers or {})},
    )


@pytest.fixture
def recorder_factory() -> Callable[[Callable[[httpx.Request], httpx.Response]], Recorder]:
    return Recorder


@pytest.fixture(autouse=True)
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Retry sleeps are recorded instead of slept (sync and async clients)."""
    from onlyfans_sdk import _runtime

    recorded: list[float] = []

    def fake_sleep(self: Any, seconds: float) -> None:
        recorded.append(seconds)

    async def fake_async_sleep(self: Any, seconds: float) -> None:
        recorded.append(seconds)

    monkeypatch.setattr(_runtime.SyncAPIClient, "_sleep", fake_sleep)
    monkeypatch.setattr(_runtime.AsyncAPIClient, "_sleep", fake_async_sleep)
    return recorded
