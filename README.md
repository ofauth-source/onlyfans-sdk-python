# OFAuth Python SDK

Install `onlyfans-sdk` for Python 3.10 or later. The package provides synchronous and asynchronous resource clients, typed models, pagination, errors, uploads, webhook verification, and server Realtime over Server-Sent Events.

```python
from onlyfans_sdk import OFAuthClient, OFAuthLink

client = OFAuthClient(access_token=lambda _force_refresh=False: current_access_token(), linked_account_id=selected_account_id)
profile = client.access.profile.get()

link = OFAuthLink(client_id, client_secret=client_secret, redirect_uri=redirect_uri)
pending = link.create_authorization_url(['profile:read'])
# Save pending under your trusted user and session before redirecting to pending.url.
callback = link.parse_callback(callback_url, expected_state=pending.state)
tokens = link.exchange_code(callback.code, code_verifier=pending.code_verifier)
renewed = link.refresh(tokens['refresh_token'])
link.revoke(tokens['refresh_token'], token_type_hint='refresh_token')
```

`AsyncOFAuthClient` and `AsyncOFAuthLink` expose the corresponding asynchronous interfaces. Resource methods return parsed JSON; `onlyfans_sdk.models` provides generated Pydantic models. Realtime needs no extra dependency: it streams over httpx.

## OAuth contract

Register a confidential backend client and an exact callback URL. Sandbox, Test, and Live use the same authorization code flow with S256 PKCE.

- Browser authorization: `https://link.ofauth.com/v3/authorize`.
- Token exchange and refresh: `POST https://api.ofauth.com/v3/link/token` with a form body.
- Revocation: `POST https://api.ofauth.com/v3/link/revoke` with form `token` and optional `token_type_hint`.
- Metadata: `https://api.ofauth.com/.well-known/oauth-authorization-server/v3/link`.
- Profile: `GET https://api.ofauth.com/v3/link/userinfo` with `identity:read`.

Code exchange always returns a refresh token. Access tokens are opaque Bearer secrets with a 900-second lifetime. Use the returned `expires_in`. Refresh echoes the same client-bound refresh token and extends its 90-day inactivity window. Independent processes can refresh concurrently and retry after a lost response.

The helper uses `client_secret_basic` by default and also supports `client_secret_post`. Each request uses one method. Keep client secrets and refresh tokens on your backend and send them only to OAuth endpoints.

Bind fresh state and the PKCE verifier to the initiating application user and session. Persist pending state in your application, expire it, and consume it once after validating the session. Callback helpers validate the expected state and issuer and reject duplicate parameters. A lost initial code response requires a new authorization attempt.

Your auth framework owns token persistence and renewal. Supply its current access token or token getter to the resource client. The SDK does not provide a second credential manager or database schema. Without a framework, store the standard token response in your database and call the small OAuth helper near expiry. Condition writes on a registration revision so an in-flight refresh cannot overwrite a replacement or recreate a deleted registration. Refresh concurrency does not require a distributed lock.

Discover accounts through `GET /v3/linked-accounts`, then select one explicitly. Token responses do not contain account lists. Client construction sends no requests. An account ID selects a resource; it does not grant authority.

Refresh-token revocation ends that credential and its access tokens. Access-token revocation ends only that bearer. `DELETE /v3/authorization` disconnects the entire authorization. Provider reconnect repairs one selected provider session through `POST /v3/linked-accounts/{id}/reconnect`; it does not renew OAuth or replay writes.

Resource errors distinguish invalid bearer, insufficient permission, account selection, provider reconnect, quota, and transient failure. Follow the error's recovery action. Authenticated requests reject redirects. When injecting a custom transport, preserve this redirect policy; in C#, configure `HttpClientHandler.AllowAutoRedirect = false`.

Developer calls use the application's Developer entitlement. Owners grant account access and do not need an Operator subscription. Operator uses its holder's allowance and cannot access Realtime or Vault+.

