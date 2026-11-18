"""
Realtime over Server-Sent Events (no extra dependency).

    OFAUTH_ACCESS_TOKEN=... OFAUTH_LINKED_ACCOUNT_ID=... python realtime_events.py
"""

from __future__ import annotations

import asyncio

from _env import API_URL, access_token, require

from onlyfans_sdk import AsyncOFAuthClient, RealtimeCloseInfo, RealtimeEvent


async def main() -> None:
    async with AsyncOFAuthClient(
        access_token=access_token(),
        linked_account_id=require("OFAUTH_LINKED_ACCOUNT_ID"),
        base_url=API_URL,
    ) as client:
        realtime = client.realtime()

        @realtime.on("realtime.chat_message.received")
        async def on_message(event: RealtimeEvent) -> None:
            print("message", event["data"]["id"], "received at", event["receivedAt"])

        @realtime.on_event
        def on_any(event: RealtimeEvent) -> None:
            print("event", event["type"], "order", event["order"])

        @realtime.on_resync
        def on_resync() -> None:
            print("events were missed: refetch chats and counts through the REST API")

        @realtime.on_close
        def on_close(info: RealtimeCloseInfo) -> None:
            # reauth (after one token refresh), replaced, and rejected do not reconnect.
            print("closed", info.reason, info.status, f"retrying in {info.retry_in}s" if info.will_reconnect else "stopped")

        await realtime.connect()  # raises OFAuthAPIError if the first attempt is refused (e.g. 409, 503)
        try:
            await realtime.wait_closed()
        finally:
            await realtime.close()
            print("resume later from", realtime.last_event_id)


if __name__ == "__main__":
    asyncio.run(main())
