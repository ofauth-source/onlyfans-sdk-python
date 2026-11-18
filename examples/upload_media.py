"""
Upload a file and send it in a message.

    OFAUTH_ACCESS_TOKEN=... OFAUTH_LINKED_ACCOUNT_ID=... python upload_media.py photo.jpg 12345
"""

from __future__ import annotations

import sys
from pathlib import Path

from _env import API_URL, access_token, require

from onlyfans_sdk import OFAuthClient


def main(path: str, user_id: str) -> None:
    with OFAuthClient(
        access_token=access_token(), linked_account_id=require("OFAUTH_LINKED_ACCOUNT_ID"), base_url=API_URL
    ) as client:
        # Content type is guessed from the file name; the MD5 etag finds media already in the vault.
        result = client.upload_media(path, filename=Path(path).name, on_progress=lambda done, total: print(f"{done}/{total} bytes"))
        print(result.status, result.media_item)

        client.access.chats.messages.send(
            user_id=user_id,
            body={"text": "New photo", "mediaItems": [result.media_item], "price": 0},
        )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: python upload_media.py <file> <user_id>")
    main(sys.argv[1], sys.argv[2])
