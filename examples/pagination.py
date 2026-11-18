"""
Pagination: manual cursors, iterators, and the async client.

    OFAUTH_ACCESS_TOKEN=... OFAUTH_LINKED_ACCOUNT_ID=... python pagination.py
"""

from __future__ import annotations

import asyncio

from _env import API_URL, access_token, require

from onlyfans_sdk import AsyncOFAuthClient, OFAuthClient


def sync_example() -> None:
    with OFAuthClient(
        access_token=access_token(), linked_account_id=require("OFAUTH_LINKED_ACCOUNT_ID"), base_url=API_URL
    ) as client:
        # Manual: pass page.nextCursor back as cursor.
        page = client.access.posts.list(limit=10)
        print("first page:", len(page["items"]), "posts; more:", page["page"]["hasMore"])
        if page["page"]["hasMore"]:
            second = client.access.posts.list(limit=10, cursor=page["page"]["nextCursor"])
            print("second page:", len(second["items"]), "posts")

        # Iterator: fetches pages as needed, stops after max_items.
        for subscriber in client.access.subscribers.iterate(limit=50, max_items=200):
            print("subscriber", subscriber["id"])


async def async_example() -> None:
    async with AsyncOFAuthClient(
        access_token=require("OFAUTH_ACCESS_TOKEN"),
        linked_account_id=require("OFAUTH_LINKED_ACCOUNT_ID"),
        base_url=API_URL,
    ) as client:
        count = 0
        async for _chat in client.access.chats.iterate(max_items=100):
            count += 1
        print("chats:", count)


if __name__ == "__main__":
    sync_example()
    asyncio.run(async_example())
