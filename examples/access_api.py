"""
Calling Access: profile, chats, sending a message, and switching linked accounts.

    OFAUTH_ACCESS_TOKEN=... OFAUTH_LINKED_ACCOUNT_ID=... python access_api.py
"""

from __future__ import annotations

import os

from _env import API_URL, access_token, require

from onlyfans_sdk import OFAuthClient


def main() -> None:
    with OFAuthClient(
        access_token=access_token(),
        linked_account_id=require("OFAUTH_LINKED_ACCOUNT_ID"),
        base_url=API_URL,
    ) as client:
        profile = client.access.profile.get()
        print(f"Profile: @{profile.get('username')} ({profile['id']})")

        page = client.access.chats.list(limit=5)
        for chat in page["items"]:
            print("chat with", chat["user"]["id"])

        # Bodies may be dicts or Pydantic models from onlyfans_sdk.models.
        if os.getenv("SEND_TO_USER_ID"):
            sent = client.access.chats.messages.send(
                user_id=os.environ["SEND_TO_USER_ID"],
                body={"text": "Hello from the OFAuth Python SDK"},
            )
            print("sent message", sent.get("id"))

        # Every linked account of the authorization:
        for account in client.linked_accounts.iterate():
            print("linked account", account["id"], account.get("status"))

        # Same authorization, another linked account (shares the HTTP client):
        other_id = os.getenv("OTHER_LINKED_ACCOUNT_ID")
        if other_id:
            other = client.with_linked_account(other_id)
            print("other profile", other.access.profile.get()["id"])


if __name__ == "__main__":
    main()
