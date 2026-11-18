"""
Webhooks with Flask: verify Standard Webhooks signatures and route by event type.

    OFAUTH_WEBHOOK_SECRET=whsec_... python webhook_server.py

FastAPI:

    @app.post("/webhooks/ofauth")
    async def webhook(request: Request):
        status, body = await router.handle_http_async(await request.body(), request.headers)
        return JSONResponse(body, status_code=status)
"""

from __future__ import annotations

from _env import require
from flask import Flask, request

from onlyfans_sdk import WebhookRouter

app = Flask(__name__)
router = WebhookRouter(require("OFAUTH_WEBHOOK_SECRET"))
seen_event_ids: set[str] = set()  # use your database in production


@router.on("authorization.revoked")
def on_revoked(event: dict) -> None:
    print("authorization revoked:", event["authorizationId"], "-> delete stored tokens")


@router.on("linked_account.expired")
def on_expired(event: dict) -> None:
    print("linked account needs reconnecting:", event["data"])


@router.on("realtime.chat_message.received")
def on_message(event: dict) -> None:
    print("new message in", event["linkedAccountId"], event["data"])


@router.on_default
def on_other(event: dict) -> None:
    print("unhandled", event["type"])


@app.post("/webhooks/ofauth")
def webhook():
    # Pass the raw body: re-serialized JSON will not match the signature.
    event_id = request.headers.get("webhook-id")
    if event_id in seen_event_ids:
        return {"ok": True}, 200
    status, body = router.handle_http(request.get_data(), request.headers)
    if status == 200 and event_id:
        seen_event_ids.add(event_id)
    return body, status


if __name__ == "__main__":
    app.run(port=5001)