See [the public documentation](https://docs.ofauth.com) for consent, grants, guest connection, account linking, and release availability. This branch is coordinated with [OAuth foundation #1274](https://github.com/seb-lewis/ofauth-mono/issues/1274) and requires the matching issuer release.

## Client usage

```python
from onlyfans_sdk import OFAuthClient

with OFAuthClient(access_token=tokens, linked_account_id="conn_123") as client:
    profile = client.access.profile.get()
    page = client.access.chats.list(limit=10)
    client.access.chats.messages.send(user_id="12345", body={"text": "Hi!"})
    stats = client.vault_plus.get_stats()
```

- Namespaces: `client.access.*` (Access API), `client.vault_plus.*` (Vault+), `client.linked_accounts.*`.
  Names follow the canonical SDK names in snake_case: `access.chats.messages.send`,
  `access.posts.bookmarks.list_by_type`, `access.analytics.posts.get`, ...
- Arguments are keyword-only and snake_case (`user_id`, `start_date`, ...); `None` query values are omitted.
- Request bodies are dicts or Pydantic models from `onlyfans_sdk.models` (dumped with
  `model_dump(by_alias=True, exclude_none=True)`).
- **Return values are parsed JSON** (`dict` / `list`, or `None` for empty responses). Each docstring
  names the matching Pydantic model, e.g. `models.V3AccessChatsGetResponse`; validate explicitly if you
  want model objects: `models.V3AccessChatsGetResponse.model_validate(page)`. `onlyfans_sdk.models` is
  imported lazily (it is large).
- `access_token` may be a string, a callable `(force_refresh: bool) -> str`, or a provider with
  `get_access_token(force_refresh=False)`. With a callable or provider, a request
  rejected with `401 invalid_token` is retried once with `force_refresh=True`.
- Options: `base_url` (default `https://api.ofauth.com`; staging `https://api.staging.ofauth.com`; Realtime
  always uses `/v3/realtime/events` on this origin), `headers` (case-insensitive;
  `authorization` is rejected: the SDK sends the bearer token), `timeout`, `max_retries`, `max_retry_delay`, `on_request`, `on_response`,
  `debug`, `http_client` (your own `httpx.Client`, which you close).
- `client.with_options(...)` returns a copy with some options changed (e.g. `max_retries=0`, `timeout=5`
  for one call); `with_linked_account(id)` is shorthand for `with_options(linked_account_id=id)`.

### Async

```python
from onlyfans_sdk import AsyncOFAuthClient

async with AsyncOFAuthClient(access_token=tokens, linked_account_id="conn_123") as client:
    profile = await client.access.profile.get()
    async for chat in client.access.chats.iterate(max_items=50):
        print(chat["user"]["id"])
```
## Linked accounts

Access (`/v3/access/*`) and Vault+ (`/v3/vault-plus/*`) operations act on one linked account, sent as
`x-linked-account-id`. Set a default on the client, override per call, or bind another client:

```python
client.access.profile.get(linked_account_id="conn_456")    # one call
other = client.with_linked_account("conn_456")             # shares the HTTP client
for account in client.linked_accounts.iterate():           # accounts of this authorization
    print(account["id"], account["status"])
```

An Access or Vault+ call without any linked account raises `OFAuthError` before sending a request.
`client.linked_accounts.*` operations never send the header.
## Pagination

Cursor-paginated operations have an iterator next to them: `list` -> `iterate`, `list_x` ->
`iterate_x`. Iterators fetch pages as needed and accept `max_items`:

```python
for post in client.access.posts.iterate(limit=20, max_items=100):
    ...
page = client.access.posts.list(limit=20)                   # manual
next_page = client.access.posts.list(limit=20, cursor=page["page"]["nextCursor"])
```

Iteration stops when `hasMore` is false, the next cursor is empty, or a page is empty.
## Errors and recovery actions

Error responses raise `OFAuthAPIError`:

| Attribute | Meaning |
| --- | --- |
| `status` | HTTP status |
| `code` | stable error code (`error` in the body), e.g. `linked_account_reconnect_required` |
| `recovery_action` | what to do next (`recovery.action`), e.g. `reconnect_linked_account` |
| `request_id` | from the body or `x-request-id`; quote it in support requests |
| `retry_after` | seconds from `Retry-After` |
| `operation`, `required_scope` | canonical name of the failed call and the scope it needs |
| `attempts` | how many times the request was sent |
| `issues` | `list[ValidationIssue]` (`code`, `path`, `message`) for validation errors, else `None` |
| `error_type` | raw `type` of handler errors, e.g. `RESOURCE_NOT_FOUND`, else `None` |
| `body`, `headers`, `message` | raw details |

Error bodies come in three documented shapes, all normalized onto `code`:

- `RuntimeError` (`{"error", "recovery", "requestId"}`): `code` is `error`, `recovery_action` is `recovery.action`.
- `RequestValidationError` (a query, path, or body parameter failed validation): `code` is `invalid_request`,
  `recovery_action` is `check_request`, `issues` lists each failure, and `message` reads like
  `limit: Number must be less than or equal to 100`.
- `AccessHandlerError` (`{"error": "<message>", "type": "RESOURCE_NOT_FOUND"}`, from some Access handlers such as
  uploads): `code` is the lower-cased `type` (`resource_not_found`), `error_type` keeps the raw class, `message` is
  the `error` text, and `recovery_action` is `None` (the helpers fall back to the status).

Helpers (also on every `OFAuthError`, False when they do not apply):

| Property | True when |
| --- | --- |
| `is_retryable` | action `retry` / `retry_after_reset`, or status 429/502/503/504 |
| `needs_token_refresh` | action `obtain_external_oauth_token` |
| `needs_reauthorization` | action `restart_authorization`, `request_additional_consent`, `grant_linked_account`; OAuth `invalid_grant`; `OFAuthNoTokensError` |
| `needs_reconnect` | action `reconnect_linked_account` |
| `is_integration_problem` | action `complete_integration_approval`, `update_developer_plan`, `contact_integration_owner`, `enable_vault_plus` |

`RecoveryAction` / `RECOVERY_ACTIONS` list the known actions; `recovery_action` stays a plain string,
so actions added later still come through.

Branch on the recovery action, not on the status alone:

```python
from onlyfans_sdk import OFAuthAPIError

try:
    client.access.chats.list()
except OFAuthAPIError as error:
    if error.needs_reconnect:
        ask_user_to_reconnect()
    elif error.needs_reauthorization:
        restart_authorization()
    elif error.is_retryable:
        schedule_retry(error.retry_after)
    else:
        log.error("OFAuth %s (%s) request %s", error.code, error.recovery_action, error.request_id)
```

All SDK errors derive from `OFAuthError`.
## Hooks and debug logging

```python
client = OFAuthClient(
    access_token=tokens,
    on_request=lambda info: ...,    # RequestInfo: method, url, headers (credentials redacted), attempt, operation
    on_response=lambda info: ...,   # ResponseInfo: method, url, status, request_id, duration_ms, attempt, operation
    debug=True,                     # or a callable(line), or set OFAUTH_DEBUG=1
)
# [ofauth] GET /v3/access/profile -> 503 (87ms, req_abc)
# [ofauth] retrying GET /v3/access/profile in 0.42s (attempt 2 of 3): 503 transient_provider_failure
# [ofauth] GET /v3/access/profile -> 200 (123ms, req_def)
```

Hooks run once per attempt; on the async client they may be coroutines. Exceptions raised by hooks or the
logger are ignored. `debug=True` writes to stderr. Tokens, secrets, and bodies are never logged.

Hooks never see credentials, so they are safe to log. Header names are lowercase, and `authorization`,
`cookie`, `x-api-key`, `cf-access-client-secret`, and any header whose name contains `token`, `secret`, or
`password` read `[REDACTED]`. `url` has the values of credential-like query parameters (`X-Amz-Signature` and
other `X-Amz-*`, `token`, `sig`, `key`, ...) replaced by `REDACTED`; the request itself is sent unchanged.

Realtime stream requests go through the same hooks and logger (`client.realtime()` passes them on, or
`client.realtime(on_request=..., on_response=..., debug=...)` overrides them; None / False turns one off):
`on_request` gets method `GET`, the sanitized stream URL, redacted headers, and the attempt (1, then 2, 3, ...
until a stream opens); `on_response` gets status 200 when the stream opens or the HTTP status of a refusal,
with `request_id` from `x-realtime-session-id` / `x-request-id`. A network failure before any HTTP response
only logs. Debug line: `[ofauth] SSE /v3/realtime/events -> 200 (85ms, rts_abc)`.
## Webhooks

Deliveries follow [Standard Webhooks](https://www.standardwebhooks.com) (`webhook-id`,
`webhook-timestamp`, `webhook-signature`; `svix-*` headers are accepted too). Always verify the raw body.

```python
from onlyfans_sdk import WebhookRouter, verify_webhook

event = verify_webhook(raw_body, headers, "whsec_...")      # dict; raises WebhookVerificationError

router = WebhookRouter("whsec_...")

@router.on("authorization.revoked")
def revoked(event):
    delete_tokens(event["authorizationId"])

@router.on_default
def other(event): ...

# Flask
@app.post("/webhooks/ofauth")
def webhook():
    status, body = router.handle_http(request.get_data(), request.headers)
    return body, status

# FastAPI (handlers may be async)
@app.post("/webhooks/ofauth")
async def webhook(request: Request):
    status, body = await router.handle_http_async(await request.body(), request.headers)
    return JSONResponse(body, status_code=status)
```

`WebhookVerificationError.code` is one of `MISSING_HEADERS`, `INVALID_TIMESTAMP`,
`TIMESTAMP_OUT_OF_TOLERANCE` (default tolerance 300 s), `NO_VALID_SIGNATURES`, `SIGNATURE_MISMATCH`,
`INVALID_JSON`. Every event has `eventId, type, schemaVersion, order, occurredAt, environment,
integrationId, externalOauthClientId, authorizationId, linkedAccountId, test, data`. Deduplicate on
`eventId` and apply events per `linkedAccountId` in `order`.

Event types: lifecycle `authorization.granted|updated|revoked`,
`linked_account.expired|reconnected|disconnected`, and 11 `realtime.*` types (see
`onlyfans_sdk.events`). For typed events, `parse_webhook_event(event)` returns the Pydantic envelope
(e.g. `models.LifecycleAuthorizationRevokedEnvelope`), and `WebhookRouter(secret, typed=True)` passes
those to handlers.

### Testing webhook handlers

`onlyfans_sdk.testing` signs payloads like OFAuth does and builds valid events for all 17 types from the
examples in the OpenAPI spec:

```python
from onlyfans_sdk.testing import create_test_event, deliver_webhook, sign_webhook

event = create_test_event("authorization.revoked", {"authorizationId": "authz_1"})  # deep-merged, fresh eventId
router.handle(*sign_webhook(event, SECRET))         # (body, headers): verified and dispatched
deliver_webhook(router, event)                      # the same in one call (deliver_webhook_async for async)
body, headers = sign_webhook(event, SECRET, id="msg_1", timestamp=1700000000)
```

`generate_webhook_secret()` makes a random `whsec_` secret. See `examples/test_webhook_handlers.py`.
## Realtime

Realtime events for one linked account over Server-Sent Events (asyncio, on httpx; no extra dependency).
Lifecycle events are webhook-only.

```python
realtime = client.realtime()                 # the only way to get a RealtimeConnection

@realtime.on("realtime.chat_message.received")
async def on_message(event):                 # a RealtimeEvent dict
    print(event["data"], event["receivedAt"])

realtime.on_resync(refetch_everything)       # events were missed: refetch state through the REST API
realtime.on_close(lambda info: print(info.reason, info.status, info.will_reconnect, info.retry_in))
await realtime.connect()                     # a failed first connect raises OFAuthAPIError (401, 409, 503, ...)
await realtime.wait_closed()
```

`client.realtime()` streams `GET /v3/realtime/events?linkedAccountId=...` with the client's token and extra
`headers`. Options: `linked_account_id`, `last_event_id` (resume after an event you stored before a restart;
`realtime.last_event_id` is the current one), `reconnect` (default True), `max_reconnect_delay` (seconds,
default 30), `heartbeat_timeout` (seconds, default 45; 0 disables it), `http_client` (an `httpx.AsyncClient`;
`AsyncOFAuthClient` streams with its own, `OFAuthClient` opens one per connection), and the hooks above.
Listeners (`on(type)`, `on_event`, `on_resync`, `on_open`, `on_close`, `on_error`) may be sync or async, and
work as decorators.

- Reconnects back off exponentially from the stream's `retry:` time (3 s), with jitter, capped at
  `max_reconnect_delay`, never sooner than `Retry-After`, and resume with `Last-Event-ID`. Repeated `eventId`s
  are dropped (delivery is at least once).
- The server sends a heartbeat every 15 s; after `heartbeat_timeout` without any bytes the stream reconnects.
- `RealtimeCloseInfo.reason` (a `RealtimeCloseReason`) is one of:
  - `reauth` (`closed` with `reauth`, or 401): the SDK gets a new token (`force_refresh=True`) and retries
    once, then stops. A string token cannot be refreshed, so a 401 stops at once.
  - `replaced` (`closed` with `replaced`, or 409): a newer stream took the slot (up to 10 per account). Stops.
  - `unavailable` (`closed` with `unavailable`, 503, 429): backs off and resumes.
  - `dropped` (the stream ended without `closed`, or a network error) and `heartbeat_timeout`: resumes.
  - `rejected` (400, 403, 404, 406, or a response that is not an event stream): stops.
  - `client_closed`: you called `close()`.

  `status` has the HTTP status of a refusal and `retry_in` the delay (seconds) before the next attempt.
- `connect()` while connected does nothing. The first `connect()` raises instead of retrying in the
  background (except for the one token refresh).

For a browser, mint a stream URL on your server and send only the URL to the page, which opens it with
`EventSource` (or the TypeScript SDK's `connectRealtimeStream`):

```python
stream = client.realtime.create_stream_url()  # POST /v3/realtime; await it on AsyncOFAuthClient
stream.url, stream.expires_at                  # a 10-minute stream credential, not the access token
```

`client.realtime()` always streams from `/v3/realtime/events` on the client's `base_url` origin with the
client's token. Realtime is served on the same origin as every other API route, so there is no realtime URL
option and a staging client never sends its token to production Realtime. A `base_url` that is not http(s)
raises `OFAuthError`. `RealtimeConnection` cannot be created on its own (its constructor raises
`TypeError`); the class stays public for type annotations.
## Uploads

```python
result = client.upload_media("photo.jpg", filename="photo.jpg", on_progress=lambda done, total: ...)
client.access.chats.messages.send(user_id="12345", body={"text": "New", "mediaItems": [result.media_item]})
```

`upload_media` accepts bytes, a path, or a binary file object; `content_type` is guessed from the file
name when omitted. It starts the upload with the file's MD5 as `etag`, returns
`status="already_exists"` with `media_id` when the file is already in the vault, otherwise PUTs every
part and finalizes (`status="uploaded"`, `upload_id`). Pass `vault_upload={"userId": ..., "listId": ...}`
to also save to the vault; `result.vault_media_ids` then lists the numeric vault media ids it created
(e.g. to hide them later with `client.access.vault.media.hide`).

`result.media` (already_exists) is a `models.MediaAsset` and `result.finalize` (uploaded) a
`models.V3AccessUploadsFinalizePostResponse` (the variant is `result.finalize.root`: `uploadIds`, or
`uploads[{uploadId, mediaId, media}]` with `vault_upload`). A response that doesn't match the spec is
still returned, built without validation, since the upload has already succeeded.
## API reference

Every operation's docstring has its scope and a one-line usage example. Build the HTML reference
(pdoc, output in `docs/`, gitignored):

```bash
cd packages/python
make docs        # uv run --no-project --with-editable . --with pdoc pdoc --docformat google -o docs onlyfans_sdk ...
```

`pip install "onlyfans-sdk[docs]"` installs pdoc if you prefer running it yourself.
## Development

The SDK is generated: `node scripts/generate-types.mjs` (normalized spec + `models.py`), then
`node scripts/generate-python.mjs`. Hand-written runtime code lives in `scripts/templates/python/`.

```bash
cd packages/python
make test        # uv run --no-project --with pytest --with pytest-asyncio --with fastapi --with httpx --with flask --with-editable . pytest -q
make lint        # ruff + mypy
```

Contract tests against a real authorization: see `contract/README.md`.
## License

Apache-2.0
